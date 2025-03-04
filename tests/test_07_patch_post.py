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
        ["post_id", "metadata"],
        [
            ["58514345-4e10-54c9-8f2c-d81507088079", dict(title="updated post title")],
            ["a378c839-0940-56fb-b52c-e5b78d34ec94", dict(title="updated title", author="new post author")],
            ["58514345-4e10-54c9-8f2c-d81507088079", dict(pubdate="2009-03-04T14:56:07Z")],
        ]
)
def test_update_post_metadata(post_id, metadata):
    resp = requests.patch(urljoin(base_url, f"api/v1/posts/{post_id}/"), json=metadata)
    assert resp.status_code == 201
    resp_data = resp.json()

    if expected_pretty_url := metadata.get("pretty_url"):
        assert resp_data["pretty_url"] == expected_pretty_url

    if expected_categories := metadata.get("categories"):
        assert resp_data["categories"] == expected_categories

    if expected_author := metadata.get("author"):
        assert resp_data["author"] == expected_author

    
    if expected_pubdate := metadata.get("pubdate"):
        assert resp_data["pubdate"] == expected_pubdate