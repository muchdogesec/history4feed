import unittest

class BaseTest(unittest.TestCase):
    def setUp(self):
        # Define the base URL for the API requests
        self.base_url = "http://127.0.0.1:8002/api/v1/feeds/"

        # Feeds URLs, their corresponding feed IDs, descriptions, and feed types
        self.feeds = {
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-encoded.xml": {
                "id": "d1d96b71-c687-50db-9d2b-d0092d1d163a",
                "description": "RSS -- Contains encoded html -- FULL CONTENT",
                "feed_type": "rss"
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-decoded.xml": {
                "id": "8f89731d-b9de-5931-9182-5460af59ca84",
                "description": "RSS -- Contains decoded html (without CDATA tags, but it XML escaped) -- FULL CONTENT",
                "feed_type": "rss"
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-cdata.xml": {
                "id": "c8592fca-aa7b-55b7-9664-886230d7c338",
                "description": "RSS -- Contains decoded html inside CDATA tags -- FULL CONTENT",
                "feed_type": "rss"
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-encoded-partial.xml": {
                "id": "e6178850-0b78-54cc-9f3e-85b482b84f2b",
                "description": "RSS -- Contains encoded html -- PARTIAL CONTENT ONLY",
                "feed_type": "rss"
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-decoded-partial.xml": {
                "id": "8375e600-cc52-5823-8179-a8313ba9df5c",
                "description": "RSS -- Contains decoded html (without CDATA tags, but it XML escaped) -- PARTIAL CONTENT ONLY",
                "feed_type": "rss"
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-cdata-partial.xml": {
                "id": "2d6575b8-3d90-5479-bdfe-b980b753ec40",
                "description": "RSS -- Contains decoded html inside CDATA tags -- PARTIAL CONTENT ONLY",
                "feed_type": "rss"
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-encoded.xml": {
                "id": "2f21dfd2-e776-5d2b-ad3d-00460e540cca",
                "description": "ATOM -- Contains encoded html -- FULL CONTENT",
                "feed_type": "atom"
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-decoded.xml": {
                "id": "cb0ba709-b841-521a-a3f2-5e1429f4d366",
                "description": "ATOM -- Contains decoded html (without CDATA tags, but it XML escaped) -- FULL CONTENT",
                "feed_type": "atom"
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-cdata.xml": {
                "id": "121e5557-7277-5aa3-945d-e466c6bf92d5",
                "description": "ATOM -- Contains decoded html inside CDATA tags -- FULL CONTENT",
                "feed_type": "atom"
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-encoded-partial.xml": {
                "id": "66966023-522a-57af-93ac-88c6214e1891",
                "description": "ATOM -- Contains encoded html -- PARTIAL CONTENT ONLY",
                "feed_type": "atom"
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-decoded-partial.xml": {
                "id": "9c04d319-a949-52df-bcb6-5a73a1458fe5",
                "description": "ATOM -- Contains decoded html (without CDATA tags, but it XML escaped) -- PARTIAL CONTENT ONLY",
                "feed_type": "atom"
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-cdata-partial.xml": {
                "id": "220ae197-f66f-56b3-a17a-cbfc6dc9661a",
                "description": "ATOM -- Contains decoded html inside CDATA tags -- PARTIAL CONTENT ONLY",
                "feed_type": "atom"
            }
        }

        # Posts corresponding to feed IDs
        self.posts = {
            "d1d96b71-c687-50db-9d2b-d0092d1d163a": [
                {
                    "id": "8f16d2be-7b06-5f3c-a851-9cce31b4fec8",
                    "title": "Update this post for testing updates to posts",
                    "pubdate": "2024-08-20T10:00:00Z"
                },
                {
                    "id": "47f72d92-f22a-5f08-84f3-55aedf4c7967",
                    "title": "Testing Extractions",
                    "pubdate": "2024-08-07T08:00:00Z"
                },
                {
                    "id": "85a762c9-00f9-5c0c-9858-498883e13ea1",
                    "title": "Testing Markdown Elements",
                    "pubdate": "2024-08-05T08:00:00Z"
                }, 
                {
                    "id": "29be2407-d5d1-5b47-bbb5-1c51a84d48eb",
                    "title": "Real Post Example - Fighting Ursa Luring Targets With Car for Sale",
                    "pubdate": "2024-08-01T08:00:00Z"
                }
            ]
        }