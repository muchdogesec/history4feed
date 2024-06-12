from datetime import datetime, timezone
from xml.dom.minidom import Document, Element


def createTextElement(document: Document, tagName, text):
    el = document.createElement(tagName)
    txtNode = document.createTextNode(text or "")
    el.appendChild(txtNode)
    return el

def createCDataElement(document: Document, tagName, text):
    el = document.createElement(tagName)
    txtNode = document.createCDATASection(text or "")
    el.appendChild(txtNode)    
    return el

def createRSSHeader(title, description,  url, last_build_date=None):
    last_build_date = last_build_date or datetime.now(timezone.utc)
    d = Document()
    rss = d.createElement("rss")
    d.appendChild(rss)
    rss.setAttribute("version", "2.0")
    channel = d.createElement("channel")
    rss.appendChild(channel)
    channel.appendChild(createTextElement(d, "title", title))
    channel.appendChild(createTextElement(d, "description", description))
    channel.appendChild(createTextElement(d, "link", url))
    channel.appendChild(createTextElement(d, "lastBuildDate", last_build_date.isoformat()))
    # channel.appendChild(createTextElement(d, "generator", LINK_TO_SELF))
    return d, channel


def getText(nodelist: list[Element]):
    if not nodelist:
        return ''
    if not isinstance(nodelist, list):
        nodelist = nodelist.childNodes
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE or node.nodeType == node.CDATA_SECTION_NODE:
            rc.append(node.data)
    return ''.join(rc)

def getFirstElementByTag(node, tag):
    if not node:
        return None
    elems = node.getElementsByTagName(tag)
    return (elems or None) and elems[0]

def getFirstChildByTag(node: Element, tag):
    child = None
    for c in node.childNodes:
        if c.nodeName == tag:
            child = c
            break
    return child


def getAtomLink(node: Element, rel='self'):
    links = [child for child in node.childNodes if child.nodeType == child.ELEMENT_NODE and child.tagName in ['link', 'atom:link']]

    link = links[0]
    for l in links:
        r = l.attributes.get('rel')
        if r and r.value == rel:
            link = l
            break
    return link.attributes['href'].value