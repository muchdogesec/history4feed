import unittest
import requests
import time
from .base_test import BaseTest  # Ensure this import path is correct

class TestFeedProcessing(BaseTest):

    def delete_existing_feeds(self):
        """Deletes existing feeds from the API to ensure a clean state."""
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
                else:
                    print(f"Unexpected status code {response.status_code} when deleting feed ID {feed_id}.")
                    break

    def setUp(self):
        """Ensures that the DELETE operation runs before any test starts."""
        super().setUp()
        self.delete_existing_feeds()

    def test_post_feed_urls_and_check_jobs(self):
        """Tests adding feeds via POST requests, checks job status until success, and verifies post retrieval."""
        job_ids = []

        # Step 1: Post feeds and collect job IDs
        for feed_url in self.feeds.keys():
            with self.subTest(feed_url=feed_url):
                response = requests.post(
                    self.base_url,
                    json={
                        "url": feed_url,
                        "include_remote_blogs": False
                    },
                    headers={"Accept": "application/json"}  # Ensure the server responds with JSON
                )
                print(f"POST {self.base_url} - Feed URL: {feed_url} - Status Code: {response.status_code}")
                self.assertEqual(response.status_code, 200, f"Request to {self.base_url} failed with status code {response.status_code}")
                data = response.json()
                job_id = data.get("job_id")
                self.assertIsNotNone(job_id, f"Job ID not returned for URL {feed_url}")
                job_ids.append(job_id)

        # Step 2: Check the job status until it reaches "success"
        print("Checking job status until success...")
        for job_id in job_ids:
            job_url = f"http://localhost:8002/api/v1/jobs/{job_id}/"
            max_attempts = 20
            for attempt in range(max_attempts):
                response = requests.get(job_url, headers={"Accept": "application/json"})
                print(f"GET {job_url} - Status Code: {response.status_code} - Attempt {attempt + 1}/{max_attempts}")
                self.assertEqual(response.status_code, 200, f"Request to {job_url} failed with status code {response.status_code}")
                data = response.json()
                state = data.get("state")
                print(f"Job ID {job_id} - State: {state}")
                if state == "success":
                    break
                elif attempt < max_attempts - 1:
                    time.sleep(4)  # Wait before the next check
                else:
                    self.fail(f"Job ID {job_id} did not reach 'success' state after {max_attempts} attempts.")

        # Step 3: Verify that each post can be retrieved with a 200 OK response
        print("Verifying retrieval of posts...")
        for feed_id, posts in self.posts.items():
            for post in posts:
                post_url = f"http://localhost:8002/api/v1/feeds/{feed_id}/posts/{post['id']}/"
                response = requests.get(post_url, headers={"Accept": "application/json"})
                print(f"GET {post_url} - Status Code: {response.status_code}")
                self.assertEqual(response.status_code, 200, f"Request to {post_url} failed with status code {response.status_code}")

# To run the tests
if __name__ == '__main__':
    unittest.main()
