from rest_framework import serializers, validators
from .models import Category, Feed, Post, Job, normalize_url
from django.db import models as django_models
from django.utils.translation import gettext_lazy as _

class FeedSerializer(serializers.ModelSerializer):
    count_of_posts = serializers.IntegerField(source='get_post_count', read_only=True, help_text="Number of posts in feed")
    profile_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    include_remote_blogs = serializers.BooleanField(write_only=True, default=False)
    class Meta:
        model = Feed
        fields = '__all__'
        read_only_fields = ['id', 'title', 'description', 'earliest_item_pubdate', 'latest_item_pubdate', 'datetime_added']

    def create(self, validated_data: dict):
        validated_data = validated_data.copy()
        validated_data.pop('include_remote_blogs', None)
        return super().create(validated_data)

class FeedCreateSerializer(FeedSerializer):
    job_id = serializers.UUIDField(read_only=True, help_text="only returns with POST /feeds/")
    job_state = serializers.CharField(read_only=True, help_text="only returns with POST /feeds/")
    

class PostSerializer(serializers.ModelSerializer):
    profile_id = serializers.UUIDField(required=False, default=None)
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
    profile_id = serializers.UUIDField(required=False, default=None)

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
