from unittest.mock import MagicMock, patch, call

import celery
import celery.canvas
import pytest
from history4feed.app import models
from history4feed.app.models import Feed, FeedType, FullTextState, FulltextJob, Job, Post
from history4feed.h4fscripts import exceptions
from history4feed.h4fscripts.h4f import PostDict
from history4feed.h4fscripts.task_helper import (
    JobCancelled,
    add_post_to_db,
    create_fulltexts_task_chain,
    new_job,
    new_patch_posts_job,
    retrieve_full_text,
    retrieve_posts_from_links,
    retrieve_posts_from_serper,
    retrieve_posts_from_url,
    start_job,
    start_post_job,
)
from rest_framework.exceptions import APIException, Throttled
from datetime import UTC, datetime as dt


@pytest.fixture(autouse=True, scope="module")
def celery_eager():
    from history4feed.h4fscripts.celery import app

    app.conf.task_always_eager = True
    app.conf.broker_url = None
    yield
    app.conf.task_always_eager = False


@pytest.mark.django_db
def test_new_job():
    feed = Feed.objects.create(url="https://example.com/rss.xml", title="Test Feed")

    with (
        patch(
            "history4feed.h4fscripts.task_helper.retrieve_posts_from_links.run"
        ) as mock_retrieve_posts,
        patch("history4feed.h4fscripts.task_helper.start_job.run") as mock_start_job,
        patch(
            "history4feed.h4fscripts.task_helper.collect_and_schedule_removal.run"
        ) as mock_collect_and_schedule_removal,
        patch(
            "history4feed.h4fscripts.task_helper.error_handler.run"
        ) as mock_error_handler,
        patch(
            "history4feed.h4fscripts.task_helper.queue_lock", return_value=True
        ) as mock_queue_lock,
    ):
        new_job(feed, include_remote_blogs=False)
        job: Job = mock_queue_lock.call_args[0][1]
        assert job.feed == feed
        mock_queue_lock.assert_called_once_with(feed, job)
        mock_retrieve_posts.assert_called_once_with(mock_start_job.return_value, job.id)
        mock_start_job.assert_called_once_with(job.id)
        mock_collect_and_schedule_removal.assert_called_once_with(job.id)
        mock_error_handler.assert_not_called(), "should not be called unless there is an error"


@pytest.mark.django_db
def test_job_queue_fail():
    feed = Feed.objects.create(url="https://example.com/rss.xml", title="Test Feed")

    with (
        patch(
            "history4feed.h4fscripts.task_helper.cache.get", return_value={}
        ) as mock_get_cache,
        patch(
            "history4feed.h4fscripts.task_helper.queue_lock", return_value=False
        ) as mock_queue_lock,
        pytest.raises(Throttled),
    ):
        new_job(feed, include_remote_blogs=False)
        job: Job = mock_queue_lock.call_args[0][1]


@pytest.mark.django_db
def test_new_patch_posts_job():
    feed = Feed.objects.create(url="https://example.com/rss.xml", title="Test Feed")
    posts = [
        Post.objects.create(feed=feed, title="First post", pubdate=dt.now()),
        Post.objects.create(
            feed=feed,
            title="Second post",
            pubdate=dt.now(),
            link="https://example.net/post2",
        ),
    ]

    with (
        patch(
            "history4feed.h4fscripts.task_helper.retrieve_full_text.run"
        ) as mock_retrieve_full_text,
        # patch("history4feed.h4fscripts.task_helper.start_post_job.run") as mock_start_post_job,
        patch(
            "history4feed.h4fscripts.task_helper.collect_and_schedule_removal.run"
        ) as mock_collect_and_schedule_removal,
        patch(
            "history4feed.h4fscripts.task_helper.error_handler.run"
        ) as mock_error_handler,
        patch(
            "history4feed.h4fscripts.task_helper.queue_lock", return_value=True
        ) as mock_queue_lock,
    ):
        job = new_patch_posts_job(feed, posts, include_remote_blogs=False)
        assert job.feed == feed
        mock_queue_lock.assert_called_once_with(feed, job)
        # assert job.state == models.JobState.RUNNING

        [
            models.FulltextJob.objects.get(pk=call[0][0]).post.id
            for call in mock_retrieve_full_text.call_args_list
        ] == [post.id for post in posts]

        mock_collect_and_schedule_removal.assert_called_once_with(job.id)
        mock_error_handler.assert_not_called(), "should not be called unless there is an error"


@pytest.mark.django_db
def test_start_post_job_already_cancelled():
    job_obj = models.Job.objects.create(
        feed=Feed.objects.create(url="https://example.com/rss.xml", title="Test Feed"),
        state=models.JobState.PENDING,
    )
    job_obj.update_state(models.JobState.CANCELLED)
    with (
        patch(
            "history4feed.h4fscripts.task_helper.queue_lock", return_value=True
        ) as mock_queue_lock,
    ):
        result = start_post_job.si(job_obj.id).delay()
        assert result.get() == False
        mock_queue_lock.assert_not_called()


@pytest.mark.django_db
def test_start_post_job_retries_until_queue_no_longer_locked():
    job_obj = models.Job.objects.create(
        feed=Feed.objects.create(url="https://example.com/rss.xml", title="Test Feed"),
        state=models.JobState.PENDING,
    )
    with (
        patch(
            "history4feed.h4fscripts.task_helper.queue_lock",
            side_effect=[False, False, True],
        ) as mock_queue_lock,
    ):
        result = start_post_job.si(job_obj.id).delay()
        job_obj.refresh_from_db()
        assert result.get() == True
        assert job_obj.state == models.JobState.RUNNING
        mock_queue_lock.assert_called()
        assert len(mock_queue_lock.call_args_list) == 3


@pytest.mark.django_db
def test_start_job__search_index():
    job_obj = models.Job.objects.create(
        feed=Feed.objects.create(
            url="https://example.com/rss.xml",
            title="Test Feed",
            feed_type=models.FeedType.SEARCH_INDEX,
        ),
        state=models.JobState.PENDING,
    )
    result = start_job(job_obj.id)
    assert result == [job_obj.feed.url]
    job_obj.refresh_from_db()
    assert job_obj.state == models.JobState.RUNNING


@pytest.mark.django_db
def test_start_job__atom_or_rss():
    job_obj = models.Job.objects.create(
        feed=Feed.objects.create(
            url="https://example.com/rss.xml",
            title="Test Feed",
            feed_type=models.FeedType.RSS,
        ),
        state=models.JobState.PENDING,
    )
    with patch(
        "history4feed.h4fscripts.wayback_helpers.get_wayback_urls"
    ) as mock_get_wayback_urls:
        result = start_job(job_obj.id)
        assert result == mock_get_wayback_urls.return_value
        job_obj.refresh_from_db()
        assert job_obj.state == models.JobState.RUNNING


@pytest.mark.django_db
def test_start_job__atom_or_rss__fails():
    job_obj = models.Job.objects.create(
        feed=Feed.objects.create(
            url="https://example.com/rss.xml",
            title="Test Feed",
            feed_type=models.FeedType.RSS,
        ),
        state=models.JobState.PENDING,
    )
    with patch(
        "history4feed.h4fscripts.wayback_helpers.get_wayback_urls",
        side_effect=Exception,
    ) as mock_get_wayback_urls:
        result = start_job(job_obj.id)
        assert result == []
        job_obj.refresh_from_db()
        assert job_obj.state == models.JobState.FAILED


@pytest.mark.parametrize(
    "feed_type",
    [
        models.FeedType.RSS,
        models.FeedType.ATOM,
        models.FeedType.SEARCH_INDEX,
    ],
)
@pytest.mark.django_db
def test_retrieve_posts_from_links(feed_type):
    job_obj = models.Job.objects.create(
        feed=Feed.objects.create(
            url="https://example.com/rss.xml",
            title="Test Feed",
            feed_type=feed_type,
        ),
        state=models.JobState.PENDING,
    )
    chains = [MagicMock(), MagicMock()]
    with (
        patch(
            "history4feed.h4fscripts.task_helper.retrieve_posts_from_serper",
            return_value=MagicMock(),
        ) as mock_retrieve_serp,
        patch(
            "history4feed.h4fscripts.task_helper.retrieve_posts_from_url",
            return_value=[{}, MagicMock(), None],
        ) as mock_retrieve_rss,
        patch(
            "history4feed.h4fscripts.task_helper.create_fulltexts_task_chain",
            side_effect=chains,
        ) as mock_ft_chain,
    ):

        resp = retrieve_posts_from_links(
            ["https://goo.gl", "http://example.com"], job_obj.id
        )
        job_obj.refresh_from_db()
        assert job_obj.feed.freshness == job_obj.run_datetime
        if job_obj.feed.feed_type == models.FeedType.SEARCH_INDEX:
            mock_retrieve_serp.assert_has_calls(
                [
                    call(job_obj.feed, job_obj, "https://goo.gl"),
                    call(job_obj.feed, job_obj, "http://example.com"),
                ]
            )
            mock_ft_chain.call_count == 2
            mock_ft_chain.assert_called_with(
                job_obj.id, mock_retrieve_serp.return_value
            )
        else:
            mock_retrieve_rss.assert_has_calls(
                [
                    call(
                        "https://goo.gl",
                        job_obj.feed,
                        job_obj,
                    ),
                    call("http://example.com", job_obj.feed, job_obj),
                ]
            )
            mock_ft_chain.call_count == 2
            mock_ft_chain.assert_called_with(
                job_obj.id, mock_retrieve_rss.return_value[1]
            )
        assert resp == [chain.apply_async.return_value.id for chain in chains]


@pytest.mark.django_db
def test_create_fulltexts_task_chain():
    job_obj = models.Job.objects.create(
        feed=Feed.objects.create(
            url="https://example.com/rss.xml",
            title="Test Feed",
            feed_type=models.FeedType.RSS,
        ),
        state=models.JobState.PENDING,
    )
    feed = job_obj.feed
    posts = [
        Post.objects.create(feed=feed, title="First post", pubdate=dt.now()),
        Post.objects.create(
            feed=feed,
            title="Second post",
            pubdate=dt.now(),
            link="https://example.net/post2",
        ),
    ]

    with (
        patch(
            "history4feed.h4fscripts.task_helper.retrieve_full_text.run"
        ) as mock_retrieve_ft,
    ):
        chain = create_fulltexts_task_chain(job_obj.id, posts)
        chain.apply_async()
        assert isinstance(chain, (celery.chain, celery.canvas._chain)), type(chain)
        fts = models.FulltextJob.objects.filter(job_id=job_obj.id)
        mock_retrieve_ft.assert_has_calls([call(ft.pk) for ft in fts], any_order=True)


@pytest.mark.django_db
def test_retrieve_posts_from_serper():
    job_obj = models.Job.objects.create(
        feed=Feed.objects.create(
            url="https://example.com/rss.xml",
            title="Test Feed",
            feed_type=models.FeedType.SEARCH_INDEX,
            freshness=dt(2024, 1, 1),
        ),
        state=models.JobState.PENDING,
    )
    with (
        patch(
            "history4feed.h4fscripts.task_helper.fetch_posts_links_with_serper",
            return_value={
                post.link: post
                for post in [
                    PostDict(
                        title="random title",
                        link="https://example.com/post/1",
                        pubdate=dt.now(),
                    ),
                    PostDict(
                        title="random title",
                        link="https://example.com/post/2",
                        pubdate=dt.now()
                    ),
                    PostDict(
                        title="random title",
                        link="https://example.com/post/3",
                        pubdate=dt.now()
                    ),
                    PostDict(
                        title="random title",
                        link="https://example.com/post/4",
                        pubdate=dt.now()
                    ),
                ]
            },
        ) as mock_fetch,
        patch(
            "history4feed.h4fscripts.task_helper.add_post_to_db",
            side_effect=add_post_to_db,
        ) as mock_add_post_to_db,
    ):
        url = "https://example.net"
        results = retrieve_posts_from_serper(job_obj.feed, job_obj, url)
        mock_fetch.assert_called_once_with(
            url, from_time=dt(2024, 1, 1, tzinfo=UTC), to_time=job_obj.run_datetime
        )
        assert len(results) == 4
        mock_add_post_to_db.call_count == 4

def test_retrieve_posts_from_url():
    pass




@pytest.fixture
def dummy_feed():
    return MagicMock(spec=Feed)


@pytest.fixture
def dummy_job():
    job = MagicMock(spec=Job)
    job.is_cancelled.return_value = False
    return job


@patch("history4feed.h4fscripts.task_helper.add_post_to_db")
@patch("history4feed.h4fscripts.task_helper.h4f.parse_posts_from_rss_feed")
@patch("history4feed.h4fscripts.task_helper.h4f.parse_feed_from_content")
@patch("history4feed.h4fscripts.task_helper.h4f.fetch_page_with_retries")
@patch("history4feed.h4fscripts.task_helper.time.sleep")
def test_retrieve_posts_rss_success(mock_sleep, mock_fetch, mock_parse_feed, mock_parse_rss, mock_add_post, dummy_feed, dummy_job):
    url = "https://example.com/rss"

    mock_fetch.return_value = (b"<xml>RSS</xml>", "text/xml", url)
    mock_parse_feed.return_value = {"feed_type": FeedType.RSS}
    mock_parse_rss.return_value = {"1": {"title": "Post 1"}, "2": {"title": "Post 2"}}
    post1 = MagicMock(spec=Post)
    post2 = MagicMock(spec=Post)
    mock_add_post.side_effect = [post1, post2]

    parsed_feed, all_posts, error = retrieve_posts_from_url(url, dummy_feed, dummy_job)

    assert parsed_feed['feed_type'] == FeedType.RSS
    assert all_posts == [post1, post2]
    assert error is None
    mock_fetch.assert_called_once_with(url)
    dummy_feed.save.assert_called_once()


@patch("history4feed.h4fscripts.task_helper.add_post_to_db")
@patch("history4feed.h4fscripts.task_helper.h4f.parse_posts_from_atom_feed")
@patch("history4feed.h4fscripts.task_helper.h4f.parse_feed_from_content")
@patch("history4feed.h4fscripts.task_helper.h4f.fetch_page_with_retries")
@patch("time.sleep")
def test_retrieve_posts_atom_success(mock_sleep, mock_fetch, mock_parse_feed, mock_parse_atom, mock_add_post, dummy_feed, dummy_job):
    url = "https://example.com/atom"
    mock_fetch.return_value = (b"<xml>ATOM</xml>", "text/xml", url)
    mock_parse_feed.return_value = {"feed_type": FeedType.ATOM}
    mock_parse_atom.return_value = {"1": {"title": "A1"}}
    post = MagicMock(spec=Post)
    mock_add_post.return_value = post

    parsed_feed, all_posts, error = retrieve_posts_from_url(url, dummy_feed, dummy_job)

    assert parsed_feed['feed_type'] == FeedType.ATOM
    assert all_posts == [post]
    assert error is None


@patch("history4feed.h4fscripts.task_helper.h4f.fetch_page_with_retries")
@patch("history4feed.h4fscripts.task_helper.h4f.parse_feed_from_content")
@patch("time.sleep")
def test_retrieve_posts_unknown_feedtype(mock_sleep, mock_parse_feed, mock_fetch, dummy_feed, dummy_job):
    url = "https://unknown.feed"
    mock_fetch.return_value = (b"<xml>???</xml>", "text/xml", url)
    mock_parse_feed.return_value = {"feed_type": "UNKNOWN"}

    _, _, err = retrieve_posts_from_url(url, dummy_feed, dummy_job)
    assert isinstance(err,  exceptions.UnknownFeedtypeException)


@patch("history4feed.h4fscripts.task_helper.h4f.fetch_page_with_retries")
def test_retrieve_posts_job_cancelled(mock_fetch, dummy_feed, dummy_job):
    dummy_job.is_cancelled.return_value = True
    url = "https://cancel.test"

    _, _, err =retrieve_posts_from_url(url, dummy_feed, dummy_job)
    assert isinstance(err,  JobCancelled)


@patch("history4feed.h4fscripts.task_helper.h4f.fetch_page_with_retries", side_effect=ConnectionError("Timeout"))
@patch("time.sleep")
def test_retrieve_posts_connection_error_retries(mock_sleep, mock_fetch, dummy_feed, dummy_job, settings):
    settings.REQUEST_RETRY_COUNT = 3
    settings.WAYBACK_SLEEP_SECONDS = 1

    url = "https://retry.fail"

    parsed_feed, all_posts, error = retrieve_posts_from_url(url, dummy_feed, dummy_job)

    assert parsed_feed == {}
    assert all_posts == []
    assert isinstance(error, ConnectionError)
    assert mock_fetch.call_count == 3
    assert mock_sleep.call_count == 2  # called only after the first attempt fails


@patch("history4feed.h4fscripts.task_helper.h4f.fetch_page_with_retries", side_effect=ValueError("boom"))
@patch("time.sleep")
def test_retrieve_posts_general_exception(mock_sleep, mock_fetch, dummy_feed, dummy_job):
    url = "https://explode.me"
    parsed_feed, all_posts, error = retrieve_posts_from_url(url, dummy_feed, dummy_job)

    assert parsed_feed == {}
    assert all_posts == []
    assert isinstance(error, ValueError)
    assert mock_fetch.call_count == 1


@pytest.fixture
def dummy_ftjob(dummy_post):
    ftjob = MagicMock(spec=FulltextJob)
    ftjob.post = dummy_post
    ftjob.pk = 1
    ftjob.status = None
    ftjob.error_str = ""
    return ftjob
@pytest.fixture
def dummy_post():
    post = MagicMock(spec=Post)
    post.link = "https://example.com/article"
    return post

@patch("history4feed.h4fscripts.task_helper.logger")
@patch("history4feed.h4fscripts.task_helper.h4f.get_full_text")
@patch("history4feed.h4fscripts.task_helper.models.FulltextJob.objects.get")
def test_retrieve_full_text_success(mock_get_job, mock_get_full_text, mock_logger, dummy_ftjob):
    mock_get_job.return_value = dummy_ftjob
    dummy_ftjob.is_cancelled.return_value = False
    mock_get_full_text.return_value = ("<p>Content</p>", "text/html")

    retrieve_full_text(dummy_ftjob.pk)

    mock_get_full_text.assert_called_once_with(dummy_ftjob.post.link)
    assert dummy_ftjob.status == FullTextState.RETRIEVED
    assert dummy_ftjob.error_str == ""
    assert dummy_ftjob.post.description == "<p>Content</p>"
    assert dummy_ftjob.post.content_type == "text/html"
    assert dummy_ftjob.post.is_full_text is True
    dummy_ftjob.save.assert_called_once()
    dummy_ftjob.post.save.assert_called_once()


@patch("history4feed.h4fscripts.task_helper.models.FulltextJob.objects.get")
def test_retrieve_full_text_cancelled(mock_get_job, dummy_ftjob):
    mock_get_job.return_value = dummy_ftjob
    dummy_ftjob.is_cancelled.return_value = True

    retrieve_full_text(dummy_ftjob.pk)

    assert dummy_ftjob.status == FullTextState.CANCELLED
    assert "cancelled" in dummy_ftjob.error_str.lower()
    dummy_ftjob.save.assert_called_once()
    dummy_ftjob.post.save.assert_called_once()


@patch("history4feed.h4fscripts.task_helper.h4f.get_full_text", side_effect=Exception("boom"))
@patch("history4feed.h4fscripts.task_helper.models.FulltextJob.objects.get")
def test_retrieve_full_text_exception(mock_get_job, mock_get_text, dummy_ftjob):
    mock_get_job.return_value = dummy_ftjob
    dummy_ftjob.is_cancelled.return_value = False

    retrieve_full_text(dummy_ftjob.pk)

    assert dummy_ftjob.status == FullTextState.FAILED
    assert dummy_ftjob.error_str == "boom"
    dummy_ftjob.save.assert_called_once()
    dummy_ftjob.post.save.assert_called_once()