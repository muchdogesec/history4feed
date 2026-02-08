from history4feed.app.serializers import CreatePostsSerializer
from datetime import datetime as dt, UTC
import pytest

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

