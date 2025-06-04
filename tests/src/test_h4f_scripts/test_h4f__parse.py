import pytest
from history4feed.h4fscripts.h4f import (
    parse_feed_from_content,
    parse_posts_from_atom_feed,
    parse_posts_from_rss_feed,
)
from .rss_data import rss_example, atom_example


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
        "https://muchdogesec.github.io/fakeblog123///test1/2024/09/01/same-ioc-across-posts.html",
        "https://muchdogesec.github.io/fakeblog123///test1/2024/08/23/obstracts-ai-relationships.html",
        "https://muchdogesec.github.io/fakeblog123///test3/2024/08/20/update-to-post-1.html",
        "https://muchdogesec.github.io/fakeblog123///test2/2024/08/07/testing-extractions-1.html",
        "https://muchdogesec.github.io/fakeblog123///test2/2024/08/05/testing-markdown-elements-1.html",
        "https://muchdogesec.github.io/fakeblog123///test1/2024/08/01/real-post-example-1.html",
    ]

    assert expected_links == list(posts)


def test_parse_posts_from_atom_feed():
    posts = parse_posts_from_atom_feed(
        "https://example.blog/rss/", atom_example.encode()
    )
    expected_links = [
        "https://muchdogesec.github.io/fakeblog123///test1/2024/09/01/same-ioc-across-posts.html",
        "https://muchdogesec.github.io/fakeblog123///test1/2024/08/23/obstracts-ai-relationships.html",
        "https://muchdogesec.github.io/fakeblog123///test3/2024/08/20/update-to-post-1.html",
        "https://muchdogesec.github.io/fakeblog123///test2/2024/08/07/testing-extractions-1.html",
        "https://muchdogesec.github.io/fakeblog123///test2/2024/08/05/testing-markdown-elements-1.html",
        "https://muchdogesec.github.io/fakeblog123///test1/2024/08/01/real-post-example-1.html",
    ]

    assert expected_links == list(posts)
