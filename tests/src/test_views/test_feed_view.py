from unittest.mock import MagicMock, patch
import uuid

import pytest
from history4feed.app.models import Feed, FeedType, Job
from history4feed.app.views import FeedView
import pytest
from rest_framework import status
from django.http import HttpRequest
from rest_framework.request import Request
from history4feed.app.models import Post, Feed, Job
from datetime import datetime as dt
from unittest.mock import patch
from history4feed.app.serializers import (
    FeedFetchSerializer,
    FeedPatchSerializer,
    FeedSerializer,
    PostWithFeedIDSerializer,
    SearchIndexFeedSerializer,
)
from history4feed.app.views import PostOnlyView
from dateutil.parser import parse as parse_date


from history4feed.app.utils import (
    DatetimeFieldUTC,
    Ordering,
    Pagination,
    MinMaxDateFilter,
)

# from .openapi_params import FEED_PARAMS, POST_PARAMS

from history4feed.app.serializers import PostWithFeedIDSerializer
from history4feed.app.models import Post, Feed, Job
from rest_framework import (
    status,
)
from django_filters.rest_framework import (
    DjangoFilterBackend,
)


def test_class_variables():
    assert FeedView.ordering_fields == [
        "datetime_added",
        "title",
        "url",
        "count_of_posts",
        "earliest_item_pubdate",
        "latest_item_pubdate",
    ]
    assert FeedView.ordering == "datetime_added_descending", "default ordering"
    assert FeedView.filter_backends == [
        DjangoFilterBackend,
        Ordering,
        MinMaxDateFilter,
    ]
    assert type(FeedView.pagination_class) == Pagination
    assert FeedView.pagination_class.results_key == "feeds"
    assert FeedView.serializer_class == FeedSerializer


@pytest.mark.django_db
def test_create_feed(client):

    feed = Feed.objects.create(url="https://example.com/rss.xml", title="Test Feed")
    job = Job.objects.create(feed=feed)
    payload = dict(data="some data")
    with patch.object(FeedView, "new_create_job") as mock_create_job:
        mock_create_job.return_value = job
        resp = client.post(
            "/api/v1/feeds/", data=payload, content_type="application/json"
        )
        assert resp.status_code == 201
        assert str(resp.data["job_id"]) == str(job.id)


@pytest.mark.parametrize("include_remote_blogs", [True, False])
@pytest.mark.parametrize("use_search_index", [True, False])
@pytest.mark.django_db
def test_new_create_job(use_search_index, include_remote_blogs):
    request = MagicMock()
    request.data = dict(
        title="some title",
        description="some description",
        url="https://example.net/",
        use_search_index=use_search_index,
        include_remote_blogs=include_remote_blogs,
    )
    with (
        patch(
            "history4feed.app.views.task_helper.new_job",
            side_effect=lambda *args: Job.objects.create(feed=args[0]),
        ) as mock_new_job,
        patch(
            "history4feed.app.views.SearchIndexFeedSerializer",
            side_effect=SearchIndexFeedSerializer,
        ) as mock_search_index_serializer,
        patch(
            "history4feed.app.views.h4f.parse_feed_from_url"
        ) as mock_parse_feed_from_url,
    ):
        mock_parse_feed_from_url.return_value = {**request.data, "feed_type": "atom"}
        result = FeedView().new_create_job(request)
        assert result.feed.title == request.data["title"]
        assert result.feed.description == request.data["description"]
        mock_new_job.assert_called_once_with(result.feed, include_remote_blogs)
        if use_search_index:
            mock_search_index_serializer.assert_called_once_with(data=request.data)
            assert result.feed.feed_type == FeedType.SEARCH_INDEX
            mock_parse_feed_from_url.assert_not_called()
        else:
            mock_parse_feed_from_url.assert_called_once_with(request.data["url"])
            assert result.feed.feed_type == FeedType.ATOM
            mock_search_index_serializer.assert_not_called()


@pytest.mark.django_db
def test_create_skeleton(client):
    payload = dict(
        title="some title", description="some description", url="https://example.net/"
    )
    resp = client.post(
        "/api/v1/feeds/skeleton/", data=payload, content_type="application/json"
    )
    assert resp.status_code == 201, resp.content
    assert resp.data["title"] == "some title"
    assert resp.data["description"] == "some description"
    assert resp.data["feed_type"] == "skeleton"


@pytest.mark.django_db
def test_create_skeleton_400(client):
    payload = dict(title="some title", description="some description")
    resp = client.post(
        "/api/v1/feeds/skeleton/", data=payload, content_type="application/json"
    )
    assert resp.status_code == 400, resp.content


@pytest.mark.parametrize(
    "payload",
    [
        dict(title="my new title"),
        dict(description="my new descr"),
        dict(description="my new descr", title="new title 2"),
        dict(pretty_url="https://aa.net/3", title="new title 2"),
        dict(pretty_url="https://example.com/4", description="new descr 2"),
    ],
)
@pytest.mark.django_db
def test_feed_metadata_update(client, payload):
    feed = Feed.objects.create(url="https://example.com/rss.xml", title="Test Feed")
    with patch(
        "history4feed.app.views.FeedPatchSerializer",
        side_effect=FeedPatchSerializer,
    ) as mock_patch_feed_serializer:
        resp = client.patch(
            f"/api/v1/feeds/{feed.id}/", data=payload, content_type="application/json"
        )
        assert resp.status_code == 201, resp.content
        mock_patch_feed_serializer.assert_called_once_with(
            feed, data=payload, partial=True
        )
        for k in ["title", "description", "pretty_url"]:
            if k in payload:
                assert resp.data[k] == payload[k]


@pytest.mark.django_db
def test_fetch_feed(client):

    feed = Feed.objects.create(url="https://example.com/rss.xml", title="Test Feed")
    job = Job.objects.create(feed=feed)
    with patch.object(FeedView, "new_fetch_job") as mock_fetch_job:
        mock_fetch_job.return_value = job
        url = f"/api/v1/feeds/{feed.id}/fetch/"
        resp = client.patch(url, content_type="application/json")
        assert resp.status_code == 201, resp.content
        assert str(resp.data["job_id"]) == str(job.id)
        mock_fetch_job.assert_called_once()
        mock_fetch_job.call_args[0][0].path == url


@pytest.mark.django_db
def test_new_fetch_job():
    request = Request(HttpRequest())
    feed = Feed.objects.create(
        url="https://example.com/rss.xml", title="Test Feed", feed_type="atom"
    )
    view = FeedView()
    view.request = request
    view.kwargs = dict(feed_id=feed.id)
    with (
        patch(
            "history4feed.app.views.task_helper.new_job",
            side_effect=lambda *args: Job.objects.create(feed=args[0]),
        ) as mock_new_job,
        patch(
            "history4feed.app.views.FeedFetchSerializer",
            side_effect=FeedFetchSerializer,
        ) as mock_fetch_feed_serializer,
    ):
        result = view.new_fetch_job(request)
        assert result.feed == feed
        mock_new_job.assert_called_once_with(result.feed, False)
        mock_fetch_feed_serializer.assert_called_once_with(
            feed, data=request.data, partial=True
        )


@pytest.mark.parametrize(
    ["filters", "expected"],
    [
        [dict(), (0, 1, 2)],
        [dict(title="fEed"), (0, 1, 2)],
        [dict(title="feed 2"), (1,)],
        [dict(description="-iption", title="feed"), (1,)],
        [dict(feed_type="skeleton"), (2,)],
    ],
)
@pytest.mark.django_db
def test_list_feed(client, filters, expected):
    feeds = [
        Feed.objects.create(
            url="https://example.com/rss1.xml",
            title="Test Feed 1",
            feed_type="atom",
            description="some description",
        ),
        Feed.objects.create(
            url="https://example.com/rss2.xml",
            title="Test Feed 2",
            feed_type="rss",
            description="descr-iption",
        ),
        Feed.objects.create(
            url="https://example.com/rss3.xml",
            title="Some other feed 3",
            feed_type="skeleton",
        ),
    ]
    expected_ids = {str(feeds[i].id) for i in expected}
    resp = client.get("/api/v1/feeds/", query_params=filters)
    assert resp.status_code == 200
    assert len(resp.data["feeds"]) == len(expected_ids)
    assert {feed["id"] for feed in resp.data["feeds"]} == expected_ids


@pytest.mark.django_db
def test_retrieve(client):
    feed = Feed.objects.create(
        url="https://example.com/rss1.xml",
        title="Test Feed 1",
        feed_type="atom",
        description="some description",
    )
    another_uuid = uuid.uuid4()
    resp = client.get(f"/api/v1/feeds/{feed.id}/")
    assert resp.status_code == 200
    assert resp.data["id"] == str(feed.id)

    resp = client.get(f"/api/v1/feeds/{another_uuid}/")
    assert resp.status_code == 404
