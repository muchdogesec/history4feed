import requests

# Define the base URL for the DELETE request
base_url = "http://127.0.0.1:8002/api/v1/feeds/"

# List of all feed IDs to be deleted
feed_ids = [
    "d1d96b71-c687-50db-9d2b-d0092d1d163a",
    "8f89731d-b9de-5931-9182-5460af59ca84",
    "c8592fca-aa7b-55b7-9664-886230d7c338",
    "e6178850-0b78-54cc-9f3e-85b482b84f2b",
    "8375e600-cc52-5823-8179-a8313ba9df5c",
    "2d6575b8-3d90-5479-bdfe-b980b753ec40",
    "2f21dfd2-e776-5d2b-ad3d-00460e540cca",
    "cb0ba709-b841-521a-a3f2-5e1429f4d366",
    "121e5557-7277-5aa3-945d-e466c6bf92d5",
    "66966023-522a-57af-93ac-88c6214e1891",
    "9c04d319-a949-52df-bcb6-5a73a1458fe5",
    "220ae197-f66f-56b3-a17a-cbfc6dc9661a"
]

# Iterate over the list of feed IDs and send a DELETE request for each
for feed_id in feed_ids:
    # Construct the full URL for the DELETE request
    url = f"{base_url}{feed_id}/"
    
    # Make the DELETE request and store the response
    response = requests.delete(url)
    
    # Check if the request was successful
    if response.status_code == 204:
        print(f"Successfully deleted feed with ID: {feed_id}")
    else:
        print(f"Failed to delete feed with ID: {feed_id}")
        print("Status Code:", response.status_code)
        print("Response:", response.text)
