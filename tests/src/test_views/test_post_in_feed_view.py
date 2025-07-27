import pytest
from rest_framework import status
from history4feed.app.models import Feed, Job
from unittest.mock import MagicMock, patch

from history4feed.app.serializers import JobSerializer
from history4feed.app.views import feed_post_view

import pytest
from rest_framework import status
from history4feed.app.models import Feed, Job
from unittest.mock import patch



# from .openapi_params import FEED_PARAMS, POST_PARAMS

from history4feed.app.models import Feed, Job
from rest_framework import (
    status,
)

from tests.utils import Transport


@pytest.mark.django_db
def test_create_post_in_feed_success(client, api_schema):
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

        api_schema['/api/v1/feeds/{feed_id}/posts/']['POST'].validate_response(Transport.get_st_response(resp))

@pytest.mark.django_db
def test_new_create_post_job(feed):
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
def test_reindex_feed(client, feed_posts, api_schema):
    feed, posts = feed_posts
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
        mock_new_job.assert_called_once_with(feed, posts)
        mock_job_s_class.assert_called_once_with(job)
        assert resp.data["id"] == str(job.id)
        assert resp.data["feed_id"] == str(job.feed.id)
        api_schema['/api/v1/feeds/{feed_id}/posts/reindex/']['PATCH'].validate_response(Transport.get_st_response(resp))

