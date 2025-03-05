

import os
import time
from types import SimpleNamespace
import unittest, pytest
from urllib.parse import urljoin

from tests.utils import remove_unknown_keys, wait_for_jobs

base_url = os.environ["SERVICE_BASE_URL"]
import requests

@pytest.mark.parametrize(
    ["post_id", "should_fail"],
    [
        ["9c04d319-a949-52df-bcb6-5a73a1458fe5", True], #post does not exist
        ["4aa844cb-18e6-58cc-bed1-4c22abf3b977", False],
        ["4aa844cb-18e6-58cc-bed1-4c22abf3b977", True], #post already deleted
    ]
)
def test_delete_post(post_id, should_fail):
    post_url = urljoin(base_url, f"api/v1/posts/{post_id}/")
    delete_resp = requests.delete(post_url)

    if should_fail:
        assert delete_resp.status_code == 404, f"delete post request expected to fail: {delete_resp.text}"
        return
    assert delete_resp.status_code == 204, f"unexpected status, body: {delete_resp.text}"


    get_resp = requests.get(post_url)
    assert get_resp.status_code == 404, f"post should already be deleted"
