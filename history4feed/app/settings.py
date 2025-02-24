from datetime import datetime, timezone
from typing import Any, Dict, get_type_hints
import uuid

from django.conf import settings
from rest_framework.settings import APISettings, perform_import, api_settings

H4F_DEFAULTS: dict[str, any] = {
    'SCRAPFLY_KEY': '',
    'WAYBACK_SLEEP_SECONDS': 20,
    'EARLIEST_SEARCH_DATE': datetime(2020, 1, 1, tzinfo=timezone.utc),
    'REQUEST_RETRY_COUNT': 3,
    'HISTORY4FEED_NAMESPACE': uuid.UUID("6c6e6448-04d4-42a3-9214-4f0f7d02694e"),
    "BRAVE_SEARCH_API_KEY": None
}

IMPORT_STRINGS = [
]

class History4FeedServerSettings(APISettings):
    SCRAPFLY_KEY: str
    WAYBACK_SLEEP_SECONDS: int
    EARLIEST_SEARCH_DATE: datetime
    REQUEST_RETRY_COUNT: int
    HISTORY4FEED_NAMESPACE : str|uuid.UUID
    BRAVE_SEARCH_API_KEY: str

history4feed_server_settings = History4FeedServerSettings(
    user_settings=getattr(settings, 'HISTORY4FEED_SETTINGS', {}),  # type: ignore
    defaults=H4F_DEFAULTS,  # type: ignore
    import_strings=IMPORT_STRINGS,
)