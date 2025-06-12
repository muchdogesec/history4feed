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
    DatetimeFilter,
    Ordering,
    Pagination,
    MinMaxDateFilter,
    RSSRenderer,
    XMLPostPagination,
)
from dogesec_commons.utils.serializers import CommonErrorSerializer
# from .openapi_params import FEED_PARAMS, POST_PARAMS

from .serializers import CreatePostsSerializer, FeedCreatedJobSerializer, FeedFetchSerializer, FeedPatchSerializer, PostPatchSerializer, PostWithFeedIDSerializer, SearchIndexFeedSerializer, SkeletonFeedSerializer, PatchSerializer, PostJobSerializer, PostSerializer, FeedSerializer, JobSerializer, PostCreateSerializer
from .models import AUTO_TITLE_TRAIL, FulltextJob, JobState, Post, Feed, Job, FeedType
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
import django.utils

from history4feed.app import serializers

from history4feed.app import utils

from drf_spectacular.views import SpectacularAPIView

class SchemaViewCached(SpectacularAPIView):
    _schema = None
    
    def _get_schema_response(self, request):
        version = self.api_version or request.version or self._get_version_parameter(request)
        if not self.__class__._schema:
            generator = self.generator_class(urlconf=self.urlconf, api_version=version, patterns=self.patterns)
            self.__class__._schema = generator.get_schema(request=request, public=self.serve_public)
        return response.Response(
            data=self.__class__._schema,
            headers={"Content-Disposition": f'inline; filename="{self._get_filename(request, version)}"'}
        )

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
            200: PostWithFeedIDSerializer,
            404: OpenApiResponse(CommonErrorSerializer, "Post not found", examples=[HTTP404_EXAMPLE]),
            400: OpenApiResponse(CommonErrorSerializer, "Request not understood", examples=[HTTP400_EXAMPLE]),
        },
    ),
    list=extend_schema(
        summary="Search for Posts",
        description=textwrap.dedent(
            """
            Search through Posts from all Blogs. Filter by the ones you're interested in.
            """
        ),
        responses={
            200: PostWithFeedIDSerializer,
            404: OpenApiResponse(CommonErrorSerializer, "Feed not found", examples=[HTTP404_EXAMPLE]),
            400: OpenApiResponse(CommonErrorSerializer, "Request not understood", examples=[HTTP400_EXAMPLE]),
        },
    ),
    destroy=extend_schema(
        summary="Delete a Post by ID",
       description=textwrap.dedent(
            """
            This will delete the post inside of the feed. Deleting the post will remove it forever and it will not be reindexed on subsequent feed updates. The only way to re-index it is to add it manually.
            """
        ),
    ),
    reindex=extend_schema(
        summary="Update a Post in a Feed",
        description=textwrap.dedent(
            """
             When blog posts are modified, the RSS or ATOM feeds or search results are not often updated with the new modification time. As such, fetching for blog will cause these updated posts to be missed.

            To ensure the post stored in the database matches the one currently published you can make a request to this endpoint using the Post ID to update it.

            This update will only change the content (`description`) stored for the Post. It will not update the `title`, `pubdate`, `author`, or `categories`. If you need to update these properties you can use the Update Post Metadata endpoint.

            **IMPORTANT**: This action will delete the original post as well as all the STIX SDO and SRO objects created during the processing of the original text. Mostly this is not an issue, however, if the post has been removed at source you will end up with an empty entry for this Post.

            The response will return the Job information responsible for getting the requested data you can track using the `id` returned via the GET Jobs by ID endpoint.
            """
        ),
        responses={
            201: PostJobSerializer,
            404: OpenApiResponse(CommonErrorSerializer, "post does not exist", examples=[HTTP404_EXAMPLE]),
        },
        request=PatchSerializer,
    ),
    partial_update=extend_schema(
        summary="Update a Posts Metadata",
        description=textwrap.dedent(
            """
            In most cases, the automatically indexed metadata (or user submitted metadata in the case of manually added Posts) will be fine.

            However, these may be occasions you want to change the values of the `title`, `pubdate`, `author`, or `categories` for a Post.

            The following key/values are accepted in the body of the request:

            * `pubdate` (required): The date of the blog post in the format `YYYY-MM-DD`. history4feed cannot accurately determine a post date in all cases, so you must enter it manually.
            * `title` (required):  history4feed cannot accurately determine the title of a post in all cases, so you must enter it manually.
            * `author` (optional): the value to be stored for the author of the post.
            * `categories` (optional) : the value(s) to be stored for the category of the post. Pass as a list like `["tag1","tag2"]`.

            Only one key/value is required. If no values are passed, they will be remain unchanged from the current state.

            It is not possible to manually modify any other values for the Post object. You can update the post content using the Update a Post in A Feed endpoint.
            """
        ),
        responses={
            201: PostSerializer,
            400: OpenApiResponse(CommonErrorSerializer, "Request not understood", examples=[HTTP400_EXAMPLE]),
            404: OpenApiResponse(CommonErrorSerializer, "post does not exist", examples=[HTTP404_EXAMPLE]),
        },
        request=PostPatchSerializer,
    ),

)
class PostOnlyView(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    openapi_path_params = [POST_ID_PARAM]
    openapi_tags = ["Posts"]
    serializer_class = PostWithFeedIDSerializer
    lookup_url_kwarg = "post_id"
    pagination_class = Pagination("posts")
    filter_backends = [DjangoFilterBackend, Ordering, MinMaxDateFilter]
    ordering_fields = ["pubdate", "title", "datetime_updated", "datetime_added"]
    ordering = "pubdate_descending"
    minmax_date_fields = ["pubdate"]

    class filterset_class(FilterSet):
        feed_id = filters.BaseInFilter(help_text="Filter the results by one or more `feed_id`(s). e.g. `3f388179-4683-4495-889f-690c5de3ae7c`")
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
        job_id = Filter(help_text="Filter the results by the Job ID the Post was downloaded or updated in. e.g. `6606bd0c-9d9d-4ffd-81bb-81c9196ccfe6`", field_name="fulltext_jobs__job_id")
        job_state = filters.ChoiceFilter(choices=JobState.choices, help_text="Filter by job status")
        updated_after = DatetimeFilter(help_text="Only show posts with a `datetime_updated` after the time specified. It must be in `YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]`, e.g. `2020-01-01 00:00`", field_name="datetime_updated", lookup_expr="gt")

    def get_queryset(self):
        return Post.visible_posts() \
                .annotate(job_state=Subquery(Job.objects.filter(pk=OuterRef('last_job_id')).values('state')[:1]))
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = PostPatchSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        s = self.get_serializer(instance)
        return Response(s.data, status=status.HTTP_201_CREATED)
    
    @decorators.action(detail=True, methods=['PATCH'])
    def reindex(self, request, *args, **kwargs):
        post, job_obj = self.new_reindex_post_job(request)
        job_resp = JobSerializer(job_obj).data.copy()
        job_resp.update(post_id=post.id)
        return Response(job_resp, status=status.HTTP_201_CREATED)

    def new_reindex_post_job(self, request):
        s = PatchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        post: Post = self.get_object()
        job_obj = task_helper.new_patch_posts_job(post.feed, [post])
        return post, job_obj

    def destroy(self, *args, **kwargs):
        obj = self.get_object()
        obj.deleted_manually = True
        obj.save()
        obj.feed.save()
        return Response(None, status=status.HTTP_204_NO_CONTENT)



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
    ordering = "datetime_added_descending"
    minmax_date_fields = ["earliest_item_pubdate", "latest_item_pubdate"]

    class filterset_class(FilterSet):
        title = Filter(
            help_text="Filter by the content in feed title. Will search for titles that contain the value entered. Search is wildcard so `exploit` will match `exploited` and `exploits`.",
            lookup_expr="icontains",
        )
        description = Filter(
            help_text="Filter by the content in feed description. Will search for descriptions that contain the value entered. Search is wildcard so `exploit` will match `exploited` and `exploits`.",
            lookup_expr="icontains",
        )
        url = Filter(
            help_text="Filter by the content in a feeds URL. Will search for URLs that contain the value entered. Search is wildcard so `google` will match `google.com` and `google.co.uk`.",
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
        summary="Create a New Feed",
        description=textwrap.dedent(
            """
            Use this endpoint to create to a new feed.

            The following key/values are accepted in the body of the request:

            * `url` (required): a valid RSS or ATOM feed URL (if `use_search_index` = `false`) OR the URL of the blog (if `use_search_index` = `true`).
            * `include_remote_blogs` (required): is a boolean setting and will ask history4feed to ignore any feeds not on the same domain as the URL of the feed. Some RSS/ATOM feeds include remote posts from other sites (e.g. for a paid promotion). This setting (set to `false` allows you to ignore remote posts that do not use the same domain as the `url` used). Generally you should set `include_remote_blogs` to `false`. The one exception is when things like feed aggregators (e.g. Feedburner) URLs are used, where the actual blog posts are not on the `feedburner.com` (or whatever) domain. In this case `include_remote_blogs` should be set to `true`.
            * `pretty_url` (optional): you can also include a secondary URL in the database. This is designed to be used to show the link to the blog (not the RSS/ATOM) feed so that a user can navigate to the blog in their browser.
            * `title` (optional): the title of the feed will be used if not passed. You can also manually pass the title of the blog here.
            * `description` (optional): the description of the feed will be used if not passed. You can also manually pass the description of the blog here.
            * `use_search_index` (optional, default is `false`): If the `url` is not a valid RSS or ATOM feed you must set this mode to `true`. Set to `true` this mode uses search results that contain the base `url` passed vs. the RSS/ATOM feed entries (when this mode is set to `false`). This mode is only be able to index results in Google Search, so can miss some sites entirely where they are not indexed by Google. You must also pass a `title` and `description` when setting this mode to `true`. Note, you can use the skeleton endpoint to create a feed manually from a non RSS/ATOM URL or where search results do not satisfy your use case.

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

        job_obj = self.new_create_job(request)
        resp_data = self.serializer_class(job_obj.feed).data.copy()
        resp_data.update(
            job_state=job_obj.state,
            job_id=job_obj.id,
        )
        return Response(resp_data, status=status.HTTP_201_CREATED)
    
    def new_create_job(self, request: request.Request):
        feed_data = {}
        s = FeedSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        if s.validated_data["use_search_index"]:
            s = SearchIndexFeedSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            feed_data.update(feed_type=FeedType.SEARCH_INDEX)
        else:
            try:
                feed_data = h4f.parse_feed_from_url(s.data["url"])
            except Exception as e:
                raise serializers.InvalidFeed(s.data["url"])

        for k in ['title', 'description']:
            if v := s.validated_data.get(k):
                feed_data[k] = v
            elif v := feed_data.get(k):
                feed_data[k] = v + AUTO_TITLE_TRAIL
        
        s2 = FeedSerializer(data={**s.data, **feed_data})
        s2.is_valid(raise_exception=True)

        feed_obj: Feed = s2.save(feed_type=feed_data['feed_type'])
        job_obj = task_helper.new_job(feed_obj, s.validated_data.get('include_remote_blogs', False))
        return job_obj

    @extend_schema(
        summary="Create a New Skeleton Feed",
        description=textwrap.dedent(
            """
            Sometimes it might be the case you want to curate a blog manually using various URLs from different blogs. This is what `skeleton` feeds are designed for, allowing you to create a skeleton feed and then add posts to it manually later on using the add post manually endpoint.

            The following key/values are accepted in the body of the request:

            * `url` (required): the URL to be attached to the feed. Needs to be a URL (because this is what feed ID is generated from), however does not need to be valid.
            * `pretty_url` (optional): you can also include a secondary URL in the database. This is designed to be used to show the link to the blog (not the RSS/ATOM) feed so that a user can navigate to the blog in their browser.
            * `title` (required): the title of the feed
            * `description` (optional): the description of the feed

            The response will return the created Feed object with the Feed `id`.
            """
        ),
        responses={
            201: FeedSerializer,
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
            Update the metadata of the Feed.

            Note, it is not possible to update the `url` of the feed. You must delete the Feed and add it again to modify the `url`.

            The following key/values are accepted in the body of the request:

            * `title` (optional): update the `title` of the Feed
            * `description` (optional): update the `description` of the Feed
            * `pretty_url` (optional): update the `pretty_url of the Feed

            Only one/key value is required in the request. For those not passed, the current value will remain unchanged.

            The response will contain the newly updated Feed object.

            Every time the feed is updated, the `datetime_modified` property in the Feed object will be updated accordingly.
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
        s.save(datetime_modified=django.utils.timezone.now())
        return Response(self.serializer_class(feed_obj).data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        parameters=[FEED_ID_PARAM],
        summary="Fetch Updates for a Feed",
        request=FeedFetchSerializer,
        description=textwrap.dedent(
            """
            Use this endpoint to check for new posts on this blog since the last post time. An update request will immediately trigger a job to get the posts between `latest_item_pubdate` for feed and time you make a request to this endpoint.

            The following key/values are accepted in the body of the request:

             * `include_remote_blogs` (required): is a boolean setting and will ask history4feed to ignore any feeds not on the same domain as the URL of the feed. Some feeds include remote posts from other sites (e.g. for a paid promotion). This setting (set to `false` allows you to ignore remote posts that do not use the same domain as the `url` used). Generally you should set `include_remote_blogs` to `false`. The one exception is when things like feed aggregators (e.g. Feedburner) URLs are used, where the actual blog posts are not on the `feedburner.com` (or whatever) domain. In this case `include_remote_blogs` should be set to `true`.

            Each post ID is generated using a UUIDv5. The namespace used is `6c6e6448-04d4-42a3-9214-4f0f7d02694e` (history4feed) and the value used `<FEED_ID>+<POST_URL>+<POST_PUB_TIME (to .000000Z)>` (e.g. `d1d96b71-c687-50db-9d2b-d0092d1d163a+https://muchdogesec.github.io/fakeblog123///test3/2024/08/20/update-post.html+2024-08-20T10:00:00.000000Z` = `22173843-f008-5afa-a8fb-7fc7a4e3bfda`).

            **IMPORTANT:** this request will fail if run against a Skeleton type feed. Skeleton feeds can only be updated by adding posts to them manually using the Manually Add a Post to a Feed endpoint.

            **IMPORTANT:** this endpoint can miss updates that have happened to currently indexed posts (where the RSS or ATOM feed or search results do not report the updated date correctly -- which is actually very common). To solve this issue for currently indexed blog posts, use the Update a Post in a Feed endpoint directly.

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
        job_obj = self.new_fetch_job(request)
        feed = self.serializer_class(self.get_object()).data.copy()
        feed.update(
            job_state=job_obj.state,
            job_id=job_obj.id,
        )
        return Response(feed, status=status.HTTP_201_CREATED)

    def new_fetch_job(self, request):
        feed_obj: Feed = self.get_object()
        if feed_obj.feed_type == FeedType.SKELETON:
            raise validators.ValidationError(f"fetch not supported for feed of type {feed_obj.feed_type}")
        s = FeedFetchSerializer(feed_obj, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return task_helper.new_job(feed_obj, s.validated_data.get('include_remote_blogs', False))

    @extend_schema(
        summary="Search for Feeds",
        description=textwrap.dedent(
            """
            Use this endpoint to get a list of all the feeds you are currently subscribed to. This endpoint is usually used to get the ID of Deed you want to get blog post data for in a follow up request to the GET Feed Posts endpoints or to get the status of a job related to the Feed in a follow up request to the GET Job endpoint. If you already know the id of the Feed already, you can use the GET Feeds by ID endpoint.
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
            204: {},
            404: OpenApiResponse(
                CommonErrorSerializer,
                "Feed does not exist",
                examples=[HTTP404_EXAMPLE],
            ),
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
class RSSView(viewsets.GenericViewSet):
    class filterset_class(PostOnlyView.filterset_class):
        feed_id = None
    openapi_tags = ["Feeds"]
    renderer_classes=[RSSRenderer]
    lookup_url_kwarg = 'feed_id'

    @extend_schema(
        parameters=[FEED_ID_PARAM],
        filters=True,
        summary="RSS Feed for Feed",
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
        detail=True,
        pagination_class=XMLPostPagination("xml_posts"),
    )
    def rss(self, request: request.Request, *args, feed_id=None, **kwargs):
        feed_obj = get_object_or_404(Feed, id=feed_id)
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        body = build_rss.build_rss(feed_obj, page)
        return self.paginator.get_paginated_response(body)
    
    def get_queryset(self):
        return PostOnlyView.get_queryset(self).filter(feed_id=self.kwargs.get("feed_id"))


@extend_schema_view(
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
)

class feed_post_view(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):

    openapi_tags = ["Feeds"]
    serializer_class = PostSerializer

    class filterset_class(PostOnlyView.filterset_class):
        feed_id = None
    
    
    def get_queryset(self):
        return PostOnlyView.get_queryset(self).filter(feed_id=self.kwargs.get("feed_id"))
    
    
    @extend_schema(
        parameters=[FEED_ID_PARAM],
        summary="Manually Add a Post to A Feed",
        description=textwrap.dedent(
            """
            Sometimes historic posts are missed when a feed is indexed (typically when no Wayback Machine archive exists).

            This endpoint allows you to add Posts manually to a Feed.

            If the feed you want to add a post to does not already exist, you should first add it using the POST Feed or POST skeleton feed endpoints.

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
        request=CreatePostsSerializer,
    )
    def create(self, request, *args, feed_id=None, **kwargs):
        job_obj = self.new_create_post_job(request, feed_id)
        job_resp = JobSerializer(job_obj).data.copy()
        # job_resp.update(post_id=post.id)
        return Response(job_resp, status=status.HTTP_201_CREATED)

    def new_create_post_job(self, request, feed_id):
        feed_obj = get_object_or_404(Feed, id=feed_id)
        data = dict(request.data) #, feed_id=feed_id, feed=feed_id)

        s = CreatePostsSerializer(data=data, context=dict(feed_id=feed_id))
        s.is_valid(raise_exception=True)

        posts = s.save(added_manually=True, deleted_manually=False)

        job_obj = task_helper.new_patch_posts_job(feed_obj, posts)
        return job_obj
    

    @extend_schema(
        summary="Update all Posts in a Feed",
        description=textwrap.dedent(
            """
                This endpoint will reindex the Post content (`description`) for all Post IDs currently listed in the Feed.

                This request will only change the content (`description`) stored for the Post ID. It will not update the title, pubdate, author, or categories. If you need to update these properties you can use the Update Post Metadata endpoint.

                Note, if you only want to update the content of a single post, it is much more effecient to use the Update a Post in a Feed endpoint.
            """
        ),
        responses={
            201: PostJobSerializer,
            404: OpenApiResponse(CommonErrorSerializer, "Feed does not exist", examples=[HTTP404_EXAMPLE]),
        },
        request={},
    )
    @decorators.action(methods=["PATCH"], detail=False, url_path='reindex')
    def reindex_feed(self, request, *args, feed_id=None, **kwargs):
        job_obj = self.new_reindex_feed_job(feed_id)
        job_resp = JobSerializer(job_obj).data.copy()
        # job_resp.update(post_id=post.id)
        return Response(job_resp, status=status.HTTP_201_CREATED)

    def new_reindex_feed_job(self, feed_id):
        posts = self.get_queryset().all()
        feed_obj = get_object_or_404(Feed, id=feed_id)
        job_obj = task_helper.new_patch_posts_job(feed_obj, tuple(posts))
        return job_obj


class FeedPostView(
    feed_post_view
):
    pass

class JobView(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = JobSerializer
    pagination_class = Pagination("jobs")
    filter_backends = [DjangoFilterBackend, Ordering]
    ordering_fields = ["run_datetime", "state"]
    ordering = "run_datetime_descending"
    openapi_tags = ["Jobs"]
    lookup_url_kwarg = "job_id"
    lookup_field = "id"

    class filterset_class(FilterSet):
        feed_id = Filter(
            help_text="Filter Jobs by the ID of the Feed they belong to. You can search for Feed IDs using the GET Feeds endpoints. Note a Feed can have multiple jobs associated with it where a PATCH request has been run to update the Feed. e.g. `6c6e6448-04d4-42a3-9214-4f0f7d02694e`"
        )
        state = Filter(help_text="Filter by the status of a Job")
        post_id = UUIDFilter(help_text="Filter Jobs by the ID of the Post they belong to. You can search for Post IDs using the GET Posts endpoint. Note a Post can have multiple jobs associated with it where a PATCH request has been run to update a Feed or a Post. e.g `797e94b1-efdc-4e66-a748-f2b6a5896a89`", field_name="fulltext_jobs__post_id")

    def get_queryset(self):
        return Job.objects.all().annotate(count_of_items=Count("fulltext_jobs"))

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
    

    @extend_schema(
        parameters=[JOB_ID_PARAM],
        summary="Kill a running Job that is indexing Posts",
        description=textwrap.dedent(
            """
            Using a Job ID you can kill it whilst it is still in `running` or `pending` state.

            If any posts have already been downloaded before the job is complete, they will still remain and you will need to delete them using the delete endpoints manually.

            The job will enter `cancelled` state when cancelled.
            """
        ),
        responses={
            204: {},
            404: OpenApiResponse(
                CommonErrorSerializer,
                "Job not found",
                [HTTP404_EXAMPLE],
            ),
        },
    )
    @decorators.action(methods=['DELETE'], detail=True, url_path="kill")
    def cancel_job(self, request, *args, **kwargs):
        obj: Job = self.get_object()
        obj.cancel()
        return Response(status=status.HTTP_204_NO_CONTENT)
