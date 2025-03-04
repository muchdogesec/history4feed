import os
import time
from types import SimpleNamespace
import unittest, pytest
from urllib.parse import urljoin

from tests.utils import remove_unknown_keys, wait_for_jobs

base_url = os.environ["SERVICE_BASE_URL"]
import requests

def all_posts():
    DATA = [
        {
            "feed_id": "d63dad15-8e23-57eb-80f7-715cedf85f33",
            "title": "Example COM",
            "id": "223565cd-dd4f-54c2-9bbd-63019f39554f",
            "link": "https://example.com/",
            "pubdate": "2024-08-11T16:12:03Z",
            "author": "test",
            "categories": [
                "test",
                "test2"
            ]
        },
        {
            "feed_id": "d63dad15-8e23-57eb-80f7-715cedf85f33",
            "title": "Example ORG",
            "id": "a378c839-0940-56fb-b52c-e5b78d34ec94",
            "link": "https://example.org/",
            "pubdate": "2024-03-22T16:11:03Z",
            "author": "test",
            "categories": [
                "test",
                "test2"
            ]
        },
        {
            "feed_id": "d63dad15-8e23-57eb-80f7-715cedf85f33",
            "title": "Example COM under real",
            "id": "223565cd-dd4f-54c2-9bbd-63019f39554f",
            "link": "https://example.com/",
            "pubdate": "2024-08-11T16:12:03Z",
            "author": "test",
            "categories": [
                "test",
                "test2"
            ],
            "should_fail": True, #already added
        },
        {
            "feed_id": "d63dad15-8e23-57eb-80f7-715cedf85f33",
            "title": "Example ORG under real",
            "id": "a378c839-0940-56fb-b52c-e5b78d34ec94",
            "link": "https://example.org/",
            "pubdate": "2024-03-22T16:11:03Z",
            "author": "test",
            "categories": [
                "test",
                "test2"
            ],
            "should_fail": True, #already added
        },
    ]
    return [
        [d["feed_id"], d["link"], d, d.get("should_fail")]
            for d in DATA
    ]

@pytest.mark.parametrize(
    ["feed_id", "post_url", "post_data", "should_fail"],
    all_posts()
)
def test_add_post(feed_id, post_url, post_data, should_fail):
    payload = remove_unknown_keys(post_data, ["link", "title", "pubdate", "author", "categories"])
    post_job_resp = requests.post(urljoin(base_url, f"api/v1/feeds/{feed_id}/posts/"), json=dict(posts=[payload]))

    if should_fail:
        assert post_job_resp.status_code == 400, "add feed request expected to fail"
        return
    
    assert post_job_resp.status_code == 201, f"request failed: {post_job_resp.text}"
    post_job_resp_data = post_job_resp.json()
    assert post_job_resp_data["feed_id"] == feed_id, "wrong feed id"
    assert len(post_job_resp_data["urls"]["retrieving"]) == 1, "one post expected"
    post_id = post_job_resp_data["urls"]["retrieving"][0]["id"]
    expected_id = post_data["id"]
    assert post_id == expected_id
    job_id = post_job_resp_data['id']

    job_data = wait_for_jobs(job_id)
    post_data_resp = requests.get(urljoin(base_url, f"api/v1/posts/{post_id}/"))
    post_data_resp_data = post_data_resp.json()
    assert post_data_resp_data["title"] == post_data["title"]
    assert post_data_resp_data["pubdate"] == post_data["pubdate"]
    assert set(post_data_resp_data["categories"]) == set(post_data.get("categories", []))
