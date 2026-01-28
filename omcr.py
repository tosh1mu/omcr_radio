# -*- coding: utf-8 -*-
import datetime
import hashlib
import re
import urllib.parse
from dataclasses import dataclass
from datetime import datetime as dt
from functools import total_ordering
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup


class OMCRError(Exception):
    """オモコロラジオの基本例外クラス"""


class InvalidURLError(OMCRError):
    """無効なURLが指定された場合の例外"""


class FetchError(OMCRError):
    """データ取得に失敗した場合の例外"""


OMOCORO_URL_PATTERN = re.compile(r"^https://omocoro\.jp/.*[0-9]+")
MP3_LINK_PATTERN = re.compile(r".*.mp3")


@dataclass(frozen=True, order=True)
class Episode:
    title: str
    pub_date: dt
    description: str
    mp3_url: str
    article_url: str


@dataclass
class ArticleLink:
    category: str
    date: dt
    title: str
    url: str


@total_ordering
class RadioPage:
    def __init__(self, url: str = "") -> None:
        self.url: str = ""
        self.id: int = 0
        self.title: str = ""
        self.pub_date: dt = dt(1900, 1, 1, 0, 0, 0)
        self.description: str = ""
        self.tags: List[str] = []
        self.mp3_urls: List[str] = []

        if url:
            self._load_from_url(url)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RadioPage):
            return NotImplemented
        return self.id == other.id

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, RadioPage):
            return NotImplemented
        return self.id < other.id

    def _load_from_url(self, url: str) -> None:
        if not OMOCORO_URL_PATTERN.match(url):
            raise InvalidURLError(f"Invalid URL: {url}")

        self.url = url
        self._fetch_page()

    def _fetch_page(self) -> None:
        try:
            res = requests.get(self.url)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise FetchError(f"Failed to fetch page: {e}") from e

        self._parse_page(res.text)

    def _parse_page(self, html: str) -> None:
        soup = BeautifulSoup(html, "html.parser")

        try:
            self.id = int(re.findall(r"[0-9]+", self.url)[0])
            self.title = soup.select_one('div[class="title"]').text.strip()

            tags_div = soup.select_one('div[class="tags"]')
            self.tags = [str(tag) for tag in tags_div.find_all("a")]

            date_text = soup.select_one('div[class="date"]').text
            self.pub_date = dt.strptime(date_text, "%Y-%m-%d")

            self.description = soup.select_one('div[class="description"]').text

            mp3_links = soup.find_all("a", attrs={"href": MP3_LINK_PATTERN})
            self.mp3_urls = [str(link.get("href")) for link in mp3_links]

            print(f"{len(self.mp3_urls)} mp3(s) found from {self.title}.")
        except (AttributeError, IndexError) as e:
            raise FetchError(f"Failed to parse page content: {e}") from e

    def get_episodes(self) -> List[Episode]:
        return [
            Episode(
                self.title,
                self.pub_date + datetime.timedelta(seconds=i + 1),
                self.description,
                mp3_url,
                self.url,
            )
            for i, mp3_url in enumerate(self.mp3_urls)
        ]


class ArticleList:
    def __init__(self, base_url: str, page: int = 1, sort: str = "new") -> None:
        self.url = f"{base_url}page/{page}/?sort={sort}"
        self.links = self._fetch_links()

    def _fetch_links(self) -> List[ArticleLink]:
        try:
            res = requests.get(self.url)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise FetchError(f"Failed to fetch article list: {e}") from e

        return self._parse_links(res.text)

    def _parse_links(self, html: str) -> List[ArticleLink]:
        soup = BeautifulSoup(html, "html.parser")
        boxes = soup.select('div[class="box"]')
        links: List[ArticleLink] = []

        for box in boxes:
            link = self._parse_box(box)
            if link:
                links.append(link)

        print(f"{len(links)} link(s) found from {urllib.parse.unquote(self.url)}.")
        return links

    def _parse_box(self, box: BeautifulSoup) -> Optional[ArticleLink]:
        try:
            category = box.select_one('div[class="category"] span').text
            if category != "ラジオ":
                return None

            date = dt.strptime(box.select_one('div[class="date"]').text, "%Y.%m.%d")
            title = box.select_one('div[class="title"] a').text
            url = box.select_one('div[class="title"] a').get("href")

            if not url.endswith("/"):
                url += "/"

            return ArticleLink(category, date, title, url)
        except (AttributeError, ValueError) as e:
            print(f"Warning: Failed to parse box content: {e}")
            return None


class TagHandler:
    PICKLE_DIR = "pickles"

    def __init__(self, tag: str) -> None:
        self.tag = tag
        self.pickle_name = f"{hashlib.md5(tag.encode()).hexdigest()}.pkl"
        self.base_url = f"https://omocoro.jp/tag/{tag}/"
        self.articles: List[RadioPage] = []

    def _has_article(self, url: str) -> bool:
        return any(article.url == url for article in self.articles)

    def _sort_articles(self) -> None:
        self.articles.sort()

    def get(self, page: int = 1, sort: str = "new") -> Tuple[int, int]:
        article_list = ArticleList(self.base_url, page, sort)

        if not article_list.links:
            return (0, 0)

        add_count = 0
        for link in article_list.links:
            if self._has_article(link.url):
                continue

            try:
                self.articles.append(RadioPage(link.url))
                add_count += 1
            except (InvalidURLError, FetchError) as e:
                print(f"Warning: Failed to process {link.url}: {e}")

        return (len(article_list.links), add_count)

    def get_pages(self, max_page: int = 1) -> None:
        for page in range(1, max_page + 1):
            self.get(page)

    def update(self) -> None:
        print(f"Updating {self.tag}...")
        page = 1

        while True:
            total, added = self.get(page, "new")
            if total > added:
                break
            page += 1

        self._sort_articles()

    def get_all(self, sort: str = "new") -> None:
        page = 1

        while True:
            total, _ = self.get(page, sort)
            if total < 1:
                break
            page += 1

        self._sort_articles()

    def refresh(self) -> None:
        self.get_all("old")
        self.update()

    def save(self, directory: str = PICKLE_DIR) -> None:
        pickle_path = Path(directory) / self.pickle_name
        pickle_path.parent.mkdir(parents=True, exist_ok=True)
        pd.to_pickle(self, pickle_path)

    def load(self, directory: str = PICKLE_DIR) -> bool:
        pickle_path = Path(directory) / self.pickle_name

        if not pickle_path.is_file():
            return False

        loaded = pd.read_pickle(pickle_path)

        # 旧属性名(_articles)との互換性を維持
        if hasattr(loaded, "articles"):
            self.articles = loaded.articles
        elif hasattr(loaded, "_articles"):
            self.articles = loaded._articles
        else:
            return False

        # RadioPageの旧属性名をマイグレーション
        for article in self.articles:
            self._migrate_radio_page(article)

        return True

    @staticmethod
    def _migrate_radio_page(page: "RadioPage") -> None:
        """旧属性名(_url等)から新属性名(url等)へマイグレーション"""
        migrations = [
            ("_url", "url"),
            ("_id", "id"),
            ("_title", "title"),
            ("_pub_date", "pub_date"),
            ("_description", "description"),
            ("_tags", "tags"),
            ("_mp3_urls", "mp3_urls"),
        ]

        for old_name, new_name in migrations:
            if hasattr(page, old_name) and not hasattr(page, new_name):
                setattr(page, new_name, getattr(page, old_name))
