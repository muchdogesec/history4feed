import pytest
from unittest.mock import patch, MagicMock
from requests import Response
from history4feed.app.settings import History4FeedServerSettings
from history4feed.h4fscripts.h4f import (
    fetch_page_with_retries,
    fetch_page,
    fetch_with_scapfly,
    FatalError,
    parse_feed_from_url
)
from history4feed.h4fscripts.exceptions import history4feedException, ScrapflyError, FetchRedirect
from types import SimpleNamespace
from history4feed.h4fscripts.h4f import get_full_text
from history4feed.h4fscripts.exceptions import history4feedException
from readability import Document as ReadabilityDocument

@pytest.fixture
def dummy_url():
    return "https://example.com/test"


@patch("history4feed.h4fscripts.h4f.time.sleep", return_value=None)
@patch("history4feed.h4fscripts.h4f.fetch_page")
@patch("history4feed.h4fscripts.h4f.fake_useragent.UserAgent")
def test_fetch_page_with_retries_success(mock_ua, mock_fetch_page, mock_sleep, dummy_url):
    mock_ua().random = "test-agent"
    mock_fetch_page.return_value = (b"html", "text/html", dummy_url)

    result = fetch_page_with_retries(dummy_url)
    assert result == (b"html", "text/html", dummy_url)
    assert mock_fetch_page.call_count == 1
    mock_sleep.assert_not_called()


@patch("history4feed.h4fscripts.h4f.time.sleep", return_value=None)
@patch("history4feed.h4fscripts.h4f.fetch_page")
@patch("history4feed.h4fscripts.h4f.fake_useragent.UserAgent")
def test_fetch_page_with_retries_with_retry(mock_ua, mock_fetch_page, mock_sleep, dummy_url):
    mock_ua().random = "test-agent"
    mock_fetch_page.side_effect = [Exception("fail"), (b"ok", "text/html", dummy_url)]

    result = fetch_page_with_retries(dummy_url, retry_count=1)
    assert result == (b"ok", "text/html", dummy_url)
    assert mock_fetch_page.call_count == 2
    mock_sleep.assert_called_once()


@patch("history4feed.h4fscripts.h4f.time.sleep", return_value=None)
@patch("history4feed.h4fscripts.h4f.fetch_page")
@patch("history4feed.h4fscripts.h4f.fake_useragent.UserAgent")
def test_fetch_page_with_retries_fatal_error(mock_ua, mock_fetch_page, mock_sleep, dummy_url):
    mock_ua().random = "test-agent"
    mock_fetch_page.side_effect = FatalError("fatal")

    with pytest.raises(FatalError):
        fetch_page_with_retries(dummy_url)
    mock_sleep.assert_not_called()


@patch("history4feed.h4fscripts.h4f.time.sleep", return_value=None)
@patch("history4feed.h4fscripts.h4f.fetch_page")
@patch("history4feed.h4fscripts.h4f.fake_useragent.UserAgent")
def test_fetch_page_with_retries_exhausts(mock_ua, mock_fetch_page, mock_sleep, dummy_url):
    mock_ua().random = "test-agent"
    mock_fetch_page.side_effect = Exception("fail")

    with pytest.raises(ConnectionError) as e:
        fetch_page_with_retries(dummy_url, retry_count=2)
    assert "could not fetch page after 2 retries" in str(e.value)
    assert mock_fetch_page.call_count == 3
    assert mock_sleep.call_count == 2  # Should sleep after each failed attempt



# -------------------
# fetch_page (direct)
# -------------------

@patch("history4feed.h4fscripts.h4f.logger")
def test_fetch_page_success(mock_logger, dummy_url):
    session = MagicMock()
    response = MagicMock(spec=Response)
    response.ok = True
    response.content = b"html-content"
    response.headers = {"content-type": "text/html"}
    response.url = dummy_url
    session.get.return_value = response

    content, content_type, final_url = fetch_page(session, dummy_url)

    session.get.assert_called_once_with(dummy_url, headers={})
    assert content == b"html-content"
    assert content_type == "text/html"
    assert final_url == dummy_url

@patch('history4feed.h4fscripts.h4f.fetch_with_scapfly')
def test_fetch_page_uses_scrapfly(mock_fetch, settings, dummy_url):
    api_key = "some value"
    session = MagicMock()
    settings.HISTORY4FEED_SETTINGS = {
        'SCRAPFLY_APIKEY': api_key
    }
    mocked_resp = MagicMock()
    mock_fetch.return_value = [None, mocked_resp]
    result = fetch_page(session, dummy_url)
    mock_fetch.assert_called_once_with(session, dummy_url, {}, api_key)
    assert result == (mocked_resp.content.encode(), mocked_resp.content_type, mocked_resp.url)


@patch("history4feed.h4fscripts.h4f.logger")
def test_fetch_page_not_ok_raises(mock_logger, dummy_url):
    session = MagicMock()
    response = MagicMock()
    response.ok = False
    response.status_code = 500
    response.reason = "Internal Error"
    session.get.return_value = response

    with pytest.raises(history4feedException):
        fetch_page(session, dummy_url)

    session.get.assert_called_once_with(dummy_url, headers={})


@patch("history4feed.h4fscripts.h4f.logger")
@patch("history4feed.h4fscripts.h4f.brotli.decompress", side_effect=Exception("decompress failed"))
def test_fetch_page_brotli_fails(mock_brotli, mock_logger, dummy_url):
    session = MagicMock()
    response = MagicMock()
    response.ok = True
    response.content = b"compressed"
    response.headers = {"content-type": "text/html"}
    response.url = dummy_url
    session.get.return_value = response

    content, ctype, url = fetch_page(session, dummy_url)
    mock_brotli.assert_called_once_with(b"compressed")
    assert content == b"compressed"  # returned as-is due to decompress failure


# ------------------------
# fetch_with_scapfly
# ------------------------

def test_fetch_with_scapfly_success(dummy_url):
    session = MagicMock()
    result_data = {
        "result": {
            "content": "<html></html>",
            "content_type": "text/html",
            "url": dummy_url,
            "status_code": 200,
            "status": "OK"
        }
    }
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = result_data
    session.get.return_value = response

    headers = {"User-Agent": "curl"}
    proxy_apikey = "abc123"

    returned_headers, result = fetch_with_scapfly(session, dummy_url, headers, proxy_apikey)

    assert result.content == "<html></html>"
    assert result.content_type == "text/html"
    assert result.url == dummy_url

    expected_params = {
        "headers[User-Agent]": "curl",
        "key": proxy_apikey,
        "url": dummy_url,
        "country": "us,ca,mx,gb,fr,de,au,at,be,hr,cz,dk,ee,fi,ie,se,es,pt,nl"
    }
    session.get.assert_called_once_with("https://api.scrapfly.io/scrape", params=expected_params)


def test_fetch_with_scapfly_fail_error(dummy_url):
    session = MagicMock()
    response = MagicMock()
    response.status_code = 500
    response.json.return_value = {"result": {}, "message": "Server error"}
    session.get.return_value = response

    with pytest.raises(ScrapflyError):
        fetch_with_scapfly(session, dummy_url, {"User-Agent": "UA"}, "apikey")


def test_fetch_with_scapfly_500_error(dummy_url):
    session = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"result": {"status_code": 500,}, "message": "Server error"}
    session.get.return_value = response

    with pytest.raises(FatalError):
        fetch_with_scapfly(session, dummy_url, {"User-Agent": "UA"}, "apikey")


def test_fetch_with_scapfly_redirect(dummy_url):
    session = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "result": {
            "status_code": 302,
            "status": "Redirected",
            "content": "",
            "url": dummy_url,
            "content_type": "text/html"
        }
    }
    session.get.return_value = response

    with pytest.raises(FetchRedirect):
        fetch_with_scapfly(session, dummy_url, {"User-Agent": "UA"}, "apikey")


# ---------------------
# get_full_text
# ---------------------

@patch("history4feed.h4fscripts.h4f.ReadabilityDocument", side_effect=ReadabilityDocument)
@patch("history4feed.h4fscripts.h4f.fetch_page_with_retries")
@patch.object(ReadabilityDocument, 'summary', side_effect=ReadabilityDocument.summary, autospec=True)
def test_get_full_text_success(mock_summary, mock_fetch, mock_readability, dummy_url):
    mock_fetch.return_value = (b"<html>Article</html>", "text/html", dummy_url)

    summary, ctype = get_full_text(dummy_url)

    assert isinstance(summary, str)
    assert ctype == "text/html"
    mock_fetch.assert_called_once_with(dummy_url)
    mock_readability.assert_called_once_with("<html>Article</html>", url=dummy_url)
    mock_summary.assert_called_once()


@patch("history4feed.h4fscripts.h4f.fetch_page_with_retries", side_effect=Exception("failure"))
def test_get_full_text_raises(mock_fetch, dummy_url):
    with pytest.raises(history4feedException) as e:
        get_full_text(dummy_url)
    assert "Error processing fulltext: failure" in str(e.value)


@patch('history4feed.h4fscripts.h4f.fetch_page_with_retries')
@patch('history4feed.h4fscripts.h4f.parse_feed_from_content')
def test_parse_feed_from_url(mock_parse: MagicMock, mock_fetch: MagicMock):
    mock_fetch.return_value = [1, 2, 3]
    url = "https://soem.url/"
    parse_feed_from_url(url)
    mock_fetch.assert_called_once_with(url, retry_count=0)
    mock_parse.assert_called_once_with(1, 3)
