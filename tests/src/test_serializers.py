from datetime import UTC
import pytest

from datetime import UTC, datetime
import uuid
from history4feed.app.models import Feed, Post
from history4feed.app.serializers import PostSerializer, PostWithFeedIDSerializer, CreatePostsSerializer


@pytest.mark.django_db
def test_create_posts_serializer__existing_url(feed_posts):
    feed, (post, _) = feed_posts
    serializer = CreatePostsSerializer(data={
        "posts": [
            {
                "title": "New Post",
                "link": post.link,  # Same link as existing post
                "pubdate": post.pubdate.isoformat(),
                "author": "Author",
                "categories": ["Category1", "Category2"],
            }
        ]
    }, context={'feed_id': feed.id})
    assert not serializer.is_valid()
    assert 'link' in serializer.errors['posts'][0]
    assert serializer.errors['posts'][0]['link'][0] == f'Post at `{post.link}` already exists in feed.'



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
    assert 'description' not in data, "description field should not be in serialized output"


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
    assert 'description' not in data, "description field should not be in serialized output"


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
    assert 'id' in data
    assert 'title' in data
    assert data['title'] == "Test Post"
    assert 'link' in data
    assert data['link'] == "https://example.net/post1"
    assert 'author' in data
    assert data['author'] == "Test Author"
    assert 'pubdate' in data
    assert 'datetime_added' in data
    assert 'datetime_updated' in data
