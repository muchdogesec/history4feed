

import os
import time
from types import SimpleNamespace
import unittest, pytest
from urllib.parse import urljoin

from tests.utils import remove_unknown_keys, wait_for_jobs

base_url = os.environ["SERVICE_BASE_URL"]
import requests

@pytest.mark.parametrize(
    ["feed_id", "should_fail"],
    [
        ["c2fe0594-f463-5362-afe7-6950bda94bc6", True], #feed does not exist
        ["9c04d319-a949-52df-bcb6-5a73a1458fe5", False],
        ["9c04d319-a949-52df-bcb6-5a73a1458fe5", True], #feed already deleted
    ]
)
def test_delete_feed(feed_id, should_fail):
    feed_url = urljoin(base_url, f"api/v1/feeds/{feed_id}/")
    delete_resp = requests.delete(feed_url)

    if should_fail:
        assert delete_resp.status_code == 404, f"delete feed request expected to fail: {delete_resp.text}"
        return
    assert delete_resp.status_code == 204, f"unexpected status, body: {delete_resp.text}"


    get_resp = requests.get(feed_url)
    assert get_resp.status_code == 404, f"feed should already be deleted"
