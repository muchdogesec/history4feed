# Tests

## Setup

To test history4feed we use a Jekyll blog we've created for exactly this purpose.

https://github.com/muchdogesec/fakeblog123

You can clone this repo, and then setup with Github pages to get a blog running online that you can use.

```shell
python3 -m venv history4feed-venv
source history4feed-venv/bin/activate
# install requirements
pip3 install -r requirements.txt
````

## Automated Tests

### Check different feed formats

```shell
python3 -m unittest tests/test_01_add_fakeblog123_feeds.py
```

This contains 12 feed types, both ATOM and RSS feeds, all in three formats; 1) html encoded, 2) decoded, 3) with cdata tags.

The test;

1. deletes any old feeds that match those in the tests
2. adds the feeds
3. checks the jobs for the added feeds, until all are successful
4. checks each feed id

Note, because we use a UUIDv5 ID (namespace `6c6e6448-04d4-42a3-9214-4f0f7d02694e`) to generate IDs we can hardcode the IDs. For;

* blogs: UUID generated from namespace and the value `<URL OF BLOG>`
	* e.g. `https://muchdogesec.github.io/fakeblog123/feeds/rss-feed-encoded.xml` = `d1d96b71-c687-50db-9d2b-d0092d1d163a`
* posts: UUID generated from namespace and the value `<FEED_ID>+<POST_URL>+<POST_PUB_TIME>`
	* e.g. `d1d96b71-c687-50db-9d2b-d0092d1d163a+https://muchdogesec.github.io/fakeblog123///test3/2024/08/20/update-post.html+2024-08-20T10:00:00.000000Z` = `22173843-f008-5afa-a8fb-7fc7a4e3bfda`
	* Note `<POST_PUB_TIME>` is reported in seconds, we generate the value used in UUID generation with sub-seconds (e.g. `2024-08-20T10:00:00Z` -> `2024-08-20T10:00:00.000000Z`)

### Test 3rd party blog

```shell
python3 -m unittest tests/test_02_add_external_feeds.py
```

Tests a range of feed formats and URLs.

### Clean up

Note, you can clean up any old test data using this script which will delete ALL feeds (including those not included in test scripts);

```shell
python3 tests/delete_all_feeds.py
```

## Manual Tests

### Testing WayBack machine

We don't have the test blog indexed in WBM for testing, thus we need to test this using other blogs we don't own.

The following are good blogs to use because 1) they have a large archive, and 2) they are update regularly (to test live feed behaviour)

* https://www.grahamcluley.com/feed/ (this is also a great example of the inclusion of remote blogs in a feed)
