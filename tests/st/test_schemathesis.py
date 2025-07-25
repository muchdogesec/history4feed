import time
from unittest.mock import patch
from urllib.parse import urlencode
import uuid
import schemathesis
import pytest
from schemathesis.core.transport import Response as SchemathesisResponse
from history4feed.app.models import Job
from history4feed.wsgi import application as wsgi_app
from rest_framework.response import Response as DRFResponse
from hypothesis import settings
from hypothesis import strategies
from schemathesis.specs.openapi.checks import (
    negative_data_rejection,
    positive_data_acceptance,
)
from schemathesis.config import GenerationConfig

from tests.utils import Transport

schema = schemathesis.openapi.from_wsgi("/api/schema/?format=json", wsgi_app)
schema.config.base_url = "http://localhost:8002/"
schema.config.generation = GenerationConfig(allow_x00=False)

feed_ids = strategies.sampled_from(
    [uuid.uuid4() for _ in range(3)]
    + ["6ca6ce37-1c69-4a81-8490-89c91b57e557", "0dfccb58-158c-4436-b338-163e3662943c"]
)
post_ids = strategies.sampled_from(
    [uuid.uuid4() for _ in range(3)] + ["561ed102-7584-4b7d-a302-43d4bca5605b"]
)
job_ids = strategies.sampled_from(
    [uuid.uuid4() for _ in range(3)]
    + ["e9794a6c-388e-4bd5-bf29-6bc01aebb8bb", "8ff3672d-067b-40af-9065-e801061f5593"]
)

@pytest.fixture(autouse=True)
def override_transport(monkeypatch, client):
    ## patch transport.get
    from schemathesis import transport
    monkeypatch.setattr(transport, "get", lambda _: Transport())



@pytest.fixture(autouse=True)
def module_setup(feed_posts, jobs):
    from history4feed.h4fscripts.celery import app
    app.conf.task_always_eager = False
    yield



@pytest.mark.django_db(transaction=True)
@schema.given(
    post_id=post_ids, feed_id=feed_ids, job_id=job_ids
)
@schema.exclude(method=["POST", "PATCH"]).parametrize()
@settings(max_examples=30)
def test_api(case: schemathesis.Case, **kwargs):
    for k, v in kwargs.items():
        if k in case.path_parameters:
            case.path_parameters[k] = v
    case.call_and_validate(
        excluded_checks=[negative_data_rejection, positive_data_acceptance]
    )


@pytest.mark.django_db(transaction=True)
@schema.given(
    post_id=post_ids, feed_id=feed_ids, job_id=job_ids
)
@schema.include(method=["POST", "PATCH"]).exclude(path="/api/v1/feeds/").parametrize()
@patch("celery.app.task.Task.run")
def test_imports(mock, case: schemathesis.Case, **kwargs):
    for k, v in kwargs.items():
        if k in case.path_parameters:
            case.path_parameters[k] = v
    with patch('history4feed.h4fscripts.h4f.parse_feed_from_url') as mock_parse_feed:
        case.call_and_validate(
            excluded_checks=[negative_data_rejection, positive_data_acceptance]
        )
        


@pytest.mark.django_db(transaction=True)
@schema.given(
    feed_id=feed_ids,
    url=strategies.sampled_from([
        "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-cdata-partial.xml",
        "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-cdata.xml",
        "https://blog.eclecticiq.com/rss.xml",
        #bad feeds
        "http://example.com/",
        "http://google.com/",
    ])
)
@schema.include(method="POST", path="/api/v1/feeds/").parametrize()
@patch('celery.app.task.Task.run')
def test_create_feed(mock, case: schemathesis.Case, url, **kwargs):
    for k, v in kwargs.items():
        if k in case.path_parameters:
            case.path_parameters[k] = v
    if isinstance(case.body, dict) and 'url' in case.body:
        case.body['url'] = url
    case.call_and_validate(excluded_checks=[negative_data_rejection, positive_data_acceptance])

