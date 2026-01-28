# -*- coding: utf-8 -*-
from dataclasses import dataclass
from datetime import datetime as dt
from pathlib import Path
from typing import List
from xml.dom.minidom import Document, Element, parseString


class PodcastError(Exception):
    """ポッドキャストの基本例外クラス"""


class RSSGenerationError(PodcastError):
    """RSS生成に失敗した場合の例外"""


RSS_TEMPLATE = """<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
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


@dataclass(frozen=True)
class ChannelInfo:
    title: str
    owner_email: str
    author: str
    description: str
    img_href: str
    url: str


@dataclass(frozen=True)
class EpisodeInfo:
    title: str
    description: str
    pub_date: dt
    mp3_url: str
    article_url: str


class Podcast:
    def __init__(
        self,
        channel_title: str,
        owner_email: str,
        author: str,
        description: str,
        img_href: str,
        channel_url: str,
    ) -> None:
        self._dom: Document = parseString(RSS_TEMPLATE)
        self._channel: Element = self._dom.getElementsByTagName("channel")[0]
        self._episodes: List[EpisodeInfo] = []

        channel_info = ChannelInfo(
            title=channel_title,
            owner_email=owner_email,
            author=author,
            description=description,
            img_href=img_href,
            url=channel_url,
        )
        self._set_channel_info(channel_info)

    def _set_channel_info(self, info: ChannelInfo) -> None:
        self._set_text("title", info.title)
        self._set_text("itunes:email", info.owner_email)
        self._set_text("itunes:author", info.author)
        self._set_text("description", info.description)
        self._set_text("link", info.url)
        self._channel.getElementsByTagName("itunes:image")[0].setAttribute("href", info.img_href)

    def _set_text(self, tag_name: str, text: str) -> None:
        self._channel.getElementsByTagName(tag_name)[0].firstChild.data = text

    def _create_element(self, tag_name: str, text: str) -> Element:
        node = self._dom.createElement(tag_name)
        node.appendChild(self._dom.createTextNode(text))
        return node

    def add_episode(
        self,
        ep_title: str,
        ep_description: str,
        ep_pubdate: dt,
        ep_mp3_url: str,
        article_url: str,
    ) -> None:
        episode = EpisodeInfo(
            title=ep_title,
            description=ep_description,
            pub_date=ep_pubdate,
            mp3_url=ep_mp3_url,
            article_url=article_url,
        )
        self._episodes.append(episode)
        self._add_episode_to_dom(episode)

    def _add_episode_to_dom(self, episode: EpisodeInfo) -> None:
        item = self._dom.createElement("item")
        self._channel.appendChild(item)

        item.appendChild(self._create_element("title", episode.title))
        item.appendChild(self._create_element("description", episode.description))

        pubdate_str = episode.pub_date.strftime("%a, %d %b %Y %H:%M:%S +0900")
        item.appendChild(self._create_element("pubDate", pubdate_str))

        enclosure = self._dom.createElement("enclosure")
        enclosure.setAttribute("url", episode.mp3_url)
        enclosure.setAttribute("type", "audio/mpeg")
        item.appendChild(enclosure)

        guid = self._create_element("guid", episode.article_url)
        guid.setAttribute("isPermaLink", "True")
        item.appendChild(guid)

    def create_rss(self, rss_path: str) -> None:
        try:
            path = Path(rss_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as file:
                file.write(self._dom.toprettyxml(indent="  "))
        except (IOError, OSError) as e:
            raise RSSGenerationError(f"Failed to create RSS file: {e}") from e
