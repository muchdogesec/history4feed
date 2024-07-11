# history4feed

## Overview

It is common for feeds (RSS or XML) to only include a limited number of posts. I generally see the latest 3 - 5 posts of a blog in a feed. For blogs that have been operating for years, this means potentially thousands of posts are missed.

There is no way to page through historic articles using an RSS or ATOM feed (they were not designed for this), which means the first poll of the feed will only contain the limited number of articles in the feed. This limit is defined by the blog owner.

history4feed can be used to create a complete history for a blog and output it as an RSS feed.

history4feed offers an API interface that;

1. takes an RSS / ATOM feed URL
2. downloads a Wayback Machine archive for the feed
3. identified all unique blog posts in the historic feeds downloaded
4. downloads a HTML version of the article content on each page
5. stores the post record in the databases
6. exposes the posts as JSON or XML RSS

## tl;dr

[![history4feed](https://img.youtube.com/vi/z1ATbiecbg4/0.jpg)](https://www.youtube.com/watch?v=z1ATbiecbg4)

## Install

### Download and configure

```shell
# clone the latest code
git clone https://github.com/muchdogesec/history4feed
```

### Configuration options

history4feed has various settings that are defined in an `.env` file.

To create one using the default settings:

```shell
cp .env.example .env
```

#### Proxy

We strongly recommend using the ScrapFly proxy service with history4feed. Though we have no affiliation with them, it is the best proxy service we've tested and thus built in support for it to history4feed.

Once your signed up to [ScrapFly](https://scrapfly.io/) grab your API key and add it in the `.env` file under `SCRAPFILE_APIKEY=`

#### No proxy

If you're not using a Proxy it is very likely you'll run into rate limits on the WayBack Machine and the blogs you're requesting the full text from.

To try an alleviate this, you can set the following options in the `.env` file to avoid restrictions

* `WAYBACK_SLEEP_SECONDS`: This is useful when a large amount of posts are returned. This sets the time between each request to get the full text of the article to reduce servers blocking robotic requests.
* `REQUEST_RETRY_COUNT`: This is useful when a large amount of posts are returned. This sets the number of retries when a non-200 response is returned.

#### Backfill logic settings

The `.env` file also determines how far history4feed will backfill posts for newly added feeds using `EARLIEST_SEARCH_DATE`.

e.g. `EARLIEST_SEARCH_DATE=2020-01-01T00:00:00Z` will import all posts with a publish date >= `2020-01-01T00:00:00Z`

### Build the Docker Image

```shell
sudo docker-compose build
```

### Start the server

```shell
sudo docker-compose up
```

### Access the server

The webserver (Django) should now be running on: http://127.0.0.1:8000/

You can access the Swagger UI for the API in a browser at: http://127.0.0.1:8000/schema/swagger-ui/

#### Note on Django

The webserver is Django.

To create an admin user in Django

```shell
sudo docker-compose run django python manage.py createsuperuser
```

You can then access the admin dashboard via:

http://127.0.0.1:8000/admin

Note, if you intend on using this in production, you should also modify the variables in the `.env` file for `POSTGRES_USER`, `POSTGRES_PASS`, and `DJANGO_SECRET`.

## Useful supporting tools

* [An up-to-date list of threat intel blogs that post cyber threat intelligence research](https://github.com/muchdogesec/awesome_threat_intel_blogs)
* [Donate to the Wayback Machine](https://archive.org/donate)

## Support

[Minimal support provided via the DOGESEC community](https://community.dogesec.com/).

## License

[AGPLv3](/LICENSE).