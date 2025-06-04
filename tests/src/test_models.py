

from unittest.mock import patch
import uuid
from django.core import validators
import pytest
from history4feed.app import models
from history4feed.app.settings import history4feed_server_settings
from rest_framework.validators import ValidationError


def test_stix_id():
    url = 'https://goo.gl'
    with patch('uuid.uuid5') as mock_uuid5:
        gen_id = models.stix_id(url)
        mock_uuid5.assert_called_once_with(uuid.UUID(str(history4feed_server_settings.HISTORY4FEED_NAMESPACE)), url)
        assert gen_id == mock_uuid5.return_value
    assert models.stix_id(url) == models.stix_id(url), "should be deterministic"

def test_normalize_url():
    assert models.normalize_url('https://example.com/net/') == 'https://example.com/net/'
    assert models.normalize_url('https://example.com//net//') == 'https://example.com/net/'
    assert models.normalize_url('http://example.com///net//a////') == 'http://example.com/net/a/'
    assert models.normalize_url('http://example.com///net') == 'http://example.com/net'
    assert models.normalize_url('http://example.com') == 'http://example.com/', "should add trailing slash when path is empty"

    with pytest.raises(ValidationError):
        models.normalize_url('kjasjkaskj')

@pytest.mark.django_db
def test_save_feed():

    orig_url = 'http://example.com///net//a////'
    feed = models.Feed.objects.create(title='my title', description='my description', url=orig_url)
    feed.save()

    assert feed.get_pretty_url() == orig_url
    assert feed.id == models.stix_id(feed.url)

def test_feed_get_pretty_url():
    orig_url = 'http://example.com'
    feed = models.Feed(title='my title', description='my description', url=orig_url)
    assert feed.get_pretty_url() == feed.url
    feed.pretty_url = 'https://example.net/pretty-url/'
    assert feed.get_pretty_url() == feed.pretty_url
