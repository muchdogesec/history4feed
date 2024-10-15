import unittest
import requests
import time

# BaseTest class with feeds and posts definitions
class BaseTest(unittest.TestCase):
    def setUp(self):
        # Define the base URL for the API requests
        self.base_url = "http://127.0.0.1:8002/api/v1/feeds/"

        # Feeds URLs, their corresponding feed IDs, descriptions, and feed types
        self.feeds = {
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-encoded.xml": {
                "id": "d1d96b71-c687-50db-9d2b-d0092d1d163a",
                "description": "RSS -- Contains encoded html -- FULL CONTENT",
                "feed_type": "rss",
                "profile_id": ""
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-decoded.xml": {
                "id": "8f89731d-b9de-5931-9182-5460af59ca84",
                "description": "RSS -- Contains decoded html (without CDATA tags, but it XML escaped) -- FULL CONTENT",
                "feed_type": "rss",
                "profile_id": ""
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-cdata.xml": {
                "id": "c8592fca-aa7b-55b7-9664-886230d7c338",
                "description": "RSS -- Contains decoded html inside CDATA tags -- FULL CONTENT",
                "feed_type": "rss",
                "profile_id": ""
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-encoded-partial.xml": {
                "id": "e6178850-0b78-54cc-9f3e-85b482b84f2b",
                "description": "RSS -- Contains encoded html -- PARTIAL CONTENT ONLY",
                "feed_type": "rss",
                "profile_id": ""
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-decoded-partial.xml": {
                "id": "8375e600-cc52-5823-8179-a8313ba9df5c",
                "description": "RSS -- Contains decoded html (without CDATA tags, but it XML escaped) -- PARTIAL CONTENT ONLY",
                "feed_type": "rss",
                "profile_id": ""
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-cdata-partial.xml": {
                "id": "2d6575b8-3d90-5479-bdfe-b980b753ec40",
                "description": "RSS -- Contains decoded html inside CDATA tags -- PARTIAL CONTENT ONLY",
                "feed_type": "rss",
                "profile_id": ""
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-encoded.xml": {
                "id": "2f21dfd2-e776-5d2b-ad3d-00460e540cca",
                "description": "ATOM -- Contains encoded html -- FULL CONTENT",
                "feed_type": "atom",
                "profile_id": ""
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-decoded.xml": {
                "id": "cb0ba709-b841-521a-a3f2-5e1429f4d366",
                "description": "ATOM -- Contains decoded html (without CDATA tags, but it XML escaped) -- FULL CONTENT",
                "feed_type": "atom",
                "profile_id": ""
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-cdata.xml": {
                "id": "121e5557-7277-5aa3-945d-e466c6bf92d5",
                "description": "ATOM -- Contains decoded html inside CDATA tags -- FULL CONTENT",
                "feed_type": "atom",
                "profile_id": ""
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-encoded-partial.xml": {
                "id": "66966023-522a-57af-93ac-88c6214e1891",
                "description": "ATOM -- Contains encoded html -- PARTIAL CONTENT ONLY",
                "feed_type": "atom",
                "profile_id": ""
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-decoded-partial.xml": {
                "id": "9c04d319-a949-52df-bcb6-5a73a1458fe5",
                "description": "ATOM -- Contains decoded html (without CDATA tags, but it XML escaped) -- PARTIAL CONTENT ONLY",
                "feed_type": "atom",
                "profile_id": ""
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-cdata-partial.xml": {
                "id": "220ae197-f66f-56b3-a17a-cbfc6dc9661a",
                "description": "ATOM -- Contains decoded html inside CDATA tags -- PARTIAL CONTENT ONLY",
                "feed_type": "atom",
                "profile_id": ""
            },
        }

        # Posts corresponding to feed IDs

        #`d1d96b71-c687-50db-9d2b-d0092d1d163a+https://muchdogesec.github.io/fakeblog123///test1/2024/09/01/same-ioc-across-posts.html+2024-09-01T08:00:00.000000Z` = 84a8ff1c-c463-5a97-b0c4-93daf7102b5f
        self.posts = {
            "d1d96b71-c687-50db-9d2b-d0092d1d163a": [
                {
                    "id": "84a8ff1c-c463-5a97-b0c4-93daf7102b5f",
                    "title": "Obstracts AI relationship generation test 2",
                    "pubdate": "2024-09-01T08:00:00Z",
                    "url": "https://muchdogesec.github.io/fakeblog123///test1/2024/09/01/same-ioc-across-posts.html"
                },
                {
                    "id": "cfdb68b8-3d80-572d-9350-58baf57eabfb",
                    "title": "Obstracts AI relationship generation test",
                    "pubdate": "2024-08-23T08:00:00Z",
                    "url": "https://muchdogesec.github.io/fakeblog123///test1/2024/08/23/obstracts-ai-relationships.html"
                },
                {
                    "id": "8f16d2be-7b06-5f3c-a851-9cce31b4fec8",
                    "title": "Update this post for testing updates to posts",
                    "pubdate": "2024-08-20T10:00:00Z",
                    "url": "https://muchdogesec.github.io/fakeblog123///test3/2024/08/20/update-to-post-1.html"
                },
                {
                    "id": "47f72d92-f22a-5f08-84f3-55aedf4c7967",
                    "title": "Testing Extractions",
                    "pubdate": "2024-08-07T08:00:00Z",
                    "url": "https://muchdogesec.github.io/fakeblog123///test3/2024/08/07/testing-extractions-1.html"
                },
                {
                    "id": "85a762c9-00f9-5c0c-9858-498883e13ea1",
                    "title": "Testing Markdown Elements",
                    "pubdate": "2024-08-05T08:00:00Z",
                    "url": "https://muchdogesec.github.io/fakeblog123///test2/2024/08/05/testing-markdown-elements-1.html"
                }, 
                {
                    "id": "29be2407-d5d1-5b47-bbb5-1c51a84d48eb",
                    "title": "Real Post Example - Fighting Ursa Luring Targets With Car for Sale",
                    "pubdate": "2024-08-01T08:00:00Z",
                    "url": "https://muchdogesec.github.io/fakeblog123///test1/2024/08/01/real-post-example-1.html"
                }
            ]
        }

# TestFeedProcessing class inheriting from BaseTest
class TestFeedProcessing(BaseTest):

    def delete_existing_feeds(self):
        """Deletes only the feeds defined in BaseTest to ensure a clean state."""
        print("Starting deletion of existing feeds...")
        for feed_id in [details['id'] for details in self.feeds.values()]:
            url = f"{self.base_url}{feed_id}/"
            while True:
                response = requests.delete(url)
                print(f"DELETE {url} - Status Code: {response.status_code}")
                if response.status_code == 404:
                    print(f"Feed ID {feed_id} already deleted or not found.")
                    break
                elif response.status_code == 204:
                    print(f"Feed ID {feed_id} deleted successfully.")
                    break
                else:
                    print(f"Unexpected status code {response.status_code} when deleting feed ID {feed_id}.")
                    break

    def setUp(self):
        """Ensures that the DELETE operation runs before any test starts."""
        super().setUp()
        self.delete_existing_feeds()

    def check_job_status(self, job_id, max_retries=5, delay=30):
        """Check the job status until success or retry limit is reached."""
        job_url = f"http://localhost:8002/api/v1/jobs/{job_id}/"
        print(f"Checking job status for Job ID: {job_id}")
        for attempt in range(max_retries):
            response = requests.get(job_url, headers={"Accept": "application/json"})
            print(f"GET {job_url} - Status Code: {response.status_code} - Attempt {attempt + 1}/{max_retries}")
            self.assertEqual(response.status_code, 200, f"Request to {job_url} failed with status code {response.status_code}")
            data = response.json()
            state = data.get("state")
            print(f"Job ID {job_id} - State: {state}")
            if state == "success":
                print(f"Job ID {job_id} reached success state.")
                return True
            time.sleep(delay)  # Wait before the next check
        print(f"Job ID {job_id} did not reach success state after {max_retries} attempts.")
        return False

    def test_post_feed_urls_and_check_jobs(self):
        """Tests adding feeds one by one, waits for each job to succeed before adding the next, and verifies post retrieval."""

        # Step 1: Post each feed and wait for the job to succeed before moving to the next
        for feed_url, feed_details in self.feeds.items():
            with self.subTest(feed_url=feed_url):
                # Post the feed
                response = requests.post(
                    self.base_url,
                    json={
                        "url": feed_url,
                        "include_remote_blogs": False
                    },
                    headers={"Accept": "application/json"}  # Ensure the server responds with JSON
                )
                print(f"POST {self.base_url} - Feed URL: {feed_url} - Status Code: {response.status_code}")
                self.assertEqual(response.status_code, 201, f"Request to {self.base_url} failed with status code {response.status_code}")
                
                # Collect the job ID
                data = response.json()
                job_id = data.get("job_id")
                print(f"Job ID {job_id} received for Feed URL: {feed_url}")
                self.assertIsNotNone(job_id, f"Job ID not returned for URL {feed_url}")

                # Step 2: Wait for job to succeed (retry 5 times with 30 seconds delay)
                job_successful = self.check_job_status(job_id)
                self.assertTrue(job_successful, f"Job ID {job_id} for URL {feed_url} did not reach 'success' state after 5 retries")

                # Step 3: Verify that each post can be retrieved with a 200 OK response
                if feed_details["id"] in self.posts:
                    print(f"Verifying retrieval of posts for feed: {feed_url}")
                    for post in self.posts[feed_details["id"]]:
                        post_url = f"http://localhost:8002/api/v1/feeds/{feed_details['id']}/posts/{post['id']}/"
                        response = requests.get(post_url, headers={"Accept": "application/json"})
                        print(f"GET {post_url} - Status Code: {response.status_code}")
                        self.assertEqual(response.status_code, 200, f"Request to {post_url} failed with status code {response.status_code}")
                else:
                    print(f"No posts defined for feed: {feed_url}, skipping post retrieval verification.")

# To run the tests
if __name__ == '__main__':
    unittest.main()