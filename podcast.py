# -*- coding: utf-8 -*-
from datetime import datetime as dt
from xml.dom.minidom import parseString, Document, Element
from typing import Optional
import os
from pathlib import Path

class PodcastError(Exception):
    """ポッドキャストの基本例外クラス"""
    pass

class RSSGenerationError(PodcastError):
    """RSS生成に失敗した場合の例外"""
    pass

class Podcast:
    def __init__(
        self,
        channel_title: str,
        owner_email: str,
        author: str,
        description: str,
        img_href: str,
        channel_url: str
    ) -> None:
        self._dom: Document = self._create_base_document()
        self._channel: Element = self._dom.getElementsByTagName("channel")[0]
        self._set_channel_info(channel_title, owner_email, author, description, img_href, channel_url)

    def _create_base_document(self) -> Document:
        xml_template = """<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
            <channel>
                <title>title</title>
                <itunes:owner>
                    <itunes:email>email</itunes:email>
                </itunes:owner>
                <itunes:author>author</itunes:author>
                <description>description</description>
                <itunes:image href="https://"/>
                <language>ja-jp</language>
                <link>link</link>
            </channel>
        </rss>"""
        return parseString(xml_template)

    def _set_channel_info(
        self,
        channel_title: str,
        owner_email: str,
        author: str,
        description: str,
        img_href: str,
        channel_url: str
    ) -> None:
        self._channel.getElementsByTagName("title")[0].firstChild.data = channel_title
        self._channel.getElementsByTagName("itunes:email")[0].firstChild.data = owner_email
        self._channel.getElementsByTagName("itunes:author")[0].firstChild.data = author
        self._channel.getElementsByTagName("description")[0].firstChild.data = description
        self._channel.getElementsByTagName("itunes:image")[0].attributes["href"].value = img_href
        self._channel.getElementsByTagName("link")[0].firstChild.data = channel_url

    def add_episode(
        self,
        ep_title: str,
        ep_description: str,
        ep_pubdate: dt,
        ep_mp3_url: str,
        article_url: str
    ) -> None:
        item = self._dom.createElement('item')
        self._channel.appendChild(item)

        # タイトルの設定
        self._add_text_node(item, 'title', ep_title)
        
        # 説明文の設定
        self._add_text_node(item, 'description', ep_description)
        
        # 公開日の設定
        pubdate_str = ep_pubdate.strftime('%a, %d %b %Y %H:%M:%S +0900')
        self._add_text_node(item, 'pubDate', pubdate_str)
        
        # mp3のURL
        enclosure_node = self._dom.createElement('enclosure')
        self._set_attribute(enclosure_node, 'url', ep_mp3_url)
        self._set_attribute(enclosure_node, 'type', "audio/mpeg")
        item.appendChild(enclosure_node)
        
        # GUID(記事URL)
        guid_node = self._dom.createElement('guid')
        guid_node.appendChild(self._dom.createTextNode(article_url))
        self._set_attribute(guid_node, 'isPermaLink', "True")
        item.appendChild(guid_node)

    def _add_text_node(self, parent: Element, tag_name: str, text: str) -> None:
        node = self._dom.createElement(tag_name)
        node.appendChild(self._dom.createTextNode(text))
        parent.appendChild(node)

    def _set_attribute(self, element: Element, name: str, value: str) -> None:
        attr = self._dom.createAttribute(name)
        attr.value = value
        element.setAttributeNode(attr)

    def create_rss(self, rss_path: str) -> bool:
        try:
            path = Path(rss_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, "w", encoding='utf-8') as file:
                file.write(self._dom.toprettyxml(indent="  "))
            return True
        except (IOError, OSError) as e:
            raise RSSGenerationError(f'Failed to create RSS file: {str(e)}')