import json
import time
from datetime import datetime as dt, UTC
from collections import namedtuple
from urllib.parse import urlencode
from .h4f import FatalError, fetch_page_with_retries
from history4feed.app.settings import history4feed_server_settings as settings

DEFAULT_USER_AGENT = "curl"


CDXSearchResult = namedtuple("CDXSearchResult", ["urlkey", "timestamp", "original_url", "mimetype", "statuscode", "digest", "length"])

def cdx_search(url, earliest: dt, latest: dt=None, retry_count=3, sleep_seconds=settings.WAYBACK_SLEEP_SECONDS, user_agent="curl") -> list[CDXSearchResult]:
    latest = latest or dt.now(UTC)
    query = urlencode([
        ("from", as_wayback_date(earliest)),
        ("to", as_wayback_date(latest)),
        ("url", url),
        ("filter", "statuscode:200"),
        ("output", "json"),
        ("collapse", "digest"),
    ])

    headers = {}

    error = None

    for i in range(retry_count+1):
        if i > 0:
            time.sleep(sleep_seconds * 1.5**(i-1))
        try:
            res, content_type, _ = fetch_page_with_retries(f"http://web.archive.org/cdx/search/cdx?{query}", headers=headers)
            res_json = json.loads(res)
            error = None
            break
        except FatalError:
            return []
        except BaseException as e:
            error = e
            continue
    if error:
        raise error
    out = {}
    for v in res_json[1:]:
        try:
            v[6] = int(v[6])
            v[4] = int(v[4])
            v = CDXSearchResult(*v)
            out[v.digest] = v
        except:
            pass
    return list(out.values())
        
def as_wayback_date(date: dt) -> str:
    return date.strftime('%Y%m%d')

def get_wayback_urls(url, from_date, to_date=None):
    to_date = to_date or dt.now(UTC)
    urls = []
    results = cdx_search(url, from_date, to_date)
    for result in results:
        urls.append(f"https://web.archive.org/web/{result.timestamp}id_/{result.original_url}")
    urls.append(url)
    return urls