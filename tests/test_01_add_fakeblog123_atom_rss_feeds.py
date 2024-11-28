import unittest
import requests
import time
import argparse


class BaseTest(unittest.TestCase):
    def setUp(self):
        # Define the base URL for the API requests
        self.base_url = "http://127.0.0.1:8002/api/v1/feeds/"

        # Feeds URLs, their corresponding feed IDs, descriptions, and feed types
        self.feeds = {
            # minimum required properties
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-encoded.xml": {
                "id": "d1d96b71-c687-50db-9d2b-d0092d1d163a", # not passed in request
                "feed_type": "rss", # not passed in request
                "include_remote_blogs": False
            },
            # custom title/description/pretty_url
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-decoded.xml": {
                "id": "cb0ba709-b841-521a-a3f2-5e1429f4d366", # not passed in request
                "feed_type": "atom", # not passed in request
                "pretty_url": "https://muchdogesec.github.io/fakeblog123/",
                "title": "Custom Title",
                "description": "Custom description",
                "include_remote_blogs": False
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-cdata.xml": {
                "id": "121e5557-7277-5aa3-945d-e466c6bf92d5", # not passed in request
                "feed_type": "atom", # not passed in request
                "include_remote_blogs": False
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-decoded.xml": {
                "id": "8f89731d-b9de-5931-9182-5460af59ca84", # not passed in request
                "feed_type": "rss", # not passed in request
                "include_remote_blogs": False
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-cdata.xml": {
                "id": "c8592fca-aa7b-55b7-9664-886230d7c338", # not passed in request
                "feed_type": "rss", # not passed in request
                "include_remote_blogs": False
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-encoded-partial.xml": {
                "id": "e6178850-0b78-54cc-9f3e-85b482b84f2b", # not passed in request
                "feed_type": "rss", # not passed in request
                "include_remote_blogs": False
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-decoded-partial.xml": {
                "id": "8375e600-cc52-5823-8179-a8313ba9df5c", # not passed in request
                "feed_type": "rss", # not passed in request
                "include_remote_blogs": False
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-cdata-partial.xml": {
                "id": "2d6575b8-3d90-5479-bdfe-b980b753ec40", # not passed in request
                "feed_type": "rss", # not passed in request
                "include_remote_blogs": False
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-encoded.xml": { 
                "id": "2f21dfd2-e776-5d2b-ad3d-00460e540cca", # not passed in request
                "feed_type": "atom", # not passed in request
                "include_remote_blogs": False
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-encoded-partial.xml": {
                "id": "66966023-522a-57af-93ac-88c6214e1891", # not passed in request
                "feed_type": "atom", # not passed in request
                "include_remote_blogs": False
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-decoded-partial.xml": {
                "id": "9c04d319-a949-52df-bcb6-5a73a1458fe5", # not passed in request
                "feed_type": "atom", # not passed in request
                "include_remote_blogs": False
            },
            "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-cdata-partial.xml": {
                "id": "220ae197-f66f-56b3-a17a-cbfc6dc9661a", # not passed in request
                "feed_type": "atom", # not passed in request
                "include_remote_blogs": False
            },
        }

class TestFeedProcessing(BaseTest):

    def delete_feeds(self, feed_id=None):
        """Deletes feeds to ensure a clean state."""
        if feed_id:
            # Delete only the specified feed
            feed_ids = [feed_id]
            print(f"Deleting only the feed with ID: {feed_id}")
        else:
            # Delete all feeds
            feed_ids = [details['id'] for details in self.feeds.values()]
            print("Deleting all feeds...")

        for fid in feed_ids:
            url = f"{self.base_url}{fid}/"
            while True:
                response = requests.delete(url)
                print(f"DELETE {url} - Status Code: {response.status_code}")
                if response.status_code == 404:
                    print(f"Feed ID {fid} already deleted or not found.")
                    break
                elif response.status_code == 204:
                    print(f"Feed ID {fid} deleted successfully.")
                    break
                else:
                    print(f"Unexpected status code {response.status_code} when deleting feed ID {fid}.")
                    break

    def setUp(self):
        """Ensures that the DELETE operation runs before any test starts."""
        super().setUp()
        if args.feed_url:
            # Delete only the feed corresponding to the specified feed URL
            feed_details = self.feeds.get(args.feed_url)
            if feed_details:
                self.delete_feeds(feed_id=feed_details['id'])
            else:
                print(f"Feed URL '{args.feed_url}' is not defined in the feeds dictionary.")
                raise ValueError(f"Invalid feed URL: {args.feed_url}")
        else:
            # Delete all feeds
            self.delete_feeds()

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
        """Tests adding feeds (all or a single one based on CLI input) and verifying job success."""
        feeds_to_test = {args.feed_url: self.feeds[args.feed_url]} if args.feed_url else self.feeds

        for feed_url, feed_details in feeds_to_test.items():
            with self.subTest(feed_url=feed_url):
                # Build the request body dynamically, excluding keys with None or missing values
                body = {
                    key: value
                    for key, value in {
                        "url": feed_url,
                        "include_remote_blogs": feed_details.get("include_remote_blogs"),
                        "pretty_url": feed_details.get("pretty_url"),
                        "title": feed_details.get("title"),
                        "description": feed_details.get("description"),
                    }.items()
                    if value is not None  # Exclude keys with None values
                }

                # Prepare the POST request to print its details
                session = requests.Session()
                request = requests.Request(
                    method="POST",
                    url=self.base_url,
                    json=body,
                    headers={"Accept": "application/json"}  # Ensure the server responds with JSON
                )
                prepared_request = session.prepare_request(request)

                # Print the full request for debugging
                print("\n--- POST Request Details ---")
                print(f"URL: {prepared_request.url}")
                print(f"Method: {prepared_request.method}")
                print(f"Headers: {prepared_request.headers}")
                print(f"Body: {prepared_request.body}")
                print("----------------------------\n")

                # Send the request
                response = session.send(prepared_request)
                print(f"POST {self.base_url} - Feed URL: {feed_url} - Status Code: {response.status_code}")
                self.assertEqual(response.status_code, 201, f"Request to {self.base_url} failed with status code {response.status_code}")

                # Collect the job ID
                data = response.json()
                job_id = data.get("job_id")
                print(f"Job ID {job_id} received for Feed URL: {feed_url}")
                self.assertIsNotNone(job_id, f"Job ID not returned for URL {feed_url}")

                # Wait for job to succeed
                job_successful = self.check_job_status(job_id)
                self.assertTrue(job_successful, f"Job ID {job_id} for URL {feed_url} did not reach 'success' state after 5 retries")

                # Validate the feed type via GET request
                feed_id = feed_details["id"]
                feed_url_get = f"{self.base_url}{feed_id}/"
                response = requests.get(feed_url_get, headers={"Accept": "application/json"})
                print(f"GET {feed_url_get} - Status Code: {response.status_code}")
                self.assertEqual(response.status_code, 200, f"Request to {feed_url_get} failed with status code {response.status_code}")

                feed_data = response.json()
                actual_feed_type = feed_data.get("feed_type")
                expected_feed_type = feed_details.get("feed_type")
                print(f"Validating feed type for Feed ID: {feed_id}")
                print(f"Expected feed type: {expected_feed_type}, Actual feed type: {actual_feed_type}")
                self.assertEqual(
                    actual_feed_type,
                    expected_feed_type,
                    f"Feed type mismatch for Feed ID {feed_id}. Expected: {expected_feed_type}, Actual: {actual_feed_type}"
                )


# Add argument parsing for CLI
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Test adding specific or all feed URLs with optional parameters.")
    parser.add_argument(
        "--feed-url",
        help="Specify the feed URL to add and test. If not provided, all feeds will be tested."
    )
    args, remaining_args = parser.parse_known_args()

    # Pass remaining args to unittest
    unittest.main(argv=["first-arg-is-ignored"] + remaining_args)