from rest_framework import serializers, validators, exceptions
from .models import AUTO_TITLE_TRAIL, FEED_DESCRIPTION_MAX_LENGTH, Category, Feed, Post, Job, normalize_url, FeedType, title_as_string
from django.db import models as django_models
from django.utils.translation import gettext_lazy as _

class TitleField(serializers.CharField):
    def to_internal_value(self, data):
        return super().to_internal_value(data)
    def to_representation(self, value):
        return title_as_string(super().to_representation(value))
    
class InvalidFeed(exceptions.APIException):
    status_code = 406

class FeedSerializer(serializers.ModelSerializer):
    count_of_posts = serializers.IntegerField(source='get_post_count', read_only=True, help_text="Number of posts in feed")
    include_remote_blogs = serializers.BooleanField(write_only=True, default=False)
    pretty_url = serializers.URLField(allow_null=True, required=False, help_text="This is a cosmetic URL. It is designed to show the actual blog link to browse to in a web browser (not the feed)")
    title = TitleField(required=False, max_length=256, allow_null=True, allow_blank=True)
    description = TitleField(required=False, max_length=FEED_DESCRIPTION_MAX_LENGTH, allow_null=True, allow_blank=True)
    use_search_index = serializers.BooleanField(default=False, write_only=True, help_text="should use search index instead")
    class Meta:
        model = Feed
        # fields = '__all__'
        exclude = ['freshness']
        read_only_fields = ['id', 'earliest_item_pubdate', 'latest_item_pubdate', 'datetime_added', "datetime_modified"]

    def create(self, validated_data: dict):
        validated_data = validated_data.copy()
        validated_data.pop('include_remote_blogs', None)
        validated_data.pop('use_search_index', None)
        return super().create(validated_data)
    
class SkeletonFeedSerializer(FeedSerializer):
    include_remote_blogs = None
    use_search_index = None
    title = serializers.CharField(required=True, help_text="title of feed")
    description = serializers.CharField(required=False, help_text="description of feed", allow_blank=True)
    feed_type = serializers.HiddenField(default=FeedType.SKELETON)
    
class SearchIndexFeedSerializer(FeedSerializer):
    title = serializers.CharField(required=True, help_text="title of feed")
    description = serializers.CharField(required=True, help_text="description of feed")
    feed_type = serializers.HiddenField(default=FeedType.SEARCH_INDEX)


class FeedCreatedJobSerializer(FeedSerializer):
    job_id = serializers.UUIDField(read_only=True, help_text="only returns with POST /feeds/")
    job_state = serializers.CharField(read_only=True, help_text="only returns with POST /feeds/")
    

class PostListSerializer(serializers.ListSerializer):
    child = None

    @property
    def feed_id(self):
        return self.context.get('feed_id')
    

    def run_child_validation(self, data):
        """
        Run validation on child serializer.
        You may need to override this method to support multiple updates. For example:

        self.child.instance = self.instance.get(pk=data['id'])
        self.child.initial_data = data
        return super().run_child_validation(data)
        """
        data.setdefault('feed', self.feed_id)
        return self.child.run_validation(data)
    
    def create(self, validated_data: list[dict]):
        instances = []
        for attrs in validated_data:
            feed_id = attrs.setdefault('feed_id', self.feed_id)
            instance = None
            try:
                instance = Post.objects.get(feed_id=feed_id, link=attrs['link'])
            except:
                pass
            if instance:
                instance = self.child.update(instance, attrs)
            else:
                instance = self.child.create(attrs)

            instances.append(instance)
        return instances

class PostSerializer(serializers.ModelSerializer):
    # categories = serializers.ManyRelatedField()
    class Meta:
        list_serializer_class = PostListSerializer
        model = Post
        exclude = ['feed', 'deleted_manually']
        read_only_fields = ["id", "datetime_updated", "datetime_added", "description", "is_full_text", "content_type", "added_manually"]
        
    
    def run_validation(self, data=...):
        if categories := data.get('categories'):
            data['categories'] = [Category.objects.get_or_create(name=name)[0].name for name in categories]
        return super().run_validation(data)
    
class PostWithFeedIDSerializer(PostSerializer):
    feed_id = serializers.UUIDField()

class PatchSerializer(serializers.Serializer):
    pass

class FeedPatchSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True, help_text="title of feed")
    description = serializers.CharField(required=True, help_text="description of feed")

    class Meta:
        model = Feed
        fields = ['title', 'description', 'pretty_url']

class FeedFetchSerializer(FeedPatchSerializer, FeedSerializer):
    class Meta:
        model = Feed
        fields = ['include_remote_blogs']

class PostCreateSerializer(PostSerializer):
    link = serializers.URLField(validators=[normalize_url])
    class feed_class(serializers.HiddenField):
        def get_default(self):
            return self.context.get('feed_id')
    feed_id = feed_class(default=None)
        
    class Meta:
        list_serializer_class = PostListSerializer
        model = Post
        fields = ["title", "link", "pubdate", "author", "categories", "feed_id"]
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Post.visible_posts(),
                fields=('feed_id', 'link'),
                message='Post with link already exists in feed.',
            )
        ]

class PostPatchSerializer(PostSerializer):
    class Meta:
        model = Post
        fields = ["title", "pubdate", "author", "categories"]

    
class CreatePostsSerializer(serializers.Serializer):
    posts = PostCreateSerializer(many=True, allow_empty=False)

    def create(self, validated_data):
        posts = [{**post, **self.save_kwargs} for post in validated_data["posts"]]
        
        return self.fields['posts'].create(posts)
    
    def save(self, **kwargs):
        self.save_kwargs = kwargs
        return super().save(**kwargs)



class JobUrlStatusSerializer(serializers.Serializer):
    class joburlstatus(serializers.Serializer):
        url = serializers.URLField()
        id = serializers.UUIDField()
    retrieved = joburlstatus(many=True, default=[])
    retrieving = joburlstatus(many=True, default=[])
    skipped = joburlstatus(many=True, default=[])
    failed = joburlstatus(many=True, default=[])
    cancelled = joburlstatus(many=True, default=[])

class JobSerializer(serializers.ModelSerializer):
    count_of_items = serializers.IntegerField(read_only=True)
    feed_id = serializers.UUIDField(read_only=True, source='feed.id')
    urls = JobUrlStatusSerializer()
    class Meta:
        model = Job
        # fields = '__all__'
        exclude = ['feed']

class PostJobSerializer(JobSerializer):
    count_of_items = None
