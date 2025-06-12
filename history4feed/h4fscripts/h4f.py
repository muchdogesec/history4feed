from dataclasses import dataclass
import time
from io import BytesIO, StringIO
from xml.dom.minidom import Element, parse
import os
from history4feed.app.settings import history4feed_server_settings as settings
import requests
from dateutil.parser import parse as parse_date
from readability import Document as ReadabilityDocument
import brotli
from types import SimpleNamespace
from .import logger
from .xml_utils import getAtomLink, getFirstChildByTag, getFirstElementByTag, getText
from .exceptions import history4feedException, UnknownFeedtypeException, FetchRedirect, ScrapflyError
import fake_useragent
from urllib.parse import urljoin

def fetch_page_with_retries(url, retry_count=3, sleep_seconds=settings.WAYBACK_SLEEP_SECONDS, **kwargs):
    ua = fake_useragent.UserAgent()
    session = requests.Session()
    session.max_redirects = 3
    headers = kwargs.get('headers', {})
    headers.update({
        "User-Agent": ua.random,
    })
    kwargs.update(headers=headers)
    error = None
    for i in range(retry_count+1):
        try:
            if i > 0:
                time.sleep(sleep_seconds * 1.5 ** (i-1))
            return fetch_page(session, url, **kwargs)
        except FatalError:
            raise
        except BaseException as e:
            error = e
            print(error)
    raise ConnectionError(f"could not fetch page after {retry_count} retries") from error
    
class FatalError(Exception):
    pass

def fetch_page(session, url, headers=None) -> tuple[bytes, str, str]:
    proxy_apikey = settings.SCRAPFLY_APIKEY
    headers = headers or {}

    if proxy_apikey:
        headers, result = fetch_with_scapfly(session, url, headers, proxy_apikey)
        return result.content.encode(), result.content_type, result.url

    logger.info(f"Fetching `{url}`")
    resp: requests.Response  = session.get(url, headers=headers)
    content = resp.content
    if not resp.ok:
        raise history4feedException(f"GET Request failed for `{url}`, status: {resp.status_code}, reason: {resp.reason}")

    # some times, wayback returns br encoding, try decompressing
    try:
        content = brotli.decompress(content)
    except Exception as err:
        logger.print(f"brotli decompress fail: {err}")
    return content, resp.headers.get("content-type"), resp.url

def fetch_with_scapfly(session, url, headers, proxy_apikey):
    logger.info(f"Fetching `{url}` via scrapfly.io")
    headers = dict((f"headers[{k}]", v) for k, v in headers.items())
    resp = session.get("https://api.scrapfly.io/scrape", params=dict(**headers, key=proxy_apikey, url=url, country="us,ca,mx,gb,fr,de,au,at,be,hr,cz,dk,ee,fi,ie,se,es,pt,nl"))
    json_data = resp.json()
    if resp.status_code != 200:
        raise ScrapflyError(json_data)
    result = SimpleNamespace(**json_data['result'])
    if result.status_code > 499:
        raise FatalError(f"Got server error {result.status_code}, stopping")
    if result.status_code > 399:
        raise history4feedException(f"PROXY_GET Request failed for `{url}`, status: {result.status_code}, reason: {result.status}")
    elif result.status_code > 299:
        raise FetchRedirect(f"PROXY_GET for `{url}` redirected, status: {result.status_code}, reason: {result.status}")
    return headers,result

def parse_feed_from_url(url):
    data, content_type, url = fetch_page_with_retries(url, retry_count=0)
    return parse_feed_from_content(data, url)

def get_full_text(link):
    try:
        page, content_type, url = fetch_page_with_retries(link)
        doc  = ReadabilityDocument(page.decode(), url=url)
        return doc.summary(), content_type
    except BaseException as e:
        raise history4feedException(f"Error processing fulltext: {e}") from e


@dataclass
class PostDict:
    link: str
    title: str
    pubdate: str
    author: str = None
    categories: list[str] = None
    description: str = "EMPTY BODY"
    content_type: str =  "text/html"

def parse_feed_from_content(data: bytes, url: str):
    feed_data = {}
    try:
        if isinstance(data, str):
            document = parse(StringIO(data))
        else:
            document = parse(BytesIO(data))
        # check if it's atom or rss
        if rss := getFirstElementByTag(document, "rss"):
            channel = getFirstElementByTag(rss, "channel")
            feed_data['description'] = getText(getFirstElementByTag(channel, "description"))
            feed_data['title'] = getText(getFirstElementByTag(channel, "title"))
            # feed_data['rel'] = getText(getFirstElementByTag(channel, "link"))

            feed_data["feed_type"] = "rss"
        elif feed := getFirstElementByTag(document, "feed"):
            feed_data['description'] = getText(getFirstElementByTag(feed, "subtitle"))
            feed_data['title'] = getText(getFirstElementByTag(feed, "title"))
            # feed_data['rel'] = getAtomLink(feed)

            feed_data["feed_type"] = "atom"
        else:
            raise UnknownFeedtypeException("feed is neither RSS or ATOM")
        feed_data["url"] = url
        return feed_data
    except BaseException as e:
        raise UnknownFeedtypeException(f"Failed to parse feed from `{url}`") from e

def get_publish_date(item):
    published = getFirstElementByTag(item, "published")
    if not published:
        published = getFirstElementByTag(item, "pubDate")
    return parse_date(getText(published))

def get_categories(entry: Element) -> list[str]:
    categories = []
    for category in entry.getElementsByTagName('category'):
        cat = category.getAttribute('term') or getText(category)
        if not cat:
            cat = category
        categories.append(cat)
    return categories

def get_author(item):
    author = getFirstElementByTag(item, "dc:creator")
    if not author:
        author = getFirstElementByTag(item, "author")
        author = getFirstElementByTag(author, "name") or author
    return getText(author)


def parse_items(elem, link):
    return PostDict(
        # element = elem,
        link = link,
        title = getText(getFirstElementByTag(elem, "title")),
        pubdate = get_publish_date(elem),
        author = get_author(elem),
        categories = get_categories(elem),
        description="",
        content_type="plain/text",
    )

def parse_posts_from_rss_feed(base_url, data) -> dict[str, PostDict]:
    entries = {}
    document = parse(BytesIO(data))
    channel = getFirstElementByTag(document, "channel")

    for item in channel.getElementsByTagName("item"):
        link = urljoin(base_url, getText(getFirstElementByTag(item, "link")).strip())
        entries[link] = parse_items(item, link)
        entries[link].description = parse_rss_description(item)
    return entries

def parse_posts_from_atom_feed(base_url, data):
    entries = {}
    document = parse(BytesIO(data))

    for item in document.getElementsByTagName("entry"):
        link = urljoin(base_url, getAtomLink(item, rel='alternate'))
        entries[link] = parse_items(item, link)
        entries[link].description, content_type = parse_atom_description(item)
        if content_type:
            entries[link].content_type = content_type
    return entries

def parse_atom_description(item: Element):
    description = ""
    if summary := getFirstChildByTag(item, "summary"):
        description = getText(summary)
    if content := getFirstChildByTag(item, "content"):
        description = getText(content)
    return description, None

def parse_rss_description(item: Element):
    return getText(getFirstChildByTag(item, "description"))
