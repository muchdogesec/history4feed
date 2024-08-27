import requests

# Define the base URL for the POST request
base_url = "http://127.0.0.1:8002/api/v1/feeds/"

# List of all URLs to be posted
urls = [
    "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-encoded.xml", # d1d96b71-c687-50db-9d2b-d0092d1d163a
    "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-decoded.xml", # 8f89731d-b9de-5931-9182-5460af59ca84
    "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-cdata.xml", # c8592fca-aa7b-55b7-9664-886230d7c338
    "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-encoded-partial.xml", # e6178850-0b78-54cc-9f3e-85b482b84f2b
    "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-decoded-partial.xml", # 8375e600-cc52-5823-8179-a8313ba9df5c
    "https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-cdata-partial.xml", # 2d6575b8-3d90-5479-bdfe-b980b753ec40
    "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-encoded.xml", # 2f21dfd2-e776-5d2b-ad3d-00460e540cca
    "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-decoded.xml", # cb0ba709-b841-521a-a3f2-5e1429f4d366
    "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-cdata.xml", # 121e5557-7277-5aa3-945d-e466c6bf92d5
    "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-encoded-partial.xml", # 66966023-522a-57af-93ac-88c6214e1891
    "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-decoded-partial.xml", # 9c04d319-a949-52df-bcb6-5a73a1458fe5
    "https://muchdogesec.github.io/fakeblog123/feeds/atom-feed-cdata-partial.xml" # 220ae197-f66f-56b3-a17a-cbfc6dc9661a
]

# Iterate over the list of URLs and send a POST request for each
for url in urls:
    # Define the JSON body to be sent in the request
    data = {
        "url": url,
        "include_remote_blogs": False
    }
    
    # Make the POST request and store the response
    response = requests.post(base_url, json=data)
    
    # Check if the request was successful
    if response.status_code == 200:
        print(f"Request was successful for URL: {url}")
        print("Response JSON:", response.json())
    else:
        print(f"Failed to make the request for URL: {url}")
        print("Status Code:", response.status_code)
        print("Response:", response.text)
