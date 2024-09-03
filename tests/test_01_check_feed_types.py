import unittest
import requests
from unittest.mock import patch
import time

class TestFeedAPI(unittest.TestCase):

    def setUp(self):
        # Define the base URL for the API requests
        self.base_url = "http://127.0.0.1:8002/api/v1/feeds/"
        self.job_base_url = "http://127.0.0.1:8002/api/v1/jobs/"

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

        # This dictionary will store the job_ids for each feed
        self.job_ids = {}

    @patch('requests.post')
    def test_add_feeds(self, mock_post):
        # Mock the POST request to return a success status (200) and a job_id
        def mock_post_side_effect(url, json):
            feed_info = next(feed for feed_url, feed in self.feeds.items() if feed_url == json['url'])
            job_id = f"{feed_info['id']}-job"
            response = requests.Response()
            response.status_code = 200
            response._content = str.encode(f'''
            {{
                "description": "{feed_info["description"]}",
                "title": "Your awesome title",
                "feed_type": "{feed_info["feed_type"]}",
                "url": "{json["url"]}",
                "job_state": "pending",
                "id": "{feed_info['id']}",
                "job_id": "{job_id}"
            }}
            ''')
            return response

        mock_post.side_effect = mock_post_side_effect

        # Iterate over the feeds and send a POST request for each URL
        for url, feed_info in self.feeds.items():
            data = {
                "url": url,
                "include_remote_blogs": False
            }
            
            # Make the POST request
            response = requests.post(self.base_url, json=data)
            
            # Extract the job_id and store it
            job_id = response.json()['job_id']
            self.job_ids[feed_info['id']] = job_id
            
            # Check if the request was successful
            self.assertEqual(response.status_code, 200, f"POST request failed for URL: {url}")

    @patch('requests.get')
    def test_check_job_status(self, mock_get):
        # Expected URLs to be retrieved
        expected_urls = [
            "https://muchdogesec.github.io/fakeblog123/test3/2024/08/20/update-to-post-1.html",
            "https://muchdogesec.github.io/fakeblog123/test3/2024/08/07/testing-extractions-1.html",
            "https://muchdogesec.github.io/fakeblog123/test2/2024/08/05/testing-markdown-elements-1.html",
            "https://muchdogesec.github.io/fakeblog123/test1/2024/08/01/real-post-example-1.html"
        ]
        
        # Mock the GET request to check job status
        def mock_get_side_effect(url):
            job_id = url.split('/')[-2]
            feed_id = next(feed_id for feed_id, job in self.job_ids.items() if job == job_id)
            response = requests.Response()
            response.status_code = 200
            response._content = str.encode(f'''
            {{
                "id": "{job_id}",
                "count_of_items": 0,
                "feed_id": "{feed_id}",
                "urls": {{
                    "retrieved": {expected_urls},
                    "skipped": [],
                    "failed": [],
                    "retrieving": []
                }},
                "state": "success",
                "run_datetime": "2024-09-03T06:00:22.270278Z",
                "earliest_item_requested": "2020-01-01T00:00:00Z",
                "latest_item_requested": "2024-09-03T06:00:22.269823Z",
                "info": ""
            }}
            ''')
            return response

        mock_get.side_effect = mock_get_side_effect

        # Check the job status for each job_id until all jobs are successful
        for feed_id, job_id in self.job_ids.items():
            job_url = f"{self.job_base_url}{job_id}/"
            success = False

            while not success:
                response = requests.get(job_url)
                job_status = response.json()
                
                # Check if the job state is successful and the retrieved URLs match the expected list
                if job_status['state'] == 'success' and set(job_status['urls']['retrieved']) == set(expected_urls):
                    success = True
                else:
                    time.sleep(1)  # Wait before checking again

            # Final assertion to ensure the job was successful and URLs were retrieved
            self.assertTrue(success, f"Job {job_id} for feed {feed_id} did not complete successfully.")

    @patch('requests.get')
    def test_verify_feeds(self, mock_get):
        # Mock the GET request to return the expected feed information
        for url, feed_info in self.feeds.items():
            feed_id = feed_info["id"]
            description = feed_info["description"]
            feed_type = feed_info["feed_type"]
            get_url = f"{self.base_url}{feed_id}/"

            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "id": feed_id,
                "url": url,
                "count_of_posts": 4,  # Mocking count_of_posts to be 4 for each
                "title": "Your awesome title",
                "description": description,
                "earliest_item_pubdate": None,
                "latest_item_pubdate": None,
                "datetime_added": "2024-09-03T05:13:03.126167Z",
                "feed_type": feed_type,
                "include_remote_blogs": False
            }

            get_response = requests.get(get_url)
            self.assertEqual(get_response.status_code, 200, f"GET request failed for feed ID: {feed_id}")

            # Check that the URL, ID, description, feed_type, and count_of_posts match what we expect
            response_data = get_response.json()
            self.assertEqual(response_data['id'], feed_id, f"ID mismatch for feed ID: {feed_id}")
            self.assertEqual(response_data['url'], url, f"URL mismatch for feed ID: {feed_id}")
            self.assertEqual(response_data['description'], description, f"Description mismatch for feed ID: {feed_id}")
            self.assertEqual(response_data['feed_type'], feed_type, f"Feed type mismatch for feed ID: {feed_id}")
            self.assertEqual(response_data['count_of_posts'], 4, f"count_of_posts mismatch for feed ID: {feed_id}")

    @patch('requests.delete')
    def test_delete_feeds(self, mock_delete):
        # Mock the DELETE request to always return a success status (204)
        mock_delete.return_value.status_code = 204

        # Iterate over the feeds and send a DELETE request for each feed ID
        for feed_info in self.feeds.values():
            feed_id = feed_info["id"]
            delete_url = f"{self.base_url}{feed_id}/"
            
            # Make the DELETE request
            delete_response = requests.delete(delete_url)
            
            # Check if the DELETE request was successful
            self.assertEqual(delete_response.status_code, 204, f"DELETE request failed for feed ID: {feed_id}")

# To actually run the tests if this script is executed
if __name__ == "__main__":
    unittest.main()
