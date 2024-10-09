import unittest
import requests
import uuid
import time
import sys  # For stdout flush

class TestBlogFeedProcessing(unittest.TestCase):
    
    def setUp(self):
        # Define the base URL for the API requests
        self.base_url = "http://127.0.0.1:8002/api/v1/feeds/"
        
        # Define the blog URLs to be tested
        self.blog_urls = {
            "http://feeds.feedburner.com/Unit42": {
                "include_remote_blogs": True,
                "id": "b4e3f13c-0ad6-5abe-be01-2475d341bf84"
            },
            "https://unit42.paloaltonetworks.com/category/threat-research/feed/": {
                "include_remote_blogs": False,
                "id": "16341792-226e-5a55-829e-a7cbcd2d54af"
            },
            "https://www.crowdstrike.com/en-us/blog/feed": {
                "include_remote_blogs": False,
                "id": "ecfdd2cb-9727-52c9-bf18-9266b2e2fd61"
            }
        }
        
        # Namespace for UUIDv5
        self.namespace = uuid.UUID("6c6e6448-04d4-42a3-9214-4f0f7d02694e")

        # Call delete feeds function before each test
        self.delete_existing_feeds()

    def delete_existing_feeds(self):
        """Deletes feeds defined in self.blog_urls to ensure a clean state before testing."""
        print("Starting deletion of existing feeds...")
        for blog_url, details in self.blog_urls.items():
            feed_id = details['id']
            delete_url = f"{self.base_url}{feed_id}/"
            while True:
                response = requests.delete(delete_url)
                print(f"DELETE {delete_url} - Status Code: {response.status_code}")
                if response.status_code == 404:
                    print(f"Feed ID {feed_id} already deleted or not found.")
                    break
                elif response.status_code == 204:
                    print(f"Feed ID {feed_id} deleted successfully.")
                    break
                else:
                    print(f"Unexpected status code {response.status_code} when deleting feed ID {feed_id}.")
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

    def test_blog_urls(self):
        """Test adding blog URLs with the correct parameters, UUID generation, and job processing."""
        
        for blog_url, options in self.blog_urls.items():
            with self.subTest(blog_url=blog_url):
                # Generate UUIDv5 for the feed
                feed_uuid = self.generate_uuid(blog_url)
                print(f"Generated UUID for {blog_url}: {feed_uuid}")
                
                # Define the POST data
                post_data = {
                    "url": blog_url,
                    "include_remote_blogs": options["include_remote_blogs"]
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
                
                print(f"POST {self.base_url} - Blog URL: {blog_url} - Status Code: {response.status_code}")
                
                # Check if the request was successful
                self.assertEqual(response.status_code, 201, f"Request to {self.base_url} failed with status code {response.status_code}")
                
                # Collect the response data
                data = response.json()
                
                # Verify that the returned UUID matches the generated UUID
                returned_uuid = data.get("id")
                self.assertEqual(returned_uuid, feed_uuid, f"Expected UUID {feed_uuid} but got {returned_uuid}")

                # Step 2: Wait for the job to succeed (retry 5 times with 30-second delay)
                job_id = data.get("job_id")
                self.assertIsNotNone(job_id, "Job ID not returned in response")
                
                job_successful = self.check_job_status(job_id)
                self.assertTrue(job_successful, f"Job ID {job_id} for URL {blog_url} did not reach 'success' state after retries.")

# To run the tests
if __name__ == '__main__':
    unittest.main()
