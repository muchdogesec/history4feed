# Tests

### Testing full text lookup

To test history4feed we use a Jekyll blog we've created for exactly this purpose.

https://github.com/muchdogesec/fakeblog123

This contains both ATOM and RSS feeds, all in three formats; 1) html encoded, 2) decoded, 3) with cdata tags.

You can use the `add_fakeblog123_feeds.py` script to add these to the history4feed (when the app is running).

From the root of this code run;

```shell
python3 tests/add_fakeblog123_feeds.py
```

Note, because we use a UUIDv5 IDs we know the IDs that will be generated (UUID generated from namespace; `6c6e6448-04d4-42a3-9214-4f0f7d02694e` and the value `<URL OF BLOG>`).

### Testing WayBack machine

We don't have the test blog indexed in WBM for testing, thus we need to test this using other blogs we don't own.

The following are good blogs to use because 1) they have a large archive, and 2) they are update regularly (to test live feed behaviour)

* https://www.grahamcluley.com/feed/ (this is also a great example of the inclusion of remote blogs in a feed)

