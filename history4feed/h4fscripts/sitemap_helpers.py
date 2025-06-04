import json
import logging
import os
import time
from collections import namedtuple
from urllib.parse import urlencode
from .h4f import FatalError, PostDict, fetch_page_with_retries
from history4feed.app.settings import history4feed_server_settings as settings
import requests
from datetime import UTC, datetime as dt
import time
import requests
from datetime import datetime as dt, date, timedelta
from dateparser import parse as parse_date
DEFAULT_USER_AGENT = "curl"

class SearchIndexError(FatalError):
    pass

def fetch_posts_links_with_serper(site, from_time: dt, to_time: dt = None, delta_days=100) -> dict[str, PostDict]:
    s = requests.Session()
    s.headers.update({
        'X-API-KEY':  os.getenv("SERPER_API_KEY"),
        'Content-Type': 'application/json'
    })

    params = dict(num=100, page=1)
    entries: dict[str, PostDict] = {}
    to_time = to_time or dt.now(UTC)
    if not to_time.tzinfo:
        to_time = to_time.replace(tzinfo=UTC)

    frame_start = from_time - timedelta(days=1)
    credits_used = 0

    while frame_start < to_time:
        frame_end = frame_start + timedelta(days=delta_days)
        params.update(q=f"site:{site} after:{frame_start.date().isoformat()} before:{frame_end.date().isoformat()}", page=1)
        while True:
            resp = s.get("https://google.serper.dev/search", params=params)
            if not resp.ok:
                raise SearchIndexError(f"Serper Request GOT {resp.status_code}: {resp.text}")
            data = resp.json()
            credits_used += data['credits']
            for d in data['organic']:
                date = d.get('date')
                if date:
                    date = parse_date(date)
                else:
                    date = min(frame_end, to_time)
                post = PostDict(link=d['link'], title=d['title'], pubdate=date, categories=[])
                entries[post.link] = post
            params['page'] += 1
            if len(data['organic']) < params['num']:
                break
        frame_start = frame_end - timedelta(days=1)
    logging.info(f"got {len(entries)} posts between {from_time} and {to_time}, used {credits_used} credits")
    return entries

