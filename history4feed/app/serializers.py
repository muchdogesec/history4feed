from rest_framework import serializers
from .models import Feed, Post, Job

class FeedSerializer(serializers.ModelSerializer):
    job_id = serializers.UUIDField(read_only=True, help_text="only returns with POST /feeds/")
    job_state = serializers.CharField(read_only=True, help_text="only returns with POST /feeds/")
    count_of_posts = serializers.IntegerField(source='get_post_count', read_only=True, help_text="Number of posts in feed")
    class Meta:
        model = Feed
        fields = '__all__'
        read_only_fields = ['id', 'title', 'description', 'earliest_item_pubdate', 'latest_item_pubdate', 'datetime_added']

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        exclude = ['feed']
        # fields = '__all__'

class JobSerializer(serializers.ModelSerializer):
    count_of_items = serializers.IntegerField(read_only=True)
    feed_id = serializers.UUIDField(read_only=True, source='feed.id')
    class Meta:
        model = Job
        # fields = '__all__'
        exclude = ['feed']
