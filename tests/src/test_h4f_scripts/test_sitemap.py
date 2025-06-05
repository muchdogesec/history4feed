import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from history4feed.h4fscripts.sitemap_helpers import (
    fetch_posts_links_with_serper,
    SearchIndexError,
)


@pytest.fixture
def mock_response():
    def _make_response(organic_items, credits=1):
        response = MagicMock()
        response.ok = True
        response.json.return_value = {"organic": organic_items, "credits": credits}
        print(response.json.return_value)
        return response

    return _make_response


@patch("history4feed.h4fscripts.sitemap_helpers.requests.Session.get")
def test_fetch_posts_links_basic(mock_get, mock_response):
    from_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    to_time = datetime(2024, 1, 2, tzinfo=timezone.utc)

    mock_get.return_value = mock_response(
        [
            {
                "title": "Example Title",
                "link": "https://example.com/post",
                "date": "Jan 1, 2024",
            }
        ]
    )

    result = fetch_posts_links_with_serper("example.com", from_time, to_time)

    assert len(result) == 1
    post = result["https://example.com/post"]
    assert post.title == "Example Title"
    assert post.link == "https://example.com/post"
    assert post.pubdate.date() == datetime(2024, 1, 1).date()


@patch("history4feed.h4fscripts.sitemap_helpers.requests.Session.get")
def test_fetch_posts_links_multiple_pages(mock_get, mock_response):
    mock_get.side_effect = [
        mock_response(
            [
                {"title": "Post 1", "link": "https://x1.com/1", "date": "Jan 1, 2024"},
            ]
        ),
        mock_response(
            [
                {"title": "Post 2", "link": "https://x2.com/2", "date": "Jan 5, 2024"},
            ],
            credits=19,
        ),
        mock_response([], credits=1),  # Triggers page exit
    ]

    from_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    to_time = datetime(2024, 1, 3, tzinfo=timezone.utc)

    result = fetch_posts_links_with_serper("x.com", from_time, to_time, delta_days=3)

    assert len(result) == 2
    assert ["https://x1.com/1", "https://x2.com/2"] == list(result)


@patch("history4feed.h4fscripts.sitemap_helpers.requests.Session.get")
def test_fetch_posts_handles_no_date(mock_get, mock_response):
    # Entry with no 'date'
    mock_get.return_value = mock_response(
        [{"title": "No Date", "link": "https://example.com/nodate"}]
    )

    from_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    to_time = datetime(2024, 1, 2, tzinfo=timezone.utc)

    result = fetch_posts_links_with_serper("example.com", from_time, to_time)

    assert "https://example.com/nodate" in result
    post = result["https://example.com/nodate"]
    assert post.pubdate <= to_time


@patch("history4feed.h4fscripts.sitemap_helpers.requests.Session.get")
def test_fetch_posts_raises_on_error_status(mock_get):
    mock_get.return_value.ok = False
    mock_get.return_value.status_code = 403
    mock_get.return_value.text = "Forbidden"

    from_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(SearchIndexError) as exc:
        fetch_posts_links_with_serper("fail.com", from_time)

    assert "403" in str(exc.value)
