from datetime import UTC
import pytest

from datetime import UTC, datetime
import uuid
from history4feed.app import models
from history4feed.app.models import Feed, Post, FulltextJob, FullTextState
from history4feed.app.serializers import (
    PostSerializer,
    PostWithFeedIDSerializer,
    CreatePostsSerializer,
    JobSerializer,
)
from rest_framework.exceptions import ValidationError


def test_post_serializer_rejects_too_many_categories():
    serializer = PostSerializer(
        data={
            "title": "New Post",
            "link": "https://example.com/new-post",
            "pubdate": datetime.now(UTC).isoformat(),
            "author": "Author",
            "categories": [f"Category{i}" for i in range(33)],
        },
    )

    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)


def test_post_serializer_rejects_long_category_names():
    serializer = PostSerializer(
        data={
            "title": "New Post",
            "link": "https://example.com/new-post",
            "pubdate": datetime.now(UTC).isoformat(),
            "author": "Author",
            "categories": ["a" * 65],
        },
    )

    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
def test_post_serializdr__saves_categories_correctly(feed_posts):
    feed, _ = feed_posts
    categories = [f"Category{i}" for i in range(10)]
    serializer = PostSerializer(
        data={
            "title": "New Post",
            "link": "https://example.com/new-post",
            "pubdate": datetime.now(UTC).isoformat(),
            "author": "Author",
            "categories": categories,
        },
    )
    serializer = CreatePostsSerializer(
        data={
            "posts": [
                {
                    "title": "New Post",
                    "link": "https://example.com/new-post",
                    "pubdate": datetime.now(UTC).isoformat(),
                    "author": "Author",
                    "categories": categories,
                }
            ]
        },
        context={"feed_id": feed.id},
    )
    assert serializer.is_valid()
    instance = serializer.save()[0]
    assert {k.name for k in instance.categories.all()} == {
        models.slugify(x) for x in categories
    }


@pytest.mark.django_db
def test_create_posts_serializer__existing_url(feed_posts):
    feed, (post, _) = feed_posts
    serializer = CreatePostsSerializer(
        data={
            "posts": [
                {
                    "title": "New Post",
                    "link": post.link,  # Same link as existing post
                    "pubdate": post.pubdate.isoformat(),
                    "author": "Author",
                    "categories": ["Category1", "Category2"],
                }
            ]
        },
        context={"feed_id": feed.id},
    )
    assert not serializer.is_valid()
    assert "link" in serializer.errors["posts"][0]
    assert (
        serializer.errors["posts"][0]["link"][0]
        == f"Post at `{post.link}` already exists in feed."
    )


@pytest.mark.django_db
def test_create_posts_serializer__CREATE_POSTS_MAX_LENGTH():
    """Test that CreatePostsSerializer uses CREATE_POSTS_MAX_LENGTH from settings"""
    from history4feed.app.settings import history4feed_server_settings
    from unittest.mock import patch
    import importlib

    # Mock the settings value before the serializer class is evaluated
    with patch.object(history4feed_server_settings, "CREATE_POSTS_MAX_LENGTH", 2):
        # Reload the serializers module so it picks up the mocked value
        import history4feed.app.serializers as serializers_module

        importlib.reload(serializers_module)

        # Now create the serializer with 3 posts (exceeds limit of 2)
        serializer = serializers_module.CreatePostsSerializer(
            data={
                "posts": [
                    {
                        "title": "Post 1",
                        "link": "https://example.com/post1",
                        "pubdate": datetime.now(UTC).isoformat(),
                        "author": "Author",
                        "categories": ["Category1"],
                    },
                    {
                        "title": "Post 2",
                        "link": "https://example.com/post2",
                        "pubdate": datetime.now(UTC).isoformat(),
                        "author": "Author",
                        "categories": ["Category2"],
                    },
                    {
                        "title": "Post 3",
                        "link": "https://example.com/post3",
                        "pubdate": datetime.now(UTC).isoformat(),
                        "author": "Author",
                        "categories": ["Category3"],
                    },
                ]
            }
        )

        assert not serializer.is_valid()
        assert "posts" in serializer.errors
        assert "Ensure this field has no more than 2" in str(
            serializer.errors["posts"][0]
        )

    # Reload again to restore the original module state
    importlib.reload(serializers_module)


@pytest.mark.django_db
def test_post_serializer_excludes_description():
    """Test that PostSerializer does not return description field"""
    feed = Feed.objects.create(
        url="https://example.com/rss.xml",
        title="Test Feed",
        feed_type="rss",
        id=uuid.UUID("6ca6ce37-1c69-4a81-8490-89c91b57e557"),
    )

    post = Post.objects.create(
        feed=feed,
        title="Test Post",
        pubdate=datetime.now(UTC),
        link="https://example.net/post1",
        description="This is a long HTML description that should not be returned",
        id=uuid.UUID("561ed102-7584-4b7d-a302-43d4bca5605b"),
    )

    serializer = PostSerializer(post)
    data = serializer.data

    # Verify description is NOT in the serialized data
    assert (
        "description" not in data
    ), "description field should not be in serialized output"


@pytest.mark.django_db
def test_post_with_feed_id_serializer_excludes_description():
    """Test that PostWithFeedIDSerializer does not return description field"""
    feed = Feed.objects.create(
        url="https://example.com/rss.xml",
        title="Test Feed",
        feed_type="rss",
        id=uuid.UUID("6ca6ce37-1c69-4a81-8490-89c91b57e557"),
    )

    post = Post.objects.create(
        feed=feed,
        title="Test Post",
        pubdate=datetime.now(UTC),
        link="https://example.net/post1",
        description="This is a long HTML description that should not be returned",
        id=uuid.UUID("561ed102-7584-4b7d-a302-43d4bca5605b"),
    )

    serializer = PostWithFeedIDSerializer(post)
    data = serializer.data

    # Verify description is NOT in the serialized data
    assert (
        "description" not in data
    ), "description field should not be in serialized output"


@pytest.mark.django_db
def test_post_serializer_includes_other_fields():
    """Test that PostSerializer includes all expected fields except description"""
    feed = Feed.objects.create(
        url="https://example.com/rss.xml",
        title="Test Feed",
        feed_type="rss",
        id=uuid.UUID("6ca6ce37-1c69-4a81-8490-89c91b57e557"),
    )

    post = Post.objects.create(
        feed=feed,
        title="Test Post",
        pubdate=datetime.now(UTC),
        link="https://example.net/post1",
        author="Test Author",
        description="This should be excluded",
        id=uuid.UUID("561ed102-7584-4b7d-a302-43d4bca5605b"),
    )

    serializer = PostSerializer(post)
    data = serializer.data

    # Verify other important fields are still present
    assert "id" in data
    assert "title" in data
    assert data["title"] == "Test Post"
    assert "link" in data
    assert data["link"] == "https://example.net/post1"
    assert "author" in data
    assert data["author"] == "Test Author"
    assert "pubdate" in data
    assert "datetime_added" in data
    assert "datetime_updated" in data


@pytest.mark.django_db
def test_job_serializer__serializes_url(jobs):
    job = jobs[0]
    job.run_datetime = datetime(2020, 1, 1, 12, 12, 12, tzinfo=UTC)
    job.save()
    FulltextJob.objects.create(
        job=job,
        status=FullTextState.FAILED,
        error_str="failed for no reason",
        link="http://example.co/1",
    )
    FulltextJob.objects.create(
        job=job,
        status=FullTextState.RETRIEVED,
        error_str="was successful, will not be shown",
        link="http://example.co/1",
    )
    s = JobSerializer(job)
    assert s.data == {
        "id": str(job.id),
        "feed_id": str(job.feed_id),
        "urls": {
            "retrieved": [{"url": "http://example.co/1", "id": None}],
            "retrieving": [],
            "skipped": [],
            "failed": [
                {
                    "url": "http://example.co/1",
                    "id": None,
                    "error": "failed for no reason",
                }
            ],
            "cancelled": [],
            "timed_out": [],
        },
        "state": "pending",
        "run_datetime": "2020-01-01T12:12:12Z",
        "earliest_item_requested": None,
        "latest_item_requested": None,
        "info": "",
        "include_remote_blogs": False,
        "completion_time": None,
        "extra_data": {},
    }
