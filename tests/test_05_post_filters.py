import os
import random
import time
from types import SimpleNamespace
import unittest, pytest
from urllib.parse import urljoin

from tests.utils import get_post_ids_for_job, is_sorted, remove_unknown_keys, wait_for_jobs

base_url = os.environ["SERVICE_BASE_URL"]
import requests


@pytest.mark.parametrize(
    ["filters", "expected_ids"],
    [
        [
            dict(feed_id="d1d96b71-c687-50db-9d2b-d0092d1d163a"),
            [
                "f8c75694-a834-5e35-b0a3-52034a1d9f6d",
                "85a762c9-00f9-5c0c-9858-498883e13ea1",
                "29be2407-d5d1-5b47-bbb5-1c51a84d48eb",
                "84a8ff1c-c463-5a97-b0c4-93daf7102b5f",
                "cfdb68b8-3d80-572d-9350-58baf57eabfb",
                "8f16d2be-7b06-5f3c-a851-9cce31b4fec8",
            ],
        ],  # feed does not exist
        [
            dict(link="test2/2024/08/07"),
            [
                "afef9ebd-2dee-5ab9-be0b-96c2ad83a1bb",
                "48310096-d1f3-5e30-9910-5d7d0fd400be",
                "d8aa9854-43fc-5816-b7ef-fc93810b29a5",
                "f8c75694-a834-5e35-b0a3-52034a1d9f6d",
            ],
        ],
        [
            dict(title="uPdATe this Post"),
            [
                "58514345-4e10-54c9-8f2c-d81507088079",
                "8c72f15c-abeb-5c90-b239-6429f53696f9",
                "8f16d2be-7b06-5f3c-a851-9cce31b4fec8",
                "f214c1fd-5370-5dff-bd49-fd74bf32c7fe",
            ],
        ],
        [
            dict(title="example org"),
            [
                "a378c839-0940-56fb-b52c-e5b78d34ec94",
            ],
        ],
        [
            dict(description="example domain"),
            [
                "223565cd-dd4f-54c2-9bbd-63019f39554f",
                "a378c839-0940-56fb-b52c-e5b78d34ec94",
            ],
        ],
    ],
)
def test_filters_generic(filters: dict, expected_ids: list[str]):
    expected_ids = set(expected_ids)
    url = urljoin(base_url, "api/v1/posts/")
    resp = requests.get(url, params=filters)
    resp_data = resp.json()
    assert resp_data["total_results_count"] == len(expected_ids)
    assert {post["id"] for post in resp_data["posts"]} == expected_ids


def random_posts_values(key, count):
    url = urljoin(base_url, "api/v1/posts/")
    resp = requests.get(url)
    data = resp.json()
    return [post[key] for post in random.choices(data["posts"], k=count)]


def more_pubdate_filters(count):
    filters = []
    pubdates = random_posts_values("pubdate", 50)
    for i in range(count):
        mmin = mmax = None
        if random.random() > 0.7:
            mmax = random.choice(pubdates)
        if random.random() < 0.3:
            mmin = random.choice(pubdates)
        if mmin or mmax:
            filters.append([mmin, mmax])
    return filters


@pytest.mark.parametrize(
    ["pubdate_min", "pubdate_max"],
    [
        ["2024-03-22T16:11:03Z", "2024-08-11T16:12:03Z"],
        ["2025-03-22T16:11:03Z", "2024-08-11T16:12:03Z"],
    ],
)
def test_pubdate_minmax(pubdate_min, pubdate_max):
    filters = {}
    if pubdate_min:
        filters.update(pubdate_min=pubdate_min)
    if pubdate_max:
        filters.update(pubdate_max=pubdate_max)

    assert pubdate_max or pubdate_min, "at least one of two filters required"

    url = urljoin(base_url, "api/v1/posts/")
    resp = requests.get(url, params=filters)
    assert resp.status_code == 200
    resp_data = resp.json()
    for d in resp_data["posts"]:
        if pubdate_min:
            assert (
                d["pubdate"] >= pubdate_min
            ), "pubdate must not be less than pubdate_min"
        if pubdate_max:
            assert (
                d["pubdate"] <= pubdate_max
            ), "pubdate must not be greater than pubdate_max"


@pytest.mark.parametrize(
    "updated_after", ["2024-03-22T16:11:03Z", "2030-03-22T16:11:03Z"]
)
def test_updated_after(updated_after):
    assert updated_after, "value cannot be None"

    url = urljoin(base_url, "api/v1/posts/")
    resp = requests.get(url, params=dict(pubdate_min=updated_after))
    assert resp.status_code == 200
    resp_data = resp.json()
    for d in resp_data["posts"]:
        assert (
            d["datetime_updated"] >= updated_after
        ), "datetime_updated must not be greater than updated_after"


def test_extra_updated_after(subtests):
    for datetime_updated in random_posts_values("datetime_updated", 12):
        with subtests.test(
            "randomly_generated updated_after query", updated_after=datetime_updated
        ):
            test_updated_after(datetime_updated)


def test_extra_pubdate_filters(subtests):
    for dmin, dmax in more_pubdate_filters(22):
        with subtests.test(
            "randomly_generated pubdate_* query", pubdate_min=dmin, pubdate_max=dmax
        ):
            test_pubdate_minmax(dmin, dmax)


def test_job_filter(subtests):
    def test_job_id_filter(job_id, post_ids):
        url = urljoin(base_url, "api/v1/posts/")
        resp = requests.get(url, params=dict(job_id=job_id))
        data = resp.json()
        for post in data["posts"]:
            assert post['id'] in post_ids, "post does not belong to job"
        assert data['total_results_count'] == len(post_ids)

    jobs_resp = requests.get(urljoin(base_url, "api/v1/jobs/"))
    for job in jobs_resp.json()['jobs']:
        with subtests.test("test_job_id_filter", job_id=job['id']):
            test_job_id_filter(job['id'], [x[0] for x in get_post_ids_for_job(job)])


@pytest.mark.parametrize(
        ["sort_filter", "expected_sort"],
        [
        ("", "pubdate_descending"), #default filter
        ("pubdate_descending", "pubdate_descending"),
        ("pubdate_ascending", "pubdate_ascending"),
        ("title_descending", "title_descending"),
        ("title_ascending", "title_ascending"),
        ("datetime_updated_descending", "datetime_updated_descending"),
        ("datetime_updated_ascending", "datetime_updated_ascending"),
        ("datetime_added_descending", "datetime_added_descending"),
        ("datetime_added_ascending", "datetime_added_ascending"),
    ]
)
def test_list_posts_sort(sort_filter: str, expected_sort: str):
    reports_url = urljoin(base_url, f"api/v1/posts/")
    filters = dict(sort=sort_filter) if sort_filter else None
    get_resp = requests.get(reports_url, params=filters)
    assert get_resp.status_code == 200, f"response: {get_resp.text}"
    posts = get_resp.json()["posts"]
    property, _, direction = expected_sort.rpartition('_')
    def sort_fn(obj):
        retval = obj[property]
        print(retval)
        return retval
    assert is_sorted(posts, key=sort_fn, reverse=direction == 'descending'), f"expected posts to be sorted by {property} in {direction} order"
