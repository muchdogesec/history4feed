from .xml_utils import createRSSHeader, createCDataElement, createTextElement
from ..app.models import Feed, Post
from django.db.models.manager import BaseManager
from xml.dom.minidom import Document


def build_rss(feed_obj: Feed, posts_set: BaseManager[Post]):
    document, channel = createRSSHeader(feed_obj.title,  feed_obj.description, feed_obj.url, feed_obj.latest_item_pubdate)
    for post in posts_set:
        channel.appendChild(build_entry_element(post, document))

    return document.toprettyxml()

def build_entry_element(post: Post, d: Document):
    element = d.createElement('item')
    element.appendChild(createTextElement(d, "title", post.title))

    link = createTextElement(d, "link", post.link)
    link.setAttribute("href", post.link)
    element.appendChild(link)
    element.appendChild(createTextElement(d, "pubDate", post.pubdate.isoformat()))
    if post.description:
        description = post.description
        description = description
        element.appendChild(createTextElement(d, "description", description))

    for category in post.categories.all():
        element.appendChild(createTextElement(d, "category", category.name))

    if post.author:
        author = d.createElement('author')
        author.appendChild(createTextElement(d, "name", post.author))
        element.appendChild(author)
    return element