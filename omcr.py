# -*- coding: utf-8 -*-
from dataclasses import dataclass
from functools import total_ordering
from datetime import datetime as dt
import datetime
from typing import List, Tuple, Optional
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import hashlib
import pandas as pd
import os
from pathlib import Path

class OMCRError(Exception):
    """オモコロラジオの基本例外クラス"""
    pass

class InvalidURLError(OMCRError):
    """無効なURLが指定された場合の例外"""
    pass

class FetchError(OMCRError):
    """データ取得に失敗した場合の例外"""
    pass

## エピソードを扱うクラス
@dataclass(frozen = True, order = True)
class Episode:
    title: str
    pub_date: dt
    description: str
    mp3_url: str
    article_url: str

## オモコロラジオの記事ページを扱うクラス
@total_ordering
class RadioPage:
    def __init__(self, url: str = "") -> None:
        self._url: str = ""
        self._id: int = 0
        self._title: str = ""
        self._pub_date: dt = dt(1900, 1, 1, 0, 0 ,0)
        self._description: str = ""
        self._tags: List[str] = []
        self._mp3_urls: List[str] = []
        if url:
            self.set_url(url)
    
    def __eq__(self, other):
        if not isinstance(other, RadioPage):
            return NotImplemented
        return self.id == other.id
    
    def __lt__(self, other):
        if not isinstance(other, RadioPage):
            return NotImplemented
        return self.id < other.id

    @property
    def url(self):
        return self._url

    @property
    def id(self):
        return self._id
    
    @property
    def title(self):
        return self._title

    @property
    def pub_date(self):
        return self._pub_date
    
    @property
    def description(self):
        return self._description
    
    @property
    def tags(self):
        return self._tags
    
    @property
    def mp3_urls(self):
        return self._mp3_urls

    ## オモコロのリンクかどうかを確認する
    def check_url(self, url: str) -> bool:
        return bool(re.match(r'^(https://omocoro.jp/).*[0-9]+', url))
    
    ## URLを設定し、ページの内容を読み込む
    def set_url(self, url: str) -> bool:
        if not self.check_url(url):
            raise InvalidURLError(f'Invalid URL: {url}')
        self._url = url
        return self.load_page()

    ## ラジオページの内容を読み込む
    def load_page(self) -> bool:
        try:
            res = requests.get(self._url)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise FetchError(f'Failed to fetch page: {str(e)}')

        soup = BeautifulSoup(res.text, "html.parser")
        try:
            self._id = int(re.findall('[0-9]+', self._url)[0])
            self._title = soup.select_one('div[class="title"]').text.strip()
            tags = soup.select_one('div[class="tags"]')
            self._tags = [str(tag) for tag in tags.find_all('a')]
            self._pub_date = dt.strptime(soup.select_one('div[class="date"]').text, '%Y-%m-%d')
            self._description = soup.select_one('div[class="description"]').text

            mp3_links = soup.find_all('a', attrs={'href': re.compile(r'.*.mp3')})
            self._mp3_urls = [str(link.get('href')) for link in mp3_links]
            
            print(f'{len(self._mp3_urls)} mp3(s) found from {self._title}.')
            return True
        except (AttributeError, IndexError) as e:
            raise FetchError(f'Failed to parse page content: {str(e)}')

    ## ラジオページに含まれるエピソードをリストで返す
    def get_episodes(self) -> List[Episode]:
        return [
            Episode(
                self._title,
                self._pub_date + datetime.timedelta(seconds=i+1),
                self._description,
                mp3_url,
                self._url
            )
            for i, mp3_url in enumerate(self._mp3_urls)
        ]
    
## 記事リストページを扱うクラス
class ArticleList:
    def __init__(self, base_url: str, page: int = 1, sort: str = "new") -> None:
        self._page_url = f"{base_url}page/{page}/?sort={sort}"
        self._links = self.get_links() # 記事のタイトル：URL
    
    @property
    def url(self):
        return self._page_url

    @property
    def links(self):
        return self._links
    
    ## 記事リストページ内にある記事URLを取得
    def get_links(self) -> List[Tuple[str, dt, str, str]]:
        links = []
        try:
            res = requests.get(self._page_url)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise FetchError(f'Failed to fetch article list: {str(e)}')

        soup = BeautifulSoup(res.text, "html.parser")
        boxes = soup.select('div[class="box"]')
        
        for box in boxes:
            try:
                category = box.select_one('div[class="category"] span').text
                if category != "ラジオ":
                    continue
                    
                date = dt.strptime(box.select_one('div[class="date"]').text, '%Y.%m.%d')
                title = box.select_one('div[class="title"] a').text
                link = box.select_one('div[class="title"] a').get('href')
                
                if not link.endswith("/"):
                    link += "/"
                    
                links.append((category, date, title, link))
            except (AttributeError, ValueError) as e:
                print(f'Warning: Failed to parse box content: {str(e)}')
                continue

        print(f'{len(links)} link(s) found from {urllib.parse.unquote(self._page_url)}.')
        return links

## 指定タグを扱うクラス
class TagHandler:
    def __init__(self, tag: str) -> None:
        self._tag = tag
        self._pickle_name = f"{hashlib.md5(self._tag.encode()).hexdigest()}.pkl"
        self._base_url = f'https://omocoro.jp/tag/{self._tag}/'
        self._articles: List[RadioPage] = []

    @property    
    def pickle_name(self):
        return self._pickle_name
    
    @property
    def articles(self):
        return self._articles
    
    def sort(self):
        self._articles = sorted(self._articles)
        return True
    
    def check_url(self, url: str) -> bool:
        return any(article.url == url for article in self._articles)

    ## 指定のページ内にある記事を取得する
    def get(self, page: int = 1, sort: str = "new") -> Tuple[int, int]:
        article_list = ArticleList(self._base_url, page, sort)
        links = article_list.links
        add_count = 0

        if not links:
            return (0, 0)

        for _, _, _, url in links:
            if not self.check_url(url):
                try:
                    radio_page = RadioPage(url)
                    self._articles.append(radio_page)
                    add_count += 1
                except (InvalidURLError, FetchError) as e:
                    print(f'Warning: Failed to process {url}: {str(e)}')
                    continue

        return (len(links), add_count)
    
    ## ページ数を指定して、記事を取得する
    def get_pages(self, max_page = 1):
        page = 1
        while page <= max_page:
            self.get(page)
            page += 1
        return True
    
    def update(self):
        print('Updating ' + self._tag + '...')
        continue_flag = True
        page = 1
        while continue_flag is True:
            get_count = self.get(page, "new")
            if get_count[0] > get_count[1]:
                continue_flag = False
            page += 1
        self.sort()
        return True
    
    ## ソート順に、取得できなくなるまで全部取得する
    def get_all(self, sort = "new"):
        flag = True
        page = 1
        while flag is True:
            get_count = self.get(page, sort)
            if get_count[0] < 1:
                flag = False
            page += 1
        self.sort()
        return True
    
    ## 記事を全部取得する
    def refresh(self):
        self.get_all("old")
        self.update()
        return True
    
    def save(self, dir: str = "pickles/") -> bool:
        pickle_path = Path(dir) / self._pickle_name
        pickle_path.parent.mkdir(parents=True, exist_ok=True)
        pd.to_pickle(self, pickle_path)
        return True
    
    def load(self, dir: str = "pickles/") -> bool:
        pickle_path = Path(dir) / self._pickle_name
        if pickle_path.is_file():
            loaded = pd.read_pickle(pickle_path)
            self._articles = loaded.articles
            return True
        return False
