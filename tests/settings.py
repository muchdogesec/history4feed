from history4feed.settings import *

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

HISTORY4FEED_SETTINGS.update(SCRAPFLY_APIKEY='')