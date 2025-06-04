from datetime import datetime, timezone
import os
from typing import Any, Dict, get_type_hints
import uuid
from django.core.signals import setting_changed

from django.conf import settings
from rest_framework.settings import APISettings, perform_import, api_settings

H4F_DEFAULTS: dict[str, any] = {
    'SCRAPFLY_APIKEY': os.getenv('SCRAPFLY_APIKEY'),
    'WAYBACK_SLEEP_SECONDS': 20,
    'EARLIEST_SEARCH_DATE': datetime(2020, 1, 1, tzinfo=timezone.utc),
    'REQUEST_RETRY_COUNT': 3,
    'HISTORY4FEED_NAMESPACE': uuid.UUID("6c6e6448-04d4-42a3-9214-4f0f7d02694e"),
    "BRAVE_SEARCH_API_KEY": None
}

IMPORT_STRINGS = [
]

class History4FeedServerSettings(APISettings):
    SCRAPFLY_APIKEY: str
    WAYBACK_SLEEP_SECONDS: int
    EARLIEST_SEARCH_DATE: datetime
    REQUEST_RETRY_COUNT: int
    HISTORY4FEED_NAMESPACE : str|uuid.UUID
    BRAVE_SEARCH_API_KEY: str

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, 'HISTORY4FEED_SETTINGS', {})
        return self._user_settings

history4feed_server_settings = History4FeedServerSettings(
    user_settings=getattr(settings, 'HISTORY4FEED_SETTINGS', {}),  # type: ignore
    defaults=H4F_DEFAULTS,  # type: ignore
    import_strings=IMPORT_STRINGS,
)


def reload_api_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == 'HISTORY4FEED_SETTINGS':
        history4feed_server_settings.reload()


setting_changed.connect(reload_api_settings)
