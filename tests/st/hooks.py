import json
import schemathesis, schemathesis.schemas
from schemathesis.specs.openapi.schemas import BaseOpenAPISchema
from schemathesis import Case
from schemathesis.transports.responses import GenericResponse

@schemathesis.hook
def after_load_schema(
    context: schemathesis.hooks.HookContext,
    schema: BaseOpenAPISchema,
) -> None:
    
    schema.add_link(
        source=schema["/api/v1/jobs/"]['GET'],
        target=schema["/api/v1/jobs/{job_id}/"]['GET'],
        status_code=200,
        parameters={"path.job_id": '$response.body#/jobs/0/id'}
    )
    for method in ['GET', 'PATCH', 'DELETE']:
        schema.add_link(
            source=schema['/api/v1/feeds/']['GET'],
            target=schema['/api/v1/feeds/{feed_id}/'][method],
            status_code=200,
            parameters={"path.feed_id": "$response.body#/feeds/0/id"}
        )

    for method in ['GET', 'PATCH', 'DELETE']:
        schema.add_link(
            source=schema['/api/v1/posts/']['GET'],
            target=schema['/api/v1/posts/{post_id}/'][method],
            status_code=200,
            parameters={"path.post_id": "$response.body#/posts/0/id"}
        )