rss_example = """
<rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
    <channel>
        <title>Your awesome title</title>
        <description>RSS -- Contains encoded html -- PARTIAL CONTENT ONLY</description>
        <link>https://muchdogesec.github.io/fakeblog123/</link>
        <item>
            <title>Obstracts AI relationship generation test 2</title>
            <description>Also useful for Obstracts testing</description>
            <pubDate>Sun, 01 Sep 2024 08:00:00 +0000</pubDate>
            <link>
                https://muchdogesec.github.io/fakeblog123///test1/2024/09/01/same-ioc-across-posts.html</link>
            <guid isPermaLink="true">
                https://muchdogesec.github.io/fakeblog123///test1/2024/09/01/same-ioc-across-posts.html</guid>
            <author>David G</author>
            <category>Blog</category>
            <category>Test</category>
        </item>
        <item>
            <title>Obstracts AI relationship generation test</title>
            <description>Useful for Obstracts testing</description>
            <pubDate>Fri, 23 Aug 2024 08:00:00 +0000</pubDate>
            <link>
                https://muchdogesec.github.io/fakeblog123///test1/2024/08/23/obstracts-ai-relationships.html</link>
            <guid isPermaLink="true">
                https://muchdogesec.github.io/fakeblog123///test1/2024/08/23/obstracts-ai-relationships.html</guid>
            <author>David G</author>
            <category>Blog</category>
            <category>Test</category>
        </item>
        <item>
            <title>Update this post for testing updates to posts</title>
            <description>Mainly the patch endpoint on h4f</description>
            <pubDate>Tue, 20 Aug 2024 10:00:00 +0000</pubDate>
            <link>https://muchdogesec.github.io/fakeblog123///test3/2024/08/20/update-to-post-1.html</link>
            <guid isPermaLink="true">
                https://muchdogesec.github.io/fakeblog123///test3/2024/08/20/update-to-post-1.html</guid>
            <author>David G</author>
            <category>Blog</category>
            <category>Test</category>
        </item>
        <item>
            <title>Testing Extractions 1</title>
            <description>lots of iocs</description>
            <pubDate>Wed, 07 Aug 2024 08:00:00 +0000</pubDate>
            <link>
                https://muchdogesec.github.io/fakeblog123///test2/2024/08/07/testing-extractions-1.html</link>
            <guid isPermaLink="true">
                https://muchdogesec.github.io/fakeblog123///test2/2024/08/07/testing-extractions-1.html</guid>
            <author>David G</author>
            <category>Blog</category>
            <category>Test</category>
        </item>
        <item>
            <title>Testing Markdown Elements</title>
            <description>Nearly all Markdown applications support the basic syntax outlined in the
                original Markdown design document.</description>
            <pubDate>Mon, 05 Aug 2024 08:00:00 +0000</pubDate>
            <link>
                https://muchdogesec.github.io/fakeblog123///test2/2024/08/05/testing-markdown-elements-1.html</link>
            <guid isPermaLink="true">
                https://muchdogesec.github.io/fakeblog123///test2/2024/08/05/testing-markdown-elements-1.html</guid>
            <author>David G</author>
            <category>Blog</category>
            <category>Test</category>
        </item>
        <item>
            <title>Real Post Example - Fighting Ursa Luring Targets With Car for Sale</title>
            <description>A Russian threat actor we track as Fighting Ursa.</description>
            <pubDate>Thu, 01 Aug 2024 08:00:00 +0000</pubDate>
            <link>
                https://muchdogesec.github.io/fakeblog123///test1/2024/08/01/real-post-example-1.html</link>
            <guid isPermaLink="true">
                https://muchdogesec.github.io/fakeblog123///test1/2024/08/01/real-post-example-1.html</guid>
            <author>David G</author>
            <category>Blog</category>
            <category>Test</category>
        </item>
    </channel>
</rss>
"""

atom_example = """
<feed xmlns="http://www.w3.org/2005/Atom">
    <generator uri="https://jekyllrb.com/" version="4.3.3">Jekyll</generator>
    <link href="https://muchdogesec.github.io/fakeblog123//feeds/atom-feed-cdata-partial.xml"
        rel="self" type="application/atom+xml" />
    <link href="https://muchdogesec.github.io/fakeblog123/" rel="alternate" type="text/html" />
    <updated>2024-08-27T10:17:18+01:00</updated>
    <id>https://muchdogesec.github.io/fakeblog123//feed.xml</id>
    <title type="html">Your awesome title</title>
    <subtitle>ATOM -- Contains decoded html inside CDATA tags -- PARTIAL CONTENT ONLY</subtitle>
    <author>
        <name>David G</name>
    </author>
    <entry>
        <link
            href="https://muchdogesec.github.io/fakeblog123///test1/2024/09/01/same-ioc-across-posts.html"
            rel="alternate" type="text/html" title="Obstracts AI relationship generation test 2" />
        <published>Sun, 01 Sep 2024 08:00:00 +0000</published>
        <updated>Sun, 01 Sep 2024 08:00:00 +0000</updated>
        <id>https://muchdogesec.github.io/fakeblog123///test1/2024/09/01/same-ioc-across-posts.html</id>
        <title>
    <![CDATA[ Obstracts AI relationship generation test 2 ]]>
    </title>
        <summary>
    <![CDATA[ Also useful for Obstracts testing ]]>
    </summary>
        <content>
    <![CDATA[ Also useful for Obstracts testing ]]>
    </content>
        <author>
            <name>David G</name>
            <name>G David</name>
        </author>
        <category term="Blog" />
        <category term="Test" />
    </entry>
    <entry>
        <link
            href="https://muchdogesec.github.io/fakeblog123///test1/2024/08/23/obstracts-ai-relationships.html"
            rel="alternate" type="text/html" title="Obstracts AI relationship generation test" />
        <published>Fri, 23 Aug 2024 08:00:00 +0000</published>
        <updated>Fri, 23 Aug 2024 08:00:00 +0000</updated>
        <id>
            https://muchdogesec.github.io/fakeblog123///test1/2024/08/23/obstracts-ai-relationships.html</id>
        <title>
    <![CDATA[ Obstracts AI relationship generation test ]]>
    </title>
        <summary>
    <![CDATA[ Useful for Obstracts testing ]]>
    </summary>
        <content>
    <![CDATA[ Useful for Obstracts testing ]]>
    </content>
        <author>
            <name>David G</name>
            <name>G David</name>
        </author>
        <category term="Blog" />
        <category term="Test" />
    </entry>
    <entry>
        <link
            href="https://muchdogesec.github.io/fakeblog123///test3/2024/08/20/update-to-post-1.html"
            rel="alternate" type="text/html" title="Update this post for testing updates to posts" />
        <published>Tue, 20 Aug 2024 10:00:00 +0000</published>
        <updated>Tue, 20 Aug 2024 10:00:00 +0000</updated>
        <id>https://muchdogesec.github.io/fakeblog123///test3/2024/08/20/update-to-post-1.html</id>
        <title>
    <![CDATA[ Update this post for testing updates to posts ]]>
    </title>
        <summary>
    <![CDATA[ Mainly the patch endpoint on h4f ]]>
    </summary>
        <content>
    <![CDATA[ Mainly the patch endpoint on h4f ]]>
    </content>
        <author>
            <name>David G</name>
            <name>G David</name>
        </author>
        <category term="Blog" />
        <category term="Test" />
    </entry>
    <entry>
        <link
            href="https://muchdogesec.github.io/fakeblog123///test2/2024/08/07/testing-extractions-1.html"
            rel="alternate" type="text/html" title="Testing Extractions 1" />
        <published>Wed, 07 Aug 2024 08:00:00 +0000</published>
        <updated>Wed, 07 Aug 2024 08:00:00 +0000</updated>
        <id>https://muchdogesec.github.io/fakeblog123///test2/2024/08/07/testing-extractions-1.html</id>
        <title>
    <![CDATA[ Testing Extractions 1 ]]>
    </title>
        <summary>
    <![CDATA[ lots of iocs ]]>
    </summary>
        <content>
    <![CDATA[ lots of iocs ]]>
    </content>
        <author>
            <name>David G</name>
            <name>G David</name>
        </author>
        <category term="Blog" />
        <category term="Test" />
    </entry>
    <entry>
        <link
            href="https://muchdogesec.github.io/fakeblog123///test2/2024/08/05/testing-markdown-elements-1.html"
            rel="alternate" type="text/html" title="Testing Markdown Elements" />
        <published>Mon, 05 Aug 2024 08:00:00 +0000</published>
        <updated>Mon, 05 Aug 2024 08:00:00 +0000</updated>
        <id>
            https://muchdogesec.github.io/fakeblog123///test2/2024/08/05/testing-markdown-elements-1.html</id>
        <title>
    <![CDATA[ Testing Markdown Elements ]]>
    </title>
        <summary>
    <![CDATA[ Nearly all Markdown applications support the basic syntax outlined in the original Markdown design document. ]]>
    </summary>
        <content>
    <![CDATA[ Nearly all Markdown applications support the basic syntax outlined in the original Markdown design document. ]]>
    </content>
        <author>
            <name>David G</name>
            <name>G David</name>
        </author>
        <category term="Blog" />
        <category term="Test" />
    </entry>
    <entry>
        <link
            href="https://muchdogesec.github.io/fakeblog123///test1/2024/08/01/real-post-example-1.html"
            rel="alternate" type="text/html"
            title="Real Post Example - Fighting Ursa Luring Targets With Car for Sale" />
        <published>Thu, 01 Aug 2024 08:00:00 +0000</published>
        <updated>Thu, 01 Aug 2024 08:00:00 +0000</updated>
        <id>https://muchdogesec.github.io/fakeblog123///test1/2024/08/01/real-post-example-1.html</id>
        <title>
    <![CDATA[ Real Post Example - Fighting Ursa Luring Targets With Car for Sale ]]>
    </title>
        <summary>
    <![CDATA[ A Russian threat actor we track as Fighting Ursa. ]]>
    </summary>
        <content>
    <![CDATA[ A Russian threat actor we track as Fighting Ursa. ]]>
    </content>
        <author>
            <name>David G</name>
            <name>G David</name>
        </author>
        <category term="Blog" />
        <category term="Test" />
    </entry>
</feed>
"""

