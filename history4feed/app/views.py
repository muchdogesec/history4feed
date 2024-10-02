from django.shortcuts import get_object_or_404

from .autoschema import H4FSchema

from .openapi_params import (
    HTTP400_EXAMPLE,
    HTTP404_EXAMPLE,
    JOB_ID_PARAM,
    FEED_ID_PARAM,
    POST_ID_PARAM,
    XML_RESPONSE,
)
from .utils import (
    H4FOrdering,
    H4FPagination,
    MinMaxDateFilter,
    RSSRenderer,
    XMLPostPagination,
)

# from .openapi_params import FEED_PARAMS, POST_PARAMS

from .serializers import FeedCreateSerializer, H4FError, PatchSerializer, PostPatchRespSerializer, PostSerializer, FeedSerializer, JobSerializer
from .models import FulltextJob, Post, Feed, Job
from rest_framework import (
    viewsets,
    request,
    response,
    mixins,
    decorators,
    renderers,
    pagination,
    status,
)
from django.http import HttpResponse
from ..h4fscripts import h4f, task_helper, build_rss
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    Filter,
    BaseCSVFilter,
    UUIDFilter,
)
from django.db.models import Count, Q, Subquery, OuterRef
from datetime import datetime
import textwrap


class Response(response.Response):
    DEFAULT_HEADERS = {
        "Access-Control-Allow-Origin": "*",
    }
    CONTENT_TYPE = "application/json"

    def __init__(
        self,
        data=None,
        status=None,
        template_name=None,
        headers=None,
        exception=False,
        content_type=CONTENT_TYPE,
    ):
        headers = headers or {}
        headers.update(self.DEFAULT_HEADERS)
        super().__init__(data, status, template_name, headers, exception, content_type)


class ErrorResp(Response):
    def __init__(self, status, title, details=None):
        super().__init__({"detail": title, "code": status}, status=status)


# Create your views here.
@extend_schema_view(
    partial_update=extend_schema(
        description=textwrap.dedent(
            """
            Occasionally updates to blog posts are not reflected in RSS and ATOM feeds. To ensure the post stored in history4feed matches the currently published post you make a request to this endpoint using the Post ID to update it.\n\n
            `profile_id` is an optional field that can be passed in the request body and accepts a UUIDv4. You should not pass it. We (DOGESEC) use this property for integration with Obstracts.\n\n
            The response will return the Job information responsible for getting the requested data you can track using the `id` returned via the GET Jobs by ID endpoint.
            """
        ),
        summary="Update a Post in a Feed",
        responses={
            201: PostPatchRespSerializer,
            404: OpenApiResponse(H4FError, "Feed or post does not exist", examples=[HTTP404_EXAMPLE]),
        },
        tags=["Feeds"],
        request=PatchSerializer,
    ),
)
class PostView(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):

    open_api_tags = ["Feeds"]
    serializer_class = PostSerializer
    lookup_url_kwarg = "post_id"
    pagination_class = H4FPagination("posts")
    filter_backends = [DjangoFilterBackend, H4FOrdering, MinMaxDateFilter]
    ordering_fields = ["pubdate", "title"]
    ordering = ["-pubdate"]
    minmax_date_fields = ["pubdate"]

    class filterset_class(FilterSet):
        title = Filter(
            label="Filter by the content in a posts title. Will search for titles that contain the value entered.",
            lookup_expr="search",
        )
        description = Filter(
            label="Filter by the content in a posts description. Will search for descriptions that contain the value entered.",
            lookup_expr="search",
        )
        job_id = Filter(label="Filter the Post by Job ID the Post was downloaded in.", field_name="fulltext_jobs__job_id")

    def get_queryset(self):
        subquery = FulltextJob.objects.filter(post_id=OuterRef('pk')).order_by('-job__run_datetime').values('job__profile_id')[:1]
        return Post.objects.filter(feed_id=self.kwargs.get("feed_id")).annotate(profile_id=Subquery(subquery))

    @extend_schema(
        parameters=[FEED_ID_PARAM],
        filters=True,
        summary="Search for Posts in a Feed (RSS)",
        description=textwrap.dedent(
            """
        Use this endpoint with your feed reader. The response of this endpoint is valid RSS XML for the Posts in the Feed. If you want more flexibility (perhaps to build a custom integration) use the JSON version of this endpoint.
        """
        ),
        tags=open_api_tags,
        responses={
            200: XML_RESPONSE,
            (404, "application/json"): OpenApiResponse(H4FError, "Feed not found", examples=[HTTP404_EXAMPLE]),
            (400, "application/json"): OpenApiResponse(H4FError, "Request not understood", examples=[HTTP400_EXAMPLE]),
        },
    )
    @decorators.action(
        methods=["get"],
        detail=False,
        pagination_class=XMLPostPagination("xml_posts"),
        renderer_classes=[RSSRenderer],
    )
    def xml(self, request: request.Request, *args, feed_id=None, **kwargs):
        feed_obj = get_object_or_404(Feed, id=feed_id)
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        body = build_rss.build_rss(feed_obj, page)
        return self.paginator.get_paginated_response(body)

    @extend_schema(
        parameters=[FEED_ID_PARAM],
        summary="Search for Posts in a Feed (JSON)",
        description=textwrap.dedent(
            """
        Use this endpoint if you want to search through all Posts in a Feed. The response of this endpoint is JSON, and is useful if you're building a custom integration to a downstream tool. If you just want to import the data for this blog into your feed reader use the RSS version of this endpoint.
        """
        ),
        tags=open_api_tags,
        responses={
            200: PostSerializer,
            404: OpenApiResponse(H4FError, "Feed not found", examples=[HTTP404_EXAMPLE]),
            400: OpenApiResponse(H4FError, "Request not understood", examples=[HTTP400_EXAMPLE]),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[FEED_ID_PARAM, POST_ID_PARAM],
        summary="Get a Post in a Feed",
        description=textwrap.dedent(
            """
        This will return a single Post in a Feed using its ID. It is useful if you only want to get the data for a single entry.
        """
        ),
        tags=open_api_tags,
        responses={
            200: PostSerializer,
            404: OpenApiResponse(H4FError, "Feed or post not found", examples=[HTTP404_EXAMPLE]),
            400: OpenApiResponse(H4FError, "Request not understood", examples=[HTTP400_EXAMPLE]),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    

    def partial_update(self, request, *args, **kwargs):
        s = PatchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        post: Post = self.get_object()
        job_obj = task_helper.new_patch_posts_job(post.feed, [post], s.data['profile_id'])
        job_resp = JobSerializer(job_obj).data.copy()
        job_resp.update(post_id=post.id)
        return Response(job_resp, status=status.HTTP_201_CREATED)


class FeedView(viewsets.ModelViewSet):
    open_api_tags = ["Feeds"]
    serializer_class = FeedSerializer
    queryset = Feed.objects.all()
    lookup_url_kwarg = "feed_id"
    pagination_class = H4FPagination("feeds")
    http_method_names = ["get", "post", "patch", "delete"]

    filter_backends = [DjangoFilterBackend, H4FOrdering, MinMaxDateFilter]
    ordering_fields = [
        "datetime_added",
        "title",
        "url",
        "count_of_posts",
        "earliest_item_pubdate",
        "latest_item_pubdate",
    ]
    ordering = ["-datetime_added"]
    minmax_date_fields = ["earliest_item_pubdate", "latest_item_pubdate"]

    class filterset_class(FilterSet):
        title = Filter(
            label="Filter by the content in feed title. Will search for titles that contain the value entered.",
            lookup_expr="search",
        )
        description = Filter(
            label="Filter by the content in feed description. Will search for descriptions that contain the value entered.",
            lookup_expr="search",
        )
        url = Filter(
            label="Filter by the content in a feeds URL. Will search for URLs that contain the value entered.",
            lookup_expr="icontains",
        )
        id = BaseCSVFilter(
            label="Filter by feed id(s), comma-separated, e.g 6c6e6448-04d4-42a3-9214-4f0f7d02694e,2bce5b30-7014-4a5d-ade7-12913fe6ac36",
            lookup_expr="in",
        )

    def get_queryset(self):
        return Feed.objects.all().annotate(count_of_posts=Count("posts"))

    @extend_schema(
        summary="Create a new Feed",
        description=textwrap.dedent(
            """
        Use this endpoint to create to a new feed. The `url` value used should be a valid RSS or ATOM feed URL. If it is not valid, the Feed will not be created and an error returned.\n\n
        If the  `url` is already associated with an existing Feed, using it via this endpoint will trigger an update request for the blog. If you want to add the `url` with new settings, first delete the feed it is associated with.\n\n
        `include_remote_blogs` is a boolean setting. Some feeds include remote posts from other sites (e.g. for a paid promotion). This setting (set to `false` allows you to ignore remote posts that do not use the same domain as the `url` used). Generally you should set `include_remote_blogs` to `false`.\n\n
        `profile_id` is an optional field that can be passed in the request body and accepts a UUIDv4. You should not pass it. We (DOGESEC) use this property for integration with Obstracts.\n\n
        The response will return the Job information responsible for getting the requested data you can track using the `id` returned via the GET Jobs by ID endpoint.
        """
        ),
        tags=open_api_tags,
        responses={
            201: FeedCreateSerializer,
            400: OpenApiResponse(H4FError, "Bad request", examples=[HTTP400_EXAMPLE]),
            406: OpenApiResponse(H4FError, "Invalid feed url", examples=[OpenApiExample(name="http-406", value={"detail": "invalid feed url", "code": 406})]),
        },
    )
    def create(self, request: request.Request, **kwargs):
        s = self.serializer_class(data=request.data)
        s.is_valid(raise_exception=True)
        profile_id = request.data.get('profile_id')
        try:
            feed = h4f.parse_feed_from_url(s.data["url"])
        except Exception as e:
            return ErrorResp(406, "Invalid feed url", details={"error": str(e)})
        s.run_validation({**feed, 'profile_id': profile_id})
        feed_obj: Feed = s.create(validated_data=feed)
        job_obj = task_helper.new_job(feed_obj, profile_id)

        feed = self.serializer_class(feed_obj).data.copy()
        feed.update(
            job_state=job_obj.state,
            job_id=job_obj.id,
        )
        return Response(feed, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[FEED_ID_PARAM],
        summary="Update a Feed",
        request=PatchSerializer,
        description=textwrap.dedent(
            """
        Use this endpoint to check for new posts on this blog since the last update time. An update request will immediately trigger a job to get the posts between `latest_item_pubdate` for feed and time you make a request to this endpoint.\n\n
        Note, this endpoint can miss updates to currently indexed posts (where the RSS or ATOM feed does not report the updated correctly -- which is very common). To solve this issue for currently indexed blog posts, use the Update Post endpoint.\n\n
        `profile_id` is an optional field that can be passed in the request body and accepts a UUIDv4. You should not pass it. We (DOGESEC) use this property for integration with Obstracts.\n\n
        The response will return the Job information responsible for getting the requested data you can track using the `id` returned via the GET Jobs by ID endpoint.
        """
        ),
        tags=open_api_tags,
        responses={
            201: FeedCreateSerializer,
            400: OpenApiResponse(H4FError, "Request not understood", examples=[HTTP400_EXAMPLE]),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        s = PatchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        feed_obj: Feed = self.get_object()
        job_obj = task_helper.new_job(feed_obj, s.data['profile_id'])
        feed = self.serializer_class(feed_obj).data.copy()

        feed.update(
            job_state=job_obj.state,
            job_id=job_obj.id,
        )
        return Response(feed, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Search for Feeds",
        description=textwrap.dedent(
            """
        Use this endpoint to get a list of all the feeds you are currently subscribed to. This endpoint is usually used to get the id of feed you want to get blog post data for in a follow up request to the GET Feed Posts endpoints or to get the status of a job related to the Feed in a follow up request to the GET Job endpoint. If you already know the id of the Feed already, you can use the GET Feeds by ID endpoint.
        """
        ),
        tags=open_api_tags,
        responses={
            200: FeedSerializer,
            400: OpenApiResponse(H4FError, "Request not understood", examples=[HTTP400_EXAMPLE]),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[FEED_ID_PARAM],
        summary="Get a Feed",
        description=textwrap.dedent(
            """
        Use this endpoint to get information about a specific feed using its ID. You can search for a Feed ID using the GET Feeds endpoint, if required.
        """
        ),
        tags=open_api_tags,
        responses={
            200: FeedSerializer,
            404: OpenApiResponse(H4FError, "Not found", examples=[HTTP404_EXAMPLE]),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        parameters=[FEED_ID_PARAM],
        summary="Delete a Feed",
        description=textwrap.dedent(
            """
        Use this endpoint to delete a feed using its ID. This will delete all posts (items) that belong to the feed and cannot be reversed.
        """
        ),
        tags=open_api_tags,
        responses={
            200: OpenApiTypes.NONE,
            404: OpenApiResponse(
                H4FError,
                "Not found",
                examples=[HTTP404_EXAMPLE],
            ),
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class JobView(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = JobSerializer
    pagination_class = H4FPagination("jobs")
    filter_backends = [DjangoFilterBackend, H4FOrdering]
    ordering_fields = ["run_datetime", "state"]
    ordering = ["-run_datetime"]
    open_api_tags = ["Jobs"]
    lookup_url_kwarg = "job_id"
    lookup_field = "id"

    class filterset_class(FilterSet):
        feed_id = Filter(
            label="Filter Jobs by the ID of the Feed they belong to. You can search for Feed IDs using the GET Feeds endpoints. Note a Feed can have multiple jobs associated with it where a PATCH request has been run to update the Feed."
        )
        state = Filter(label="Filter by the status of a Job")
        post_id = UUIDFilter(label="Filter Jobs by the ID of the Post they belong to. You can search for Post IDs using the GET Posts endpoint. Note a Post can have multiple jobs associated with it where a PATCH request has been run to update a Feed or a Post.", field_name="fulltext_jobs__post_id")

    def get_queryset(self):
        return Job.objects.all().annotate(count_of_items=Count("fulltext_jobs"))

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset)

    @extend_schema(
        summary="Search Jobs",
        description=textwrap.dedent(
            """
        Jobs track the status of the request to get posts for Feeds. For every new Feed added and every update to a Feed requested a job will be created. The `id` of a job is printed in the POST and PATCH responses respectively, but you can use this endpoint to search for the id again, if required.
        """
        ),
        tags=open_api_tags,
        responses={
            200: JobSerializer,
            400: OpenApiResponse(
                H4FError,
                "Request not understood",
                [HTTP400_EXAMPLE],
            ),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[JOB_ID_PARAM],
        summary="Get a Job",
        description=textwrap.dedent(
            """
        Using a Job ID you can retrieve information about its state via this endpoint. This is useful to see if a Job to get data is complete, how many posts were imported in the job, or if an error has occurred.
        """
        ),
        tags=open_api_tags,
        responses={
            200: JobSerializer,
            404: OpenApiResponse(
                H4FError,
                "Job not found",
                [HTTP404_EXAMPLE],
            ),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
