from unittest.mock import call, patch

import pytest
from history4feed.app.models import Feed, Post
from datetime import UTC, datetime as dt

from history4feed.h4fscripts.build_rss import build_entry_element, build_rss


@pytest.mark.django_db
def test_create_rss():
    feed = Feed.objects.create(url="https://example.com/rss.xml", title="Test Feed")
    posts = [
        Post.objects.create(
            feed=feed,
            title="First post",
            pubdate=dt.now(UTC),
            link="http://example.com/post/1/",
        ),
        Post.objects.create(
            feed=feed,
            title="First post 2",
            pubdate=dt.now(UTC),
            link="http://example.com/post/3/",
            author="some author",
        ),
        Post.objects.create(
            feed=feed,
            title="Second post",
            pubdate=dt.now(UTC),
            link="https://example.net/post2",
        ),

        Post.objects.create(
            feed=feed,
            title="Third post with description",
            description="The description",
            pubdate=dt.now(UTC),
            link="http://example.com/post/6/",
        ),
    ]
    posts[2].add_categories(["cat1"])

    with patch(
        "history4feed.h4fscripts.build_rss.build_entry_element",
        side_effect=build_entry_element,
    ) as mock_build_post_entry:

        build_rss(feed, posts)
        d = mock_build_post_entry.call_args[0][1]
        mock_build_post_entry.assert_has_calls(
            [call(post, d) for post in posts], any_order=True
        )
