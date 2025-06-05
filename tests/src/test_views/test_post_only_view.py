import pytest
from rest_framework import status
from history4feed.app.models import Post, Feed, Job
from datetime import datetime as dt
from unittest.mock import patch
from history4feed.app.serializers import PostWithFeedIDSerializer
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


@pytest.mark.parametrize(
    "data",
    [
        dict(title="New title", pubdate="2024-01-01"),
        dict(pubdate="2021-01-01", author="new author 1"),
        dict(categories=['cat1', 'cat2'], author="new author 2"),
        dict(categories=['cat-1', 'cat0'], author="new author 3", pubdate='2025-01-01T10:59:01Z'),
    ]
)
@pytest.mark.django_db
def test_partial_update_post(client, data):
    feed = Feed.objects.create(title="test feed", url="https://example.com/")
    post = Post.objects.create(feed=feed, title="Old title", pubdate=dt.now())

    url = f"/api/v1/posts/{post.id}/"

    response = client.patch(url, data, content_type="application/json")

    assert response.status_code == status.HTTP_201_CREATED
    post.refresh_from_db()
    if title := data.get('title'):
        assert post.title == title
    if author := data.get('author'):
        assert post.author == author
    if categories := data.get('categories'):
        assert set([obj.name for obj in post.categories.all()]) == set(categories)
    if pubdate := data.get('pubdate'):
        assert post.pubdate == DatetimeFieldUTC().to_python(parse_date(pubdate))


@pytest.mark.django_db
def test_destroy_post(client):
    feed = Feed.objects.create(title="feed destroy test", url="https://example.com/")
    post = Post.objects.create(feed=feed, title="to be deleted", pubdate=dt.now())

    url = f"/api/v1/posts/{post.id}/"

    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    post.refresh_from_db()
    assert post.deleted_manually is True

    response = client.get(url)
    assert (
        response.status_code == status.HTTP_404_NOT_FOUND
    ), "should already be deleted"


@pytest.mark.django_db
def test_reindex_post(client):
    feed = Feed.objects.create(title="Reindex Test Feed", url="https://example.com/")
    post = Post.objects.create(feed=feed, title="Reindex Me", pubdate=dt.now())

    mock_job = Job.objects.create(state="pending", feed=feed)

    with patch(
        "history4feed.app.views.task_helper.new_patch_posts_job", return_value=mock_job
    ) as mock_task:
        url = f"/api/v1/posts/{post.id}/reindex/"
        data = {}

        response = client.patch(url, data, content_type="application/json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.json()
        assert response.json()["id"] == str(mock_job.id)
        assert response.json()["feed_id"] == str(feed.id)

        mock_task.assert_called_once_with(feed, [post])


@pytest.mark.django_db
def test_list_posts(client):
    feed = Feed.objects.create(title="list test feed", url="https://example.com/")
    Post.objects.create(feed=feed, title="First post", pubdate=dt.now())
    Post.objects.create(
        feed=feed,
        title="Second post",
        pubdate=dt.now(),
        link="https://example.net/post2",
    )

    with patch(
        "history4feed.app.views.PostOnlyView.filter_queryset", side_effect=lambda qs: qs
    ) as mock_filter:

        url = "/api/v1/posts/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["posts"]) == 2  # Pagination applied
        mock_filter.assert_called_once()


@pytest.mark.django_db
def test_retrieve_post(client):
    feed = Feed.objects.create(title="retrieve feed", url="https://example.com/")
    post = Post.objects.create(feed=feed, title="Single Post", pubdate=dt.now())

    url = f"/api/v1/posts/{post.id}/"
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(post.id)


def test_class_variables():
    assert PostOnlyView.ordering_fields == [
        "pubdate",
        "title",
        "datetime_updated",
        "datetime_added",
    ]
    assert PostOnlyView.ordering == "pubdate_descending", "default ordering"
    assert PostOnlyView.filter_backends == [
        DjangoFilterBackend,
        Ordering,
        MinMaxDateFilter,
    ]
    assert type(PostOnlyView.pagination_class) == Pagination
    assert PostOnlyView.pagination_class.results_key == "posts"
    assert PostOnlyView.serializer_class == PostWithFeedIDSerializer
