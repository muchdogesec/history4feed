import os
import time
from types import SimpleNamespace
import unittest, pytest
from urllib.parse import urljoin

base_url = os.environ["SERVICE_BASE_URL"]
import requests


def get_all_feeds():
    if not os.getenv('DELETE_ALL_FEEDS'):
        return []
    resp = requests.get(urljoin(base_url, "api/v1/feeds/"))
    return [[feed["id"]] for feed in resp.json()["feeds"]]

@pytest.mark.parametrize(
        ["feed_id"],
        get_all_feeds(),
)
def test_delete_blog(feed_id):
    resp = requests.delete(urljoin(base_url, f"api/v1/feeds/{feed_id}/"))
    assert resp.status_code == 204, "unexpected status code"
    resp = requests.get(urljoin(base_url, f"api/v1/feeds/{feed_id}/"))
    assert resp.status_code == 404, "feed should not exist after deletion"
