from rest_framework import serializers, validators
from .models import AUTO_TITLE_TRAIL, FEED_DESCRIPTION_MAX_LENGTH, Category, Feed, Post, Job, normalize_url, FeedType
from django.db import models as django_models
from django.utils.translation import gettext_lazy as _

class TitleField(serializers.CharField):
    def to_internal_value(self, data):
        return super().to_internal_value(data)
    def to_representation(self, value):
        value = super().to_representation(value)
        if value.endswith(AUTO_TITLE_TRAIL):
            value = value[:-len(AUTO_TITLE_TRAIL)]
        return value

class FeedSerializer(serializers.ModelSerializer):
    count_of_posts = serializers.IntegerField(source='get_post_count', read_only=True, help_text="Number of posts in feed")
    include_remote_blogs = serializers.BooleanField(write_only=True, default=False)
    pretty_url = serializers.URLField(allow_null=True, required=False, help_text="This is a cosmetic URL. It is designed to show the actual blog link to browse to in a web browser (not the feed)")
    title = TitleField(required=False, max_length=256, allow_null=True, allow_blank=True)
    description = TitleField(required=False, max_length=FEED_DESCRIPTION_MAX_LENGTH, allow_null=True, allow_blank=True)
    class Meta:
        model = Feed
        fields = '__all__'
        read_only_fields = ['id', 'earliest_item_pubdate', 'latest_item_pubdate', 'datetime_added']

    def create(self, validated_data: dict):
        validated_data = validated_data.copy()
        validated_data.pop('include_remote_blogs', None)
        return super().create(validated_data)
    
class SkeletonFeedSerializer(FeedSerializer):
    include_remote_blogs = None
    title = serializers.CharField(required=True, help_text="title of feed")
    description = serializers.CharField(required=True, help_text="description of feed")
    feed_type = serializers.HiddenField(default=FeedType.SKELETON)


class FeedCreatedJobSerializer(FeedSerializer):
    job_id = serializers.UUIDField(read_only=True, help_text="only returns with POST /feeds/")
    job_state = serializers.CharField(read_only=True, help_text="only returns with POST /feeds/")
    

class PostSerializer(serializers.ModelSerializer):
    # categories = serializers.ManyRelatedField()
    class Meta:
        model = Post
        exclude = ['feed']
        read_only_fields = ["id", "datetime_updated", "datetime_added", "description", "is_full_text", "content_type", "added_manually"]
        
    
    def run_validation(self, data=...):
        if categories := data.get('categories'):
            data['categories'] = [Category.objects.get_or_create(name=name)[0].name for name in categories]
        return super().run_validation(data)
    

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
    # feed_id = serializers.UUIDField(source='feed')
    link = serializers.URLField(validators=[normalize_url])
    class Meta:
        model = Post
        fields = ["title", "link", "pubdate", "author", "categories", "feed"]
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Post.objects.all(),
                fields=('feed', 'link'),
                message='Link already exists in field.',
            )
        ]



class JobUrlStatusSerializer(serializers.Serializer):
    class joburlstatus(serializers.Serializer):
        url = serializers.URLField()
        id = serializers.UUIDField()
    retrieved = joburlstatus(many=True, default=[])
    retrieving = joburlstatus(many=True, default=[])
    skipped = joburlstatus(many=True, default=[])
    failed = joburlstatus(many=True, default=[])

class JobSerializer(serializers.ModelSerializer):
    count_of_items = serializers.IntegerField(read_only=True)
    feed_id = serializers.UUIDField(read_only=True, source='feed.id')
    urls = JobUrlStatusSerializer()
    class Meta:
        model = Job
        # fields = '__all__'
        exclude = ['feed']

class PostJobSerializer(JobSerializer):
    post_id = serializers.UUIDField()
