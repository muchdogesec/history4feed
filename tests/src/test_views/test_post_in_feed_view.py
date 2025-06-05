import pytest
from django.urls import reverse
from rest_framework import status
from history4feed.app.models import Feed, Job, Post
from uuid import uuid4
from unittest.mock import MagicMock, patch
from datetime import datetime as dt

from history4feed.app.serializers import JobSerializer, PostSerializer
from history4feed.app.views import FeedPostView, feed_post_view

import pytest
from rest_framework import status
from history4feed.app.models import Post, Feed, Job
from datetime import datetime as dt
from unittest.mock import patch
from history4feed.app.serializers import PostWithFeedIDSerializer
from history4feed.app.views import FeedPostView
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


@pytest.mark.django_db
def test_create_post_in_feed_success(client):
    feed = Feed.objects.create(url="https://example.com/rss.xml", title="Test Feed")
    job = Job.objects.create(feed=feed)

    with (
        patch.object(feed_post_view, "new_create_post_job") as mock_new_create_post_job,
        patch(
            "history4feed.app.views.JobSerializer", wraps=JobSerializer
        ) as mock_job_s_class,
    ):
        mock_new_create_post_job.return_value = job
        url = f"/api/v1/feeds/{feed.id}/posts/"

        payload = {
            "link": "https://example.com/test-post",
            "title": "Test Post",
            "pubdate": "2024-08-20T10:00:00.000Z",
        }

        resp = client.post(url, data=payload, content_type="application/json")
        assert mock_new_create_post_job.call_args[0][1] == feed.id
        assert mock_new_create_post_job.call_args[0][0].data == payload
        assert resp.status_code == status.HTTP_201_CREATED
        mock_job_s_class.assert_called_once_with(job)

        assert resp.data["id"] == str(job.id)
        assert resp.data["feed_id"] == str(job.feed.id)


@pytest.mark.django_db
def test_new_create_post_job():
    feed = Feed.objects.create(url="https://example.com/rss.xml", title="Test Feed")
    posts_data = [
        {
            "link": "https://example.com/test-post",
            "title": "Test Post",
            "pubdate": "2024-08-20T10:00:00.000Z",
        }
    ]
    payload = dict(posts=posts_data)
    request = MagicMock()
    request.data = payload
    with patch(
        "history4feed.app.views.task_helper.new_patch_posts_job"
    ) as mock_new_job:
        job = feed_post_view().new_create_post_job(request, feed.id)
        post = feed.posts.first()
        mock_new_job.assert_called_once_with(feed, [post])
        assert job == mock_new_job.return_value


@pytest.mark.django_db
def test_reindex_feed(client):
    feed = Feed.objects.create(url="https://example.com/rss.xml", title="Test Feed")
    p1 = Post.objects.create(feed=feed, title="First post", pubdate=dt.now())
    p2 = Post.objects.create(
        feed=feed,
        title="Second post",
        pubdate=dt.now(),
        link="https://example.net/post2",
    )
    job = Job.objects.create(feed=feed)
    with (
        patch("history4feed.app.views.task_helper.new_patch_posts_job") as mock_new_job,
        patch(
            "history4feed.app.views.JobSerializer",
            wraps=JobSerializer,
        ) as mock_job_s_class,
    ):
        mock_new_job.return_value = job
        resp = client.patch(f"/api/v1/feeds/{feed.id}/posts/reindex/")
        mock_new_job.assert_called_once_with(feed, (p1, p2))
        mock_job_s_class.assert_called_once_with(job)
        assert resp.data["id"] == str(job.id)
        assert resp.data["feed_id"] == str(job.feed.id)

