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
    Ordering,
    Pagination,
    MinMaxDateFilter,
    RSSRenderer,
    XMLPostPagination,
)
from dogesec_commons.utils.serializers import CommonErrorSerializer
# from .openapi_params import FEED_PARAMS, POST_PARAMS

from .serializers import FeedCreatedJobSerializer, FeedFetchSerializer, FeedPatchSerializer, PostWithFeedIDSerializer, SkeletonFeedSerializer, PatchSerializer, PostJobSerializer, PostSerializer, FeedSerializer, JobSerializer, PostCreateSerializer
from .models import AUTO_TITLE_TRAIL, FulltextJob, Post, Feed, Job, FeedType
from rest_framework import (
    viewsets,
    request,
    response,
    mixins,
    decorators,
    renderers,
    pagination,
    status,
    validators,
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
    BaseInFilter,
    filters,
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
        super().__init__({"message": title, "code": status}, status=status)


# Create your views here.

@extend_schema_view(
    retrieve=extend_schema(
        summary="Get a Post",
        description=textwrap.dedent(
            """
            This will return a single Post by its ID. It is useful if you only want to get the data for a single entry.
            """
        ),
        responses={
            200: PostSerializer,
            404: OpenApiResponse(CommonErrorSerializer, "Post not found", examples=[HTTP404_EXAMPLE]),
            400: OpenApiResponse(CommonErrorSerializer, "Request not understood", examples=[HTTP400_EXAMPLE]),
        },
    ),
    list=extend_schema(
        summary="Search for Posts",
        description=textwrap.dedent(
            """
            Returns all Posts indexed. Filter by the ones you're interested in.
            """
        ),
        responses={
            200: PostSerializer,
            404: OpenApiResponse(CommonErrorSerializer, "Feed not found", examples=[HTTP404_EXAMPLE]),
            400: OpenApiResponse(CommonErrorSerializer, "Request not understood", examples=[HTTP400_EXAMPLE]),
        },
    )

)
class PostOnlyView(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    openapi_path_params = [POST_ID_PARAM]
    openapi_tags = ["Posts"]
    serializer_class = PostWithFeedIDSerializer
    lookup_url_kwarg = "post_id"
    pagination_class = Pagination("posts")
    filter_backends = [DjangoFilterBackend, Ordering, MinMaxDateFilter]
    ordering_fields = ["pubdate", "title"]
    ordering = ["-pubdate"]
    minmax_date_fields = ["pubdate"]

    class filterset_class(FilterSet):
        feed_id = filters.BaseInFilter(help_text="filter by one or more `feed_id`(s)")
        title = Filter(
            help_text="Filter the content by the `title` of the post. Will search for titles that contain the value entered. Search is wildcard so `exploit` will match `exploited` and `exploits`.",
            lookup_expr="icontains",
        )
        description = Filter(
            help_text="Filter by the content post `description`. Will search for descriptions that contain the value entered. Search is wildcard so `exploit` will match `exploited` and `exploits`.",
            lookup_expr="icontains",
        )
        link = Filter(
            help_text="Filter the content by a posts `link`. Will search for links that contain the value entered. Search is wildcard so `dogesec` will return any URL that contains the string `dogesec`.",
            lookup_expr="icontains",
        )
        job_id = Filter(help_text="Filter the Post by Job ID the Post was downloaded in.", field_name="fulltext_jobs__job_id")

    def get_queryset(self):
        return Post.visible_posts()


class FeedView(viewsets.ModelViewSet):
    openapi_tags = ["Feeds"]
    serializer_class = FeedSerializer
    queryset = Feed.objects.all()
    lookup_url_kwarg = "feed_id"
    pagination_class = Pagination("feeds")
    http_method_names = ["get", "post", "patch", "delete"]

    filter_backends = [DjangoFilterBackend, Ordering, MinMaxDateFilter]
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
            help_text="Filter by the content in feed title. Will search for titles that contain the value entered.",
            lookup_expr="icontains",
        )
        description = Filter(
            help_text="Filter by the content in feed description. Will search for descriptions that contain the value entered.",
            lookup_expr="icontains",
        )
        url = Filter(
            help_text="Filter by the content in a feeds URL. Will search for URLs that contain the value entered.",
            lookup_expr="icontains",
        )
        id = BaseCSVFilter(
            help_text="Filter by feed id(s), comma-separated, e.g `6c6e6448-04d4-42a3-9214-4f0f7d02694e,2bce5b30-7014-4a5d-ade7-12913fe6ac36`",
            lookup_expr="in",
        )
        feed_type = filters.MultipleChoiceFilter(
            help_text="Filter by `feed_type`",
            choices=FeedType.choices,
        )


    def get_queryset(self):
        return Feed.objects.all().annotate(count_of_posts=Count("posts"))

    @extend_schema(
        summary="Create a new Feed",
        description=textwrap.dedent(
            """
            Use this endpoint to create to a new feed.

            The following key/values are accepted in the body of the request:

            * `url` (required): a valid RSS or ATOM feed URL.  If it is not valid, the Feed will not be created and an error returned. You can use the skeleton endpoint to create a feed from a non RSS/ATOM URL.
            * `include_remote_blogs` (required): is a boolean setting and will ask history4feed to ignore any feeds not on the same domain as the URL of the feed. Some feeds include remote posts from other sites (e.g. for a paid promotion). This setting (set to `false` allows you to ignore remote posts that do not use the same domain as the `url` used). Generally you should set `include_remote_blogs` to `false`. The one exception is when things like feed aggregators (e.g. Feedburner) URLs are used, where the actual blog posts are not on the `feedburner.com` (or whatever) domain. In this case `include_remote_blogs` should be set to `true`.
            * `pretty_url` (optional): you can also include a secondary URL in the database. This is designed to be used to show the link to the blog (not the RSS/ATOM) feed so that a user can navigate to the blog in their browser.
            * `title` (optional): the title of the feed will be used if not passed. You can also manually pass the title of the blog here.
            * `description` (optional): the description of the feed will be used if not passed. You can also manually pass the description of the blog here.

            The `id` of a Feed is generated using a UUIDv5. The namespace used is `6c6e6448-04d4-42a3-9214-4f0f7d02694e` and the value used is `<FEED_URL>` (e.g. `https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-encoded.xml` would have the id `d1d96b71-c687-50db-9d2b-d0092d1d163a`). Therefore, you cannot add a URL that already exists, you must first delete it to add it with new settings.

            Each post ID is generated using a UUIDv5. The namespace used is `6c6e6448-04d4-42a3-9214-4f0f7d02694e` and the value used `<FEED_ID>+<POST_URL>+<POST_PUB_TIME (to .000000Z)>` (e.g. `d1d96b71-c687-50db-9d2b-d0092d1d163a+https://muchdogesec.github.io/fakeblog123///test3/2024/08/20/update-post.html+2024-08-20T10:00:00.000000Z` = `22173843-f008-5afa-a8fb-7fc7a4e3bfda`).

            The response will return the Job information responsible for getting the requested data you can track using the `id` returned via the GET Jobs by ID endpoint.
            """
        ),
        responses={
            201: FeedCreatedJobSerializer,
            400: OpenApiResponse(CommonErrorSerializer, "Bad request", examples=[HTTP400_EXAMPLE]),
            406: OpenApiResponse(CommonErrorSerializer, "Invalid feed url", examples=[OpenApiExample(name="http-406", value={"detail": "invalid feed url", "code": 406})]),
        },
        request=FeedSerializer,
    )
    def create(self, request: request.Request, **kwargs):

        s = FeedSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        try:
            feed_data = h4f.parse_feed_from_url(s.data["url"])
        except Exception as e:
            return ErrorResp(406, "Invalid feed url", details={"error": str(e)})

        for k in ['title', 'description']:
            if v := s.validated_data.get(k):
                feed_data[k] = v
            elif v := feed_data.get(k):
                feed_data[k] = v + AUTO_TITLE_TRAIL
        
        s = FeedSerializer(data={**s.data, **feed_data})
        s.is_valid(raise_exception=True)

        feed_obj: Feed = s.save(feed_type=feed_data['feed_type'])
        job_obj = task_helper.new_job(feed_obj, s.validated_data.get('include_remote_blogs', False))

        resp_data = self.serializer_class(feed_obj).data.copy()
        resp_data.update(
            job_state=job_obj.state,
            job_id=job_obj.id,
        )
        return Response(resp_data, status=status.HTTP_201_CREATED)


    @extend_schema(
        summary="Create a new Skeleton Feed",
        description=textwrap.dedent(
            """
            Sometimes blogs don't have an RSS or ATOM feed. It might also be the case you want to curate a blog manually using various URLs. This is what `skeleton` feeds are designed for, allowing you to create a skeleton feed and then add posts to it manually later on using the add post manually endpoint.

            The following key/values are accepted in the body of the request:

            * `url` (required): the URL to be attached to the feed. Needs to be a URL (because this is what feed ID is generated from), however does not need to be valid.
            * `pretty_url` (optional): you can also include a secondary URL in the database. This is designed to be used to show the link to the blog (not the RSS/ATOM) feed so that a user can navigate to the blog in their browser.
            * `title` (required): the title of the feed
            * `description` (optional): the description of the feed

            The response will return the created Feed object with the Feed `id`.
            """
        ),
        responses={
            201: SkeletonFeedSerializer,
            400: OpenApiResponse(CommonErrorSerializer, "Bad request", examples=[HTTP400_EXAMPLE]),
        },
        request=SkeletonFeedSerializer,
    )
    @decorators.action(methods=['POST'], detail=False)
    def skeleton(self, request: request.Request, **kwargs):
        s = SkeletonFeedSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        instance = s.save()
        return Response(FeedSerializer(instance).data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        parameters=[FEED_ID_PARAM],
        summary="Update a Feeds Metadata",
        request=FeedPatchSerializer,
        description=textwrap.dedent(
            """
            Update the metadata of the Feed. To leave a property unchanged from its current state do not pass it in the request.

            Note, it is not possible to update the `url` of the feed. You must delete the Feed and add it again to modify the `url`.

            The following key/values are accepted in the body of the request:

            * `title` (optional): update the `title` of the Feed
            * `description` (optional): update the `description` of the Feed
            * `pretty_url` (optional): update the `pretty_url of the Feed

            The response will contain the newly updated Feed object.
            """
        ),
        responses={
            201: FeedSerializer,
            400: OpenApiResponse(CommonErrorSerializer, "Request not understood", examples=[HTTP400_EXAMPLE]),
            (404, "application/json"): OpenApiResponse(CommonErrorSerializer, "Feed not found", examples=[HTTP404_EXAMPLE]),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        feed_obj: Feed = self.get_object()
        s = FeedPatchSerializer(feed_obj, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(self.serializer_class(feed_obj).data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        parameters=[FEED_ID_PARAM],
        summary="Fetch new Post for a Feed",
        request=FeedFetchSerializer,
        description=textwrap.dedent(
            """
            Use this endpoint to check for new posts on this blog since the last update time. An update request will immediately trigger a job to get the posts between `latest_item_pubdate` for feed and time you make a request to this endpoint.

            Note, this endpoint can miss updates to currently indexed posts (where the RSS or ATOM feed does not report the updated correctly -- which is very common). To solve this issue for currently indexed blog posts, use the Update Post endpoint.

            The following key/values are accepted in the body of the request:

             * `include_remote_blogs` (required): is a boolean setting and will ask history4feed to ignore any feeds not on the same domain as the URL of the feed. Some feeds include remote posts from other sites (e.g. for a paid promotion). This setting (set to `false` allows you to ignore remote posts that do not use the same domain as the `url` used). Generally you should set `include_remote_blogs` to `false`. The one exception is when things like feed aggregators (e.g. Feedburner) URLs are used, where the actual blog posts are not on the `feedburner.com` (or whatever) domain. In this case `include_remote_blogs` should be set to `true`.

            The response will return the Job information responsible for getting the requested data you can track using the `id` returned via the GET Jobs by ID endpoint.
            """
        ),
        responses={
            201: FeedCreatedJobSerializer,
            400: OpenApiResponse(CommonErrorSerializer, "Request not understood", examples=[HTTP400_EXAMPLE]),
            (404, "application/json"): OpenApiResponse(CommonErrorSerializer, "Feed not found", examples=[HTTP404_EXAMPLE]),
        },
    )
    @decorators.action(methods=["PATCH"], detail=True)
    def fetch(self, request, *args, **kwargs):
        feed_obj: Feed = self.get_object()
        if feed_obj.feed_type == FeedType.SKELETON:
            raise validators.ValidationError(f"fetch not supported for feed of type {feed_obj.feed_type}")
        s = FeedFetchSerializer(feed_obj, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        job_obj = task_helper.new_job(feed_obj, s.validated_data.get('include_remote_blogs', False))
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
        responses={
            200: FeedSerializer,
            400: OpenApiResponse(CommonErrorSerializer, "Request not understood", examples=[HTTP400_EXAMPLE]),
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
        responses={
            200: FeedSerializer,
            404: OpenApiResponse(CommonErrorSerializer, "Not found", examples=[HTTP404_EXAMPLE]),
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
        responses={
            200: {},
            404: OpenApiResponse(
                CommonErrorSerializer,
                "Not found",
                examples=[HTTP404_EXAMPLE],
            ),
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)



@extend_schema_view(
    destroy=extend_schema(
        summary="Delete a Feed by ID",
        description="This will delete the post inside of the feed. Deleting the post will remove it forever and it will not be reindexed on subsequent feed updates. The only way to re-index it is to add it manually.",
    ),
    retrieve=extend_schema(
        parameters=[FEED_ID_PARAM, POST_ID_PARAM],
        summary="Get a Post in a Feed",
        description=textwrap.dedent(
            """
            This will return a single Post in a Feed using its ID. It is useful if you only want to get the data for a single entry.
            """
        ),
        responses={
            200: PostSerializer,
            404: OpenApiResponse(CommonErrorSerializer, "Feed or post not found", examples=[HTTP404_EXAMPLE]),
            400: OpenApiResponse(CommonErrorSerializer, "Request not understood", examples=[HTTP400_EXAMPLE]),
        },
    ),
    list=extend_schema(
        summary="Search for Posts in a Feed (JSON)",
        description=textwrap.dedent(
            """
            Use this endpoint if you want to search through all Posts in a Feed. The response of this endpoint is JSON, and is useful if you're building a custom integration to a downstream tool. If you just want to import the data for this blog into your feed reader use the RSS version of this endpoint.
            """
        ),
        responses={
            200: PostSerializer,
            404: OpenApiResponse(CommonErrorSerializer, "Feed not found", examples=[HTTP404_EXAMPLE]),
            400: OpenApiResponse(CommonErrorSerializer, "Request not understood", examples=[HTTP400_EXAMPLE]),
        },
    ),
    partial_update=extend_schema(
        description=textwrap.dedent(
            """
            Occasionally updates to blog posts are not reflected in RSS and ATOM feeds. To ensure the post stored in history4feed matches the currently published post you make a request to this endpoint using the Post ID to update it.

            The following key/values are accepted in the body of the request:

            IMPORTANT: This action will delete the original post content making it irretrievable.

            The response will return the Job information responsible for getting the requested data you can track using the `id` returned via the GET Jobs by ID endpoint.
            """
        ),
        summary="Update a Post in a Feed",
        responses={
            201: PostJobSerializer,
            404: OpenApiResponse(CommonErrorSerializer, "Feed or post does not exist", examples=[HTTP404_EXAMPLE]),
        },
        request=PatchSerializer,
    ),
)

class FeedPostView(
    PostOnlyView
):

    openapi_tags = ["Feeds"]
    serializer_class = PostSerializer

    class filterset_class(PostOnlyView.filterset_class):
        feed_id = None

    def get_queryset(self):
        return Post.visible_posts().filter(feed_id=self.kwargs.get("feed_id"))

    @extend_schema(
        parameters=[FEED_ID_PARAM],
        filters=True,
        summary="Search for Posts in a Feed (RSS)",
        description=textwrap.dedent(
            """
            Use this endpoint with your feed reader. The response of this endpoint is valid RSS XML for the Posts in the Feed. If you want more flexibility (perhaps to build a custom integration) use the JSON version of this endpoint.
            """
        ),
        responses={
            (200, RSSRenderer.media_type): XML_RESPONSE,
            (404, "application/json"): OpenApiResponse(CommonErrorSerializer, "Feed not found", examples=[HTTP404_EXAMPLE]),
            (400, "application/json"): OpenApiResponse(CommonErrorSerializer, "Request not understood", examples=[HTTP400_EXAMPLE]),
        },
    )
    @decorators.action(
        methods=["get"],
        detail=False,
        pagination_class=XMLPostPagination("xml_posts"),
        renderer_classes=[RSSRenderer, renderers.JSONRenderer],
    )
    def xml(self, request: request.Request, *args, feed_id=None, **kwargs):
        feed_obj = get_object_or_404(Feed, id=feed_id)
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        body = build_rss.build_rss(feed_obj, page)
        return self.paginator.get_paginated_response(body)
    

    def partial_update(self, request, *args, **kwargs):
        s = PatchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        post: Post = self.get_object()
        job_obj = task_helper.new_patch_posts_job(post.feed, [post])
        job_resp = JobSerializer(job_obj).data.copy()
        job_resp.update(post_id=post.id)
        return Response(job_resp, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        parameters=[FEED_ID_PARAM],
        summary="Add a Post manually to a Feed",
        description=textwrap.dedent(
            """
            This endpoint allows you to add Posts manually to a Feed. This endpoint is designed to ingest posts that are not identified by the Wayback Machine (used by the POST Feed endpoint during ingestion). If the feed you want to add a post to does not already exist, you should first add it using the POST Feed endpoint.

            The following key/values are accepted in the body of the request:

            * `link` (required - must be unique): The URL of the blog post. This is where the content of the post is found. It cannot be the same as the `url` of a post already in this feed. If you want to update the post, use the PATCH post endpoint.
            * `pubdate` (required): The date of the blog post in the format `YYYY-MM-DDTHH:MM:SS.sssZ`. history4feed cannot accurately determine a post date in all cases, so you must enter it manually.
            * `title` (required):  history4feed cannot accurately determine the title of a post in all cases, so you must enter it manually.
            * `author` (optional): the value to be stored for the author of the post.
            * `categories` (optional) : the value(s) to be stored for the category of the post. Pass as a list like `["tag1","tag2"]`.

            The response will return the Job information responsible for getting the requested data you can track using the `id` returned via the GET Jobs by ID endpoint.

            Each post ID is generated using a UUIDv5. The namespace used is `6c6e6448-04d4-42a3-9214-4f0f7d02694e` and the value used `<FEED_ID>+<POST_URL>+<POST_PUB_TIME (to .000000Z)>` (e.g. `d1d96b71-c687-50db-9d2b-d0092d1d163a+https://muchdogesec.github.io/fakeblog123///test3/2024/08/20/update-post.html+2024-08-20T10:00:00.000000Z` = `22173843-f008-5afa-a8fb-7fc7a4e3bfda`).

            _Note: We do have a proof-of-concept to scrape a site for all blog post urls, titles, and pubdate called [sitemap2posts](https://github.com/muchdogesec/sitemap2posts) which can help form the request body needed for this endpoint._
            """
        ),
        responses={
            201: PostJobSerializer,
            404: OpenApiResponse(CommonErrorSerializer, "Feed does not exist", examples=[HTTP404_EXAMPLE]),
        },
    )
    def create(self, request, *args, feed_id=None, **kwargs):
        deleted_obj = None
        data = dict(**request.data, feed_id=feed_id, feed=feed_id)

        s = PostSerializer(data=data)
        s.is_valid(raise_exception=True)

        try:
            deleted_obj = Post.objects.get(feed_id=feed_id, link=s.data['link'])
        except Exception as e:
            pass

        s2 = PostCreateSerializer(deleted_obj, data=data)
        s2.is_valid(raise_exception=True)
        post = s2.save(added_manually=True, deleted_manually=False)
        job_obj = task_helper.new_patch_posts_job(post.feed, [post])
        job_resp = JobSerializer(job_obj).data.copy()
        job_resp.update(post_id=post.id)
        return Response(job_resp, status=status.HTTP_201_CREATED)
    
    def destroy(self, *args, **kwargs):
        obj = self.get_object()
        obj.deleted_manually = True
        obj.save()
        obj.feed.save()
        return Response(None, status=status.HTTP_204_NO_CONTENT)



class JobView(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = JobSerializer
    pagination_class = Pagination("jobs")
    filter_backends = [DjangoFilterBackend, Ordering]
    ordering_fields = ["run_datetime", "state"]
    ordering = ["-run_datetime"]
    openapi_tags = ["Jobs"]
    lookup_url_kwarg = "job_id"
    lookup_field = "id"

    class filterset_class(FilterSet):
        feed_id = Filter(
            help_text="Filter Jobs by the ID of the Feed they belong to. You can search for Feed IDs using the GET Feeds endpoints. Note a Feed can have multiple jobs associated with it where a PATCH request has been run to update the Feed."
        )
        state = Filter(help_text="Filter by the status of a Job")
        post_id = UUIDFilter(help_text="Filter Jobs by the ID of the Post they belong to. You can search for Post IDs using the GET Posts endpoint. Note a Post can have multiple jobs associated with it where a PATCH request has been run to update a Feed or a Post.", field_name="fulltext_jobs__post_id")

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
        responses={
            200: JobSerializer,
            400: OpenApiResponse(
                CommonErrorSerializer,
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
        responses={
            200: JobSerializer,
            404: OpenApiResponse(
                CommonErrorSerializer,
                "Job not found",
                [HTTP404_EXAMPLE],
            ),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
