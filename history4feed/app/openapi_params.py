from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from textwrap import dedent
from .serializers import PostSerializer


FEED_ID_PARAM = OpenApiParameter(
    "feed_id",
    type=OpenApiTypes.UUID,
    description="The ID of the Feed. You can search for Feed IDs using the GET Feeds endpoints.",
    location=OpenApiParameter.PATH,
)
JOB_ID_PARAM = OpenApiParameter(
    "job_id",
    type=OpenApiTypes.UUID,
    description="The ID of the Job. You can search for Job IDs using the GET Jobs endpoints.",
    location=OpenApiParameter.PATH,
)
POST_ID_PARAM = OpenApiParameter(
    "post_id",
    type=OpenApiTypes.UUID,
    description="The ID of the Post. You can search for Post IDs using the GET Posts endpoints for a specific Feed.",
    location=OpenApiParameter.PATH,
)


XML_RESPONSE = OpenApiResponse(
    response=PostSerializer(many=True),
    description="",
    examples=[
        OpenApiExample(
            "xml",
            value=dedent(
                """
            <?xml version="1.0" ?>
            <rss version="2.0">
                <channel>
                <title>Example CTI Blog</title>
                <description>
                </description>
                <link>https://cti.example.com/feed/</link>
                <lastBuildDate>2024-07-02T17:07:31+00:00</lastBuildDate>
                <item>
                    <title>DNS Probing Operation</title>
                    <link href="https://cti.example.com/blog/dns-probing-operation/">https://cti.example.com/blog/dns-probing-operation/</link>
                    <pubDate>2024-06-03T15:00:52+00:00</pubDate>
                    <description>&lt;html&gt;&lt;/html&gt;</description>
                    <category>infoblox-threat-intel</category>
                    <category>dns</category>
                    <category>dns-intel</category>
                    <category>dns-threat-intelligence</category>
                    <category>malware</category>
                    <author>
                    <name>John Doe (Admin)</name>
                    </author>
                </item>
                </channel>
            </rss>
"""
            ),
        )
    ],
)

HTTP404_EXAMPLE = OpenApiExample("http-404", {"detail": "resource not found", "code": 404})
HTTP400_EXAMPLE = OpenApiExample("http-400", {"detail": "request not understood", "code": 400})