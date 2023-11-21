# -*- coding: utf-8 -*-
from datetime import datetime as dt
from xml.dom.minidom import parseString

class Podcast:
    def __init__(self, channel_title, owner_email, author, description, img_href, channel_url):
        xml_template = "<rss version=\"2.0\" xmlns:itunes=\"http://www.itunes.com/dtds/podcast-1.0.dtd\">\
                            <channel>\
                                <title>title</title>\
                                <itunes:owner>\
                                    <itunes:email>email</itunes:email>\
                                </itunes:owner>\
                                <itunes:author>author</itunes:author>\
                                <description>description</description>\
                                <itunes:image href=\"https://\"/>\
                                <language>ja-jp</language>\
                                <link>link</link>\
                            </channel>\
                        </rss>"
        
        self._dom = parseString(xml_template)
        self._channel = self._dom.getElementsByTagName("channel")[0]

        self._channel.getElementsByTagName("title")[0].firstChild.data = channel_title
        self._channel.getElementsByTagName("itunes:email")[0].firstChild.data = owner_email
        self._channel.getElementsByTagName("itunes:author")[0].firstChild.data = author
        self._channel.getElementsByTagName("description")[0].firstChild.data = description
        self._channel.getElementsByTagName("itunes:image")[0].attributes["href"].value = img_href
        self._channel.getElementsByTagName("link")[0].firstChild.data = channel_url
    
    def add_episode(self, ep_title, ep_description, ep_pubdate, ep_mp3_url, article_url):
        item = self._dom.createElement('item')
        self._channel.appendChild(item)
        # タイトルの設定
        title_node = self._dom.createElement('title')
        title_node.appendChild(self._dom.createTextNode(ep_title))
        item.appendChild(title_node)
        # 説明文の設定
        description_node = self._dom.createElement('description')
        description_node.appendChild(self._dom.createTextNode(ep_description))
        item.appendChild(description_node)
        # 公開日の設定
        pubdate_node = self._dom.createElement('pubDate')
        pubdate_str = ep_pubdate.strftime('%a, %d %b %Y %H:%M:%S +0900')
        pubdate_node.appendChild(self._dom.createTextNode(pubdate_str))
        item.appendChild(pubdate_node)
        # mp3のURL
        enclosure_node = self._dom.createElement('enclosure')
        url_attr = self._dom.createAttribute('url')
        url_attr.value = str(ep_mp3_url)
        enclosure_node.setAttributeNode(url_attr)
        type_attr = self._dom.createAttribute('type')
        type_attr.value = "audio/mpeg"
        enclosure_node.setAttributeNode(type_attr)
        item.appendChild(enclosure_node)
        # GUID(記事URL)
        guid_node = self._dom.createElement('guid')
        guid_node.appendChild(self._dom.createTextNode(article_url))
        is_link_attr = self._dom.createAttribute('isPermaLink')
        is_link_attr.value = "True"
        guid_node.setAttributeNode(is_link_attr)
        item.appendChild(guid_node)
    
    def create_rss(self, rss_path):
        with open(rss_path, "w") as file:
            file.write(self._dom.toprettyxml(indent = "  "))
        return True