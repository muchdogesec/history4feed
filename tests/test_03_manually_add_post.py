import unittest
import requests
import uuid
import time
import sys

class TestCrowdStrikeFeedProcessing(unittest.TestCase):
    
    def setUp(self):
        # Define the base URL for the API requests
        self.base_url = "http://127.0.0.1:8002/api/v1/feeds/"
        
        # Define the CrowdStrike feed URL to be tested
        self.feed_url = "https://www.crowdstrike.com/en-us/blog/feed"
        self.feed_data = {
            "include_remote_blogs": False,
            "id": "ecfdd2cb-9727-52c9-bf18-9266b2e2fd61"
        }
        
        # Namespace for UUIDv5
        self.namespace = uuid.UUID("6c6e6448-04d4-42a3-9214-4f0f7d02694e")

        # Call delete feed function before each test
        self.delete_feed()

    def delete_feed(self):
        """Deletes the CrowdStrike feed to ensure a clean state before testing."""
        delete_url = f"{self.base_url}{self.feed_data['id']}/"
        while True:
            response = requests.delete(delete_url)
            print(f"DELETE {delete_url} - Status Code: {response.status_code}")
            if response.status_code == 404:
                print(f"Feed ID {self.feed_data['id']} already deleted or not found.")
                break
            elif response.status_code == 204:
                print(f"Feed ID {self.feed_data['id']} deleted successfully.")
                break
            else:
                print(f"Unexpected status code {response.status_code} when deleting feed ID {self.feed_data['id']}.")
                break

    def generate_uuid(self, url):
        """Generates a UUIDv5 using the given URL and the defined namespace."""
        return str(uuid.uuid5(self.namespace, url))

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

    def test_crowdstrike_feed_and_post(self):
        """Test adding the CrowdStrike feed, checking job status, and adding a post."""

        # Step 1: Add the feed and check the job status
        feed_uuid = self.generate_uuid(self.feed_url)
        print(f"Generated UUID for {self.feed_url}: {feed_uuid}")
        
        post_data = {
            "url": self.feed_url,
            "include_remote_blogs": self.feed_data["include_remote_blogs"]
        }
        
        # Print the body of the POST request for debugging
        print(f"POST Request Body: {post_data}")
        sys.stdout.flush()  # Ensure the print is flushed to stdout
        
        # Post the feed with the required parameters
        response = requests.post(
            self.base_url,
            json=post_data,
            headers={"Accept": "application/json"}  # Ensure the server responds with JSON
        )
        
        print(f"POST {self.base_url} - Feed URL: {self.feed_url} - Status Code: {response.status_code}")
        
        # Check if the request was successful
        self.assertEqual(response.status_code, 201, f"Request to {self.base_url} failed with status code {response.status_code}")
        
        # Collect the response data
        data = response.json()
        
        # Verify that the returned UUID matches the generated UUID
        returned_uuid = data.get("id")
        self.assertEqual(returned_uuid, feed_uuid, f"Expected UUID {feed_uuid} but got {returned_uuid}")
        
        # Check the job status for adding the feed
        job_id = data.get("job_id")
        self.assertIsNotNone(job_id, "Job ID not returned in response")
        
        job_successful = self.check_job_status(job_id)
        self.assertTrue(job_successful, f"Job ID {job_id} for feed did not reach 'success' state after retries.")
        
        # Step 2: Add a post to the feed
        post_url = f"http://localhost:8002/api/v1/feeds/{self.feed_data['id']}/posts/"
        post_body = {
            "title": "COVID-19 Cyber Threats | Weekly Updates | CrowdStrike",
            "link": "https://www.crowdstrike.com/blog/covid-19-cyber-threats/",
            "pubdate": "2024-03-22T16:11:03.471Z",
            "author": "test",
            "categories": [
                "test"
            ]
        }
        
        # Print the body of the POST request for adding a post
        print(f"POST Request Body for Post: {post_body}")
        sys.stdout.flush()  # Ensure the print is flushed to stdout

        # Post the new feed entry
        post_response = requests.post(
            post_url,
            json=post_body,
            headers={"Accept": "application/json"}
        )
        
        print(f"POST {post_url} - Status Code: {post_response.status_code}")
        
        # Check if the post request was successful
        self.assertEqual(post_response.status_code, 201, f"Post request failed with status code {post_response.status_code}")
        
        # Collect the post response data and check job status
        post_data_response = post_response.json()
        post_job_id = post_data_response.get("id")  # Extract job ID from the 'id' key
        self.assertIsNotNone(post_job_id, "Job ID not returned in post response")
        
        post_job_successful = self.check_job_status(post_job_id)
        self.assertTrue(post_job_successful, f"Job ID {post_job_id} for post did not reach 'success' state after retries.")

# To run the tests
if __name__ == '__main__':
    unittest.main()