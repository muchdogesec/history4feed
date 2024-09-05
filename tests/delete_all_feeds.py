import requests

class FeedCleanup:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_all_feeds(self):
        """Fetches all feeds from the API."""
        url = f"{self.base_url}/feeds/"
        response = requests.get(url, headers={"Accept": "application/json"})
        if response.status_code == 200:
            feeds = response.json().get('feeds', [])
            print(f"Found {len(feeds)} feeds.")
            return feeds
        else:
            print(f"Failed to fetch feeds. Status code: {response.status_code}")
            return []

    def delete_feed(self, feed_id):
        """Deletes a feed by its ID."""
        url = f"{self.base_url}/feeds/{feed_id}/"
        response = requests.delete(url)
        if response.status_code == 204:
            print(f"Successfully deleted feed with ID: {feed_id}")
        elif response.status_code == 404:
            print(f"Feed with ID {feed_id} not found.")
        else:
            print(f"Failed to delete feed with ID {feed_id}. Status code: {response.status_code}")

    def cleanup_feeds(self):
        """Fetches and deletes all feeds."""
        feeds = self.get_all_feeds()
        for feed in feeds:
            feed_id = feed.get('id')
            if feed_id:
                self.delete_feed(feed_id)

if __name__ == "__main__":
    # Base URL for the API
    base_url = "http://localhost:8002/api/v1"

    # Create a FeedCleanup instance and perform cleanup
    cleanup = FeedCleanup(base_url)
    cleanup.cleanup_feeds()
