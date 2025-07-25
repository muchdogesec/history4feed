import json
import time
from urllib.parse import urlencode
import requests
import schemathesis
from schemathesis.core.transport import Response as SchemathesisResponse
from rest_framework.response import Response as DRFResponse
from django.core.handlers.wsgi import WSGIRequest

from schemathesis.transport.wsgi import (
    WSGI_TRANSPORT,
    WSGITransport,
    REQUESTS_TRANSPORT,
)


class Transport(WSGITransport):
    def __init__(self):
        super().__init__()
        self._copy_serializers_from(WSGI_TRANSPORT)

    @staticmethod
    def case_as_request(case):
        if isinstance(case, schemathesis.Case):
            r_dict = REQUESTS_TRANSPORT.serialize_case(
                case,
                base_url=case.operation.base_url,
            )
            return requests.Request(**r_dict).prepare()
        if isinstance(case, WSGIRequest):
            return requests.Request(
                method=case.method,
                url=case.build_absolute_uri(),
                headers=case.headers,
                data=case.POST,
                files=case.FILES,
                cookies=case.COOKIES,
                params=case.GET,
            ).prepare()

        return case

    def send(self, case: schemathesis.Case, *args, **kwargs):
        t = time.time()
        case.headers.pop("Authorization", "")
        serialized_request = WSGI_TRANSPORT.serialize_case(case)
        serialized_request.update(
            QUERY_STRING=urlencode(serialized_request["query_string"]),
        )
        if json_data := serialized_request.pop("json", None):
            serialized_request.update(data=json.dumps(json_data))
        import django.test

        client = django.test.Client()
        response: DRFResponse = client.generic(**serialized_request)
        elapsed = time.time() - t
        return self.get_st_response(response, case, elapsed)

    @classmethod
    def get_st_response(self, response: DRFResponse, case=None, elapsed=1):
        if not case:
            case = response.wsgi_request
        return SchemathesisResponse(
            response.status_code,
            headers={k: [v] for k, v in response.headers.items()},
            content=response.content,
            request=self.case_as_request(case),
            elapsed=elapsed,
            verify=True,
        )
