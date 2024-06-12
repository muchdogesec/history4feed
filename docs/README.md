## Basics of RSS

RSS stands for Really Simple Syndication. Simply put, RSS is a standardized format using a computer (and human) readable format that shows what has changed for a website, and is especially used by blogs, podcasts, news sites, etc, for this reason.

Here is a sample of an RSS feed from The Record by the Recorded Future team; `https://therecord.media/feed/`.

Note, in many cases a blog will clearly show their RSS (or ATOM) feed URL, but not all. Whilst not all blogs have RSS feeds, if you open up a browser, navigate to the blog, and click view page source, you can usually find the feed address under the `link rel="alternate" type="application/rss+xml"` or `application/atom+xml` HTML tag.

Here's an example...

```shell
curl "https://krebsonsecurity.com/" > demo_1.html
```

```html
<link rel="alternate" type="application/rss+xml" title="Krebs on Security &raquo; Feed" href="https://krebsonsecurity.com/feed/" />
<link rel="alternate" type="application/rss+xml" title="Krebs on Security &raquo; Comments Feed" href="https://krebsonsecurity.com/comments/feed/" />
```

Note, you might see more than one feed, above one is for posts, the other for blog comments.

It's not always that simple to detect the feed URL...

The Recorded Future Record RSS feed;

```shell
curl "https://therecord.media/news" > demo_2.html
```

Is nestled in custom properties...

```js
"rssLink":{"id":12,"target":"_blank","externalUrl":"https://therecord.media/feed/"
```

Sometimes a feed will exist, but is not exposed in the HTML (in which case you can try and guess the URL pattern for it). Some blogs just have no feeds.

In some cases, a blog will also have feeds per category (vs getting the entire blog, which you might not always want), which you can find using the category/tag/etc, URL. e.g.

```shell
curl "https://blogs.infoblox.com/category/cyber-threat-intelligence/" > demo_3.html
```

```html
<link rel="alternate" type="application/rss+xml" title="Infoblox Blog &raquo; Feed" href="https://blogs.infoblox.com/feed/" />
<link rel="alternate" type="application/rss+xml" title="Infoblox Blog &raquo; Comments Feed" href="https://blogs.infoblox.com/comments/feed/" />
<link rel="alternate" type="application/rss+xml" title="Infoblox Blog &raquo; Cyber Threat Intelligence Category Feed" href="https://blogs.infoblox.com/category/cyber-threat-intelligence/feed/" />
```

Generally an RSS feed has an XML structure containing at least the following items;

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">

<channel>
  <title>W3Schools Home Page</title>
  <link>https://www.w3schools.com</link>
  <description>Free web building tutorials</description>
  <item>
    <title>RSS Tutorial</title>
    <link>https://www.w3schools.com/xml/xml_rss.asp</link>
    <description>New RSS tutorial on W3Schools</description>
    <pubDate>Tue, 03 Jun 2003 09:39:21 GMT</pubDate>
  </item>
  <item>
    <title>XML Tutorial</title>
    <link>https://www.w3schools.com/xml</link>
    <description>New XML tutorial on W3Schools</description>
    <pubDate>Tue, 10 Jun 2003 11:34:12 GMT</pubDate>
  </item>
</channel>

</rss>
``` 

The `<channel>` tags capture the entire feed including metadata about the feed (`title`, `link`, and `description` in this case). There are many other optional elements that can be included in the `<channel>` tags, [as defined here](https://www.rssboard.org/rss-specification).

Each article in the feed is defined inside each `<item>` tag with sub-elements, generally the most important being:

* `title`: The title of the post / article
* `link`: The URL of the post / article
* `description`: The article content
* `pubDate`: The date the article was published

There are many other optional elements that can be included in the `<item>` tags, [as defined here](https://www.rssboard.org/rss-specification).

## Basics of ATOM

Atom is a similar format to RSS and used for the same reasons. It is a slightly newer format than XML (although almost 20 years old) and designed to cover some of the shortcomings of RSS.

Here is a sample of an ATOM feed from the 0patch blog...

```shell
curl "https://blog.0patch.com/" > demo_4.html
```

```html
<link rel="alternate" type="application/atom+xml" title="0patch Blog - Atom" href="https://blog.0patch.com/feeds/posts/default" />
<link rel="alternate" type="application/rss+xml" title="0patch Blog - RSS" href="https://blog.0patch.com/feeds/posts/default?alt=rss" />
<link rel="service.post" type="application/atom+xml" title="0patch Blog - Atom" href="https://www.blogger.com/feeds/7114610046316422325/posts/default" />
```

Note, an RSS version is also available above; `application/rss+xml` vs `application/atom+xml`.

An ATOM feed has a similar XML structure to RSS, however, you will notice some of the element names are different.

```xml
  <?xml version="1.0" encoding="utf-8"?>
   <feed xmlns="http://www.w3.org/2005/Atom">

     <title>Example Feed</title>
     <link href="http://example.org/"/>
     <updated>2003-12-13T18:30:02Z</updated>
     <author>
       <name>John Doe</name>
     </author>
     <id>urn:uuid:60a76c80-d399-11d9-b93C-0003939e0af6</id>

     <entry>
       <title>Atom-Powered Robots Run Amok</title>
       <link href="http://example.org/2003/12/13/atom03"/>
       <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
       <published>2003-12-13T18:30:02Z</published>
       <updated>2003-12-13T18:30:02Z</updated>
       <title>Something</title>
       <content>Some text.</content>
     </entry>
   </feed>
```

The blog information is captured at the top of the document.

Each article in the feed is defined inside each `<entry>` tag with sub-elements, generally the most important being:

* `title`: The title of the post / article
* `id`: The UUID of the post
* `link`: The URL of the post / article
* `published`: The date the article was published
* `content`: The article content

There are many other optional elements that can be included in the `<item>` tags, [as defined here](https://validator.w3.org/feed/docs/atom.html).

## The solution

There are two ways I came up with to get historic posts from a blog;

1. Scrape the blog for historic posts. This is the most accurate way to do it, though given the different structure of blogs and websites, this can become complex, requiring a fair bit of manual scraping logic to be written for each blog you want to follow
2. [Inspired by this Reddit thread](https://www.reddit.com/r/webscraping/comments/zxduid/python_library_to_scrape_rssfeeds_from/), use the Wayback Machine's archive. Often the Wayback Machine will have captured snapshots of a feed (though not always). For example, `https://therecord.media/feed/` has been captured [187 times between November 1, 2020 and August 12, 2022](https://web.archive.org/web/20220000000000*/https://therecord.media/feed/).

Whilst the Wayback Machine will completely miss some blog archives, a particular problem for smaller sites that are less likely to be regularly indexed by the WBM), and potentially miss certain feed items where the RSS feed updates faster the WBM re-indexes the site, I chose this approach as it is currently the most scalable way I could come up with to backfill history (and most of the requirements for my use-cases were from high profile sites with a fairly small publish rate).

[Waybackpack](https://github.com/jsvine/waybackpack) is a command-line tool that lets you download the entire Wayback Machine archive for a given URL for this purpose.

Here is an example of how to use it with The Record Feed;

```shell
python3 -m venv tutorial_env
source tutorial_env/bin/activate
pip3 install waybackpack
waybackpack https://therecord.media/feed/ -d ~/Downloads/therecord_media_feed --from-date 2015 --uniques-only  
```

In the above command I am requesting all unique feed pages downloaded by the Wayback Machine (`--uniques-only `) from 2015 (`--from-date 2015`) from the feed URL (`https://therecord.media/feed/`)

Which produces about 100 unique `index.html` files (where `index.html` is the actual RSS feed). They are nested in folders named with the index datetime (time captured by WBM) in the format `YYYYMMDDHHMMSS` like so;

```

~/Downloads/therecord_media_feed
├── 20220808162900
│   └── therecord.media
│       └── feed
│           └── index.html
├── 20220805213430
│   └── therecord.media
│       └── feed
│           └── index.html
...
└── 20201101220102
    └── therecord.media
        └── feed
            └── index.html
```

It is important to point out unique entries just mean the `index.html` files have at least one difference. That is to say, much of the file can actually be the same (and include the same articles). Also whilst saved as .html documents, the content is actually pure .xml.

Take `20220808162900 > therecord.media > index.html` and `20220805213430 > therecord.media > index.html`

Both of these files contain the same item;

```xml
<item>
    <title>Twitter confirms January breach, urges pseudonymous accounts to not add email or phone number</title>
    <link>https://therecord.media/twitter-confirms-january-breach-urges-pseudonymous-accounts-to-not-add-email-or-phone-number/</link>
```

history4feed looks at all unique `<link>` elements in the downloaded `index.html` files to find the unique `<items>`s.

Note, this blog is in RSS format. 

Here's another example, this time using an ATOM feed as an example;

```shell
waybackpack https://www.schneier.com/feed/atom/ -d ~/Downloads/schneier_feed --from-date 2015 --uniques-only  
```

Looking at a snippet from one of the `index.html` files;

```xml
    <entry>
        <author>
            <name>Bruce Schneier</name>
        </author>
        <title type="html"><![CDATA[Friday Squid Blogging: Vegan Chili Squid]]></title>
        <link rel="alternate" type="text/html" href="https://www.schneier.com/blog/archives/2021/01/friday-squid-blogging-vegan-chili-squid.html" />
        <id>https://www.schneier.com/?p=60711</id>
        <updated>2021-01-04T16:50:54Z</updated>
        <published>2021-01-22T22:19:15Z</published>
```

Here, history4feed looks at the `<link href` value to find the unique entries between each `index.html`.

## Dealing with partial content in feeds

The `description` field (in RSS feeds) and `content` field (in ATOM feeds) can contain the entirety of the raw article, including the html formatting. You can see this in The Record's RSS feed. Sometime the HTML content is decoded or encoded.

However, some blogs choose to use snippets in their RSS feed content. For example, choosing only to include the first paragraph - requiring a subscriber to read the full content outside of their feed aggregator.

I wanted to include a full-text feed in the historical output created by history4feed.

To do this, once a historical feed is created, the feed is passed to the [readability-lxml library](https://pypi.org/project/readability-lxml/).

history4feed takes all the source URLs (either `<entry.link href>` property value (ATOM) in or `<item.link>` tags (RSS)) for the articles in the feeds and passes them to readability-lxml.

The result is then reprinted in the `description` or `content` field depending on feed type, overwriting the potentially partial content that it originally contained.

Note, history4feed cannot detect if a feed is full or partial so will always request the full content for all items via readability-lxml, regardless of whether the feed content is partial or full.

## Dealing with encoding in post content

For ATOM properties;

* `title`: The title of the post / article
* `description`: The article content

And for RSS properties;

* `title`: The title of the post / article
* `content`: The article content

The data is typically printed in one of three ways, either;

* Encoded: e.g. contains `&gt` vs `>`
* Decoded Raw: standard HTML tags
* Decoded CDATA: the actual Decoded Raw HTML is inside `<![CDATA[Decoded Raw HTML]]>` tags

As an example, endcoded

```html
&gt;img src=&quot;https://cms.therecord.media/uploads/2023_0706_Ransomware_Tracker_Most_Prolific_Groups_6a567c11da.jpg&quot;&lt;
```

Which as decoded raw html looks as follows

```html
<img src="https://cms.therecord.media/uploads/2023_0706_Ransomware_Tracker_Most_Prolific_Groups_6a567c11da.jpg">
```

Which as decoded CDATA looks like

```html
<![CDATA[<img src="https://cms.therecord.media/uploads/2023_0706_Ransomware_Tracker_Most_Prolific_Groups_6a567c11da.jpg">]]>
```

In the responses provided by history4feed, the XML endpoint will return encoded HTML, the JSON response will return decoded HTML.

## Live feed data (data not from WBM)

In addition to the historical feed information pulled by the Wayback Machine, history4feed also includes the latest posts in the live feed URL.

Live feed data always takes precedence. history4feed will remove duplicate entries found in the Wayback Machine response also present in the live feed, and will instead use the live feed version by default.

## Rebuilding the feed (for output XML API output)

history4feed stores data in the database as JSON.

However, to support an RSS XML API endpoint (that can be used with a feed reader), history4feed converts all feeds and their content into a single RSS formatted XML file at request time.

RSS is always the output, regardless of wether input was ATOM or RSS.

The RSS files for each feed contain a simplified header;

```xml
<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
        <channel>
            <title>CHANNEL.TITLE (RSS) / FEED.TITLE (ATOM)</title>
            <description>CHANNEL.DESCRIPTION (RSS) / FEED.SUBTITLE (ATOM)</description>
            <link>FEED URL ENTERED BY USER</link>
            <lastBuildDate>SCRIPT EXECUTION TIME</lastBuildDate>
            <generator>https://www.github.com/history4feed</generator>
            <ITEMS></ITEMS>
        </channel>
    </rss>
```

Each item the be printed between `<ITEMS></ITEMS>` tags is rebuilt as follows;

```xml
            <item>
                <title>CHANNEL.ITEM.TITLE (RSS) / FEED.ENTRY.TITLE (ATOM)</title>
                <description>CHANNEL.ITEM.DESCRIPTION (RSS) / FEED.ENTRY.CONTENT (ATOM) EITHER ENCODED OR DECODED BASED ON USER SETTING -- THIS IS THE FULL BLOG POST AFTER FULL TEXT EXTRACTED</description>
                <link>CHANNEL.ITEM.LINK (RSS) / FEED.ENTRY.LINK (ATOM)</link>
                <pubDate>CHANNEL.ITEM.PUBDATE (RSS) / FEED.ENTRY.PUBLISHED (ATOM)</pubDate>
                <author>CHANNEL.ITEM.AUTHOR (RSS) / FEED.ENTRY.AUTHOR (ATOM)</author>
                <category>CHANNEL.ITEM.CATERGORY [N] (RSS) / FEED.ENTRY.CATEGORY [N] (ATOM)</category>
                <category>CHANNEL.ITEM.CATERGORY [N] (RSS) / FEED.ENTRY.CATEGORY [N] (ATOM)</category>
            </item>
```

## Dealing with feed validation on input

ATOM feeds are XML documents. ATOM feeds can be validated by checking for the header tags where `<feed` tag contains the text `atom` somewhere inside it, e.g. https://www.schneier.com/feed/atom/

RSS feeds are very similar to ATOM in many ways. RSS feeds can be validated as they contain an `<rss>` tag in the header of the document. e.g. https://www.hackread.com/feed/

Feeds are validated to ensure they contain this data before any processing is carries out.

For example, the source of https://github.com/signalscorps/history4feed/ does not show an RSS or ATOM feed, so would return an error.

## Dealing with IP throttling during full text requests

Many sites will stop robotic request to their content. As the full text function of history4feed relies on accessing each blog post individually this can result in potentially thousands of requests to the Wayback Machine and which have a high risk of being blocked.

history4feed has two potential workarounds to solve this problem;

### 1. Use a proxy

history4feed supports the use of [ScrapFly](https://scrapfly.io/).

This is a paid service ([with a free tier](https://scrapfly.io/pricing)). In my own research, its the best proxy for web scraping.

You will need to register for an account and grab your API key.

Note, due to many site blocking access to Russian IPs, the request includes the following proxy locations only;

```shell
country=us,ca,mx,gb,fr,de,au,at,be,hr,cz,dk,ee,fi,ie,se,es,pt,nl
```

### 2. Use inbuilt app settings

It's best to request only what you need, and also slow down the rate at which the content is requested (so the request look more like a human).

history4feed supports the following options;

* sleep times: sets the time between each request to get the full post text
* time range: an earliest and latest post time can be set, reducing the number of items returned in a single script run. Similarly, you can reduce the content by ignoring entries in the live feed.
* retries: by default, when in full text mode history4feed will retry the page a certain number of times in case of error. If it still fails after retries count reached, the script will fail. You can change the retries as you require.

## A note on error handling

Due to the way old feeds are pulled from WBM, it is likely some will now be deleted (404s). Similarly, the site might reject requests (403's -- see proxy use as a solution to this).

history4feed will soft handle these errors and log the failure, including the HTTP status code and the particular URL that failed. You can view the logs for each run in the `logs/` directory.

This means that if it's required you can go back and get this post manually. However, one limitation of soft error handling is you won't be able to do this using the same history4feed install though.