from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OpenApiTypes


FEED_ID_PARAM = OpenApiParameter("feed_id", type=OpenApiTypes.UUID, description="The ID of the Feed. You can search for Feed IDs using the GET Feeds endpoints.", location=OpenApiParameter.PATH)
JOB_ID_PARAM  = OpenApiParameter("job_id", type=OpenApiTypes.UUID, description="The ID of the Job. You can search for Job IDs using the GET Jobs endpoints.", location=OpenApiParameter.PATH)
POST_ID_PARAM = OpenApiParameter("post_id", type=OpenApiTypes.UUID, description="The ID of the Post. You can search for Post IDs using the GET Posts endpoints for a specific Feed.", location=OpenApiParameter.PATH)
