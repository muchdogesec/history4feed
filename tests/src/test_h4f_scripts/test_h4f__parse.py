import pytest
from history4feed.h4fscripts.h4f import (
    parse_feed_from_content,
    parse_posts_from_atom_feed,
    parse_posts_from_rss_feed,
)
from .rss_data import rss_example, atom_example
from datetime import datetime, UTC

@pytest.mark.parametrize(
    ["data", "url", "expected_feed_data"],
    [
        pytest.param(
            rss_example,
            "https://some_url.net/",
            dict(
                title="Your awesome title",
                description="RSS -- Contains encoded html -- PARTIAL CONTENT ONLY",
                feed_type="rss",
            ),
            id="parse_rss",
        ),
        pytest.param(
            atom_example,
            "https://some_url.net/",
            dict(
                title="Your awesome title",
                description="ATOM -- Contains decoded html inside CDATA tags -- PARTIAL CONTENT ONLY",
                url="",
                feed_type="atom",
            ),
            id="parse_atom",
        ),
    ],
)
def test_parse_feed_from_content(data, url, expected_feed_data):
    feed_data = parse_feed_from_content(data, url)
    for k, v in expected_feed_data.items():
        if v:
            assert feed_data[k] == v


def test_parse_posts_from_rss_feed():
    posts = parse_posts_from_rss_feed("https://example.blog/rss/", rss_example.encode())
    expected_links = [
        (
            "https://muchdogesec.github.io/fakeblog123///test1/2024/09/01/same-ioc-across-posts.html",
            datetime(2024, 9, 1, 8, 0, tzinfo=UTC),
        ),
        (
            "https://muchdogesec.github.io/fakeblog123///test1/2024/08/23/obstracts-ai-relationships.html",
            datetime(2024, 8, 23, 8, 0, tzinfo=UTC),
        ),
        (
            "https://muchdogesec.github.io/fakeblog123///test3/2024/08/20/update-to-post-1.html",
            datetime(2024, 8, 20, 10, 0, tzinfo=UTC),
        ),
        (
            "https://muchdogesec.github.io/fakeblog123///test2/2024/08/07/testing-extractions-1.html",
            datetime(2024, 8, 7, 8, 0, tzinfo=UTC),
        ),
        (
            "https://muchdogesec.github.io/fakeblog123///test2/2024/08/05/testing-markdown-elements-1.html",
            datetime(2024, 8, 5, 8, 0, tzinfo=UTC),
        ),
        (
            "https://muchdogesec.github.io/fakeblog123///test1/2024/08/01/real-post-example-1.html",
            datetime(2024, 8, 1, 8, 0, tzinfo=UTC),
        ),
    ]
    links_and_dates = [(k.link, k.pubdate) for k in posts.values()]
    assert links_and_dates == expected_links

def test_parse_posts_from_atom_feed():
    posts = parse_posts_from_atom_feed(
        "https://example.blog/rss/", atom_example.encode()
    )
    expected_links = [
        (
            "https://muchdogesec.github.io/fakeblog123///test1/2024/09/01/same-ioc-across-posts.html",
            datetime(2024, 9, 1, 8, 0, tzinfo=UTC),
        ),
        (
            "https://muchdogesec.github.io/fakeblog123///test1/2024/08/23/obstracts-ai-relationships.html",
            datetime(2024, 8, 23, 8, 0, tzinfo=UTC),
        ),
        (
            "https://muchdogesec.github.io/fakeblog123///test3/2024/08/20/update-to-post-1.html",
            datetime(2024, 8, 20, 10, 0, tzinfo=UTC),
        ),
        (
            "https://muchdogesec.github.io/fakeblog123///test2/2024/08/07/testing-extractions-1.html",
            datetime(2024, 8, 7, 8, 0, tzinfo=UTC),
        ),
        (
            "https://muchdogesec.github.io/fakeblog123///test2/2024/08/05/testing-markdown-elements-1.html",
            datetime(2024, 8, 5, 8, 0, tzinfo=UTC),
        ),
        (
            "https://muchdogesec.github.io/fakeblog123///test1/2024/08/01/real-post-example-1.html",
            datetime(2024, 8, 1, 8, 0, tzinfo=UTC),
        ),
        (
            "https://muchdogesec.github.io/fakeblog123///test1/2024/08/01/feed-with-no-published-date.html",
            datetime(2024, 8, 1, 12, 30, tzinfo=UTC)
        )
    ]
    links_and_dates = [(k.link, k.pubdate) for k in posts.values()]
    assert links_and_dates == expected_links
