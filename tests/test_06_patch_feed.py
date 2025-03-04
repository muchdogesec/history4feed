from datetime import UTC, datetime
import os
import time
from types import SimpleNamespace
import unittest, pytest
from urllib.parse import urljoin
from dateutil.parser import parse as parse_date

from tests.utils import remove_unknown_keys, wait_for_jobs

base_url = os.environ["SERVICE_BASE_URL"]
import requests
@pytest.mark.parametrize(
        ["feed_id", "metadata"],
        [
            ["d1d96b71-c687-50db-9d2b-d0092d1d163a", dict(title="updated title")],
            ["d63dad15-8e23-57eb-80f7-715cedf85f33", dict(title="updated title", description="new description")],
            ["d1d96b71-c687-50db-9d2b-d0092d1d163a", dict(pretty_url="https://muchdogesec.github.io/fakeblog123/?added_later=true")],
        ]
)
def test_update_feed_metadata(feed_id, metadata):
    resp = requests.patch(urljoin(base_url, f"api/v1/feeds/{feed_id}/"), json=metadata)
    assert resp.status_code == 201
    resp_data = resp.json()

    if expected_pretty_url := metadata.get("pretty_url"):
        assert resp_data["pretty_url"] == expected_pretty_url

    if expected_title := metadata.get("title"):
        assert resp_data["title"] == expected_title

    if expected_description := metadata.get("description"):
        assert resp_data["description"] == expected_description

# def test_feed_reindex(feed_id):
#     start_time = datetime.now(UTC)
#     resp = requests.patch(urljoin(base_url, f"api/v1/feeds/{feed_id}/"))
#     assert resp.status_code == 201
#     resp_data = resp.json()
