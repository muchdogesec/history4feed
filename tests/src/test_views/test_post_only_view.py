import pytest
from rest_framework import status
from history4feed.app.models import Job
from unittest.mock import patch
from history4feed.app.serializers import PostWithFeedIDSerializer
from history4feed.app.views import PostOnlyView
from dateutil.parser import parse as parse_date


from history4feed.app.utils import (
    Ordering,
    Pagination,
    MinMaxDateFilter,
)
from dogesec_commons.utils.filters import DatetimeFieldUTC

# from .openapi_params import FEED_PARAMS, POST_PARAMS

from history4feed.app.serializers import PostWithFeedIDSerializer
from history4feed.app.models import Job
from rest_framework import (
    status,
)
from django_filters.rest_framework import (
    DjangoFilterBackend,
)

from tests.utils import Transport


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
def test_partial_update_post(client, data, feed_posts, api_schema):
    _, (post, _) = feed_posts

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
    api_schema['/api/v1/posts/{post_id}/']['PATCH'].validate_response(Transport.get_st_response(response))
    


@pytest.mark.django_db
def test_destroy_post(client, feed_posts, api_schema):
    _, (post, _) = feed_posts

    url = f"/api/v1/posts/{post.id}/"

    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    post.refresh_from_db()
    assert post.deleted_manually is True

    response = client.get(url)
    assert (
        response.status_code == status.HTTP_404_NOT_FOUND
    ), "should already be deleted"
    api_schema['/api/v1/posts/{post_id}/']['DELETE'].validate_response(Transport.get_st_response(response))


@pytest.mark.django_db
def test_reindex_post(client, feed_posts, api_schema):
    feed, (post, _) = feed_posts

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
        api_schema['/api/v1/posts/{post_id}/reindex/']['PATCH'].validate_response(Transport.get_st_response(response))


@pytest.mark.django_db
def test_list_posts(client, feed_posts, api_schema):
    with patch(
        "history4feed.app.views.PostOnlyView.filter_queryset", side_effect=lambda qs: qs
    ) as mock_filter:

        url = "/api/v1/posts/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["posts"]) == 2  # Pagination applied
        for post in response.json()["posts"]:
            assert "description" not in post, "description should not be in the response"
        mock_filter.assert_called_once()
        api_schema['/api/v1/posts/']['GET'].validate_response(Transport.get_st_response(response))


@pytest.mark.django_db
def test_retrieve_post(client, feed_posts, api_schema):
    _, (post, _) = feed_posts

    url = f"/api/v1/posts/{post.id}/"
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(post.id)
    assert "description" not in response.json(), "description should not be in the response"
    api_schema['/api/v1/posts/{post_id}/']['GET'].validate_response(Transport.get_st_response(response))


@pytest.mark.django_db
def test_html_endpoint_returns_description(client, feed_posts, api_schema):
    """Test that /html endpoint returns the post's description with text/html content type"""
    _, (post, _) = feed_posts
    
    # Set a description for the post
    post.description = "<html><body><h1>This is the post content</h1></body></html>"
    post.save()
    
    url = f"/api/v1/posts/{post.id}/html/"
    response = client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response['Content-Type'] == 'text/html'
    assert response.content.decode() == post.description
    api_schema['/api/v1/posts/{post_id}/html/']['GET'].validate_response(Transport.get_st_response(response))

@pytest.mark.django_db
def test_html_endpoint_not_found(client, api_schema):
    """Test that /html endpoint returns 404 for non-existent post"""
    import uuid
    non_existent_id = uuid.uuid4()
    
    url = f"/api/v1/posts/{non_existent_id}/html/"
    response = client.get(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    api_schema['/api/v1/posts/{post_id}/html/']['GET'].validate_response(Transport.get_st_response(response))

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
