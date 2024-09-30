from rest_framework import serializers
from .models import Feed, Post, Job

class FeedSerializer(serializers.ModelSerializer):
    count_of_posts = serializers.IntegerField(source='get_post_count', read_only=True, help_text="Number of posts in feed")
    profile_id = serializers.UUIDField(write_only=True, required=False)
    class Meta:
        model = Feed
        fields = '__all__'
        read_only_fields = ['id', 'title', 'description', 'earliest_item_pubdate', 'latest_item_pubdate', 'datetime_added']

class FeedCreateSerializer(FeedSerializer):
    job_id = serializers.UUIDField(read_only=True, help_text="only returns with POST /feeds/")
    job_state = serializers.CharField(read_only=True, help_text="only returns with POST /feeds/")
    

class PostSerializer(serializers.ModelSerializer):
    profile_id = serializers.UUIDField()
    class Meta:
        model = Post
        exclude = ['feed']
        # fields = '__all__'

class PatchSerializer(serializers.Serializer):
    profile_id = serializers.UUIDField(required=False, default=None)


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


class H4FError(serializers.Serializer):
    detail = serializers.CharField()
    code = serializers.IntegerField()
