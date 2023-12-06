# -*- coding: utf-8 -*-
from dataclasses import dataclass
from datetime import datetime as dt
import datetime
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

## エピソードを扱うクラス
@dataclass(frozen = True, order = True)
class Episode:
    title: str
    pub_date: dt
    description: str
    mp3_url: str
    article_url: str

## オモコロラジオの記事ページを扱うクラス
class RadioPage:
    def __init__(self, url=""):
        self._id = 0
        self._title = ""
        self._pub_date = dt(1900, 1, 1, 0, 0 ,0)
        self._description = ""
        self._tags = []
        self._mp3_urls = []
        self._url = ""
        if len(url) > 0:
            self.load_url(url)
    
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
    
    @property
    def url(self):
        return self._url
    
    ## ラジオページの内容を読み込む
    def load_url(self, url):
        self._url = url
        try:
            res = requests.get(self._url)
        except requests.exceptions.HTTPError:
            res.raise_for_status()
            print(res.text)
        soup = BeautifulSoup(res.text, "html.parser")
        self._id = int(re.findall('[0-9]+', self._url)[0])
        self._title = str(soup.select('div[class="title"]')[0].text.strip())
        tags = soup.select('div[class="tags"]')[0]
        tag_list = tags.find_all('a')
        for tag in tag_list:
            self._tags.append(str(tag))
        self._pub_date = dt.strptime(soup.select('div[class="date"]')[0].text, '%Y-%m-%d')
        self._description = str(soup.select('div[class="description"]')[0].text)
        if soup.find('a', attrs={ 'href': re.compile(r'.*.mp3') }):
            for result in soup.find_all('a', attrs={ 'href': re.compile(r'.*.mp3') }):
                mp3_url = str(result.get('href'))
                if mp3_url not in self._mp3_urls:
                    self._mp3_urls.append(mp3_url)
        
        print('A Radio Page loaded: ' + self._title + '.')
        return True

    ## ラジオページに含まれるエピソードをリストで返す
    def get_episodes(self):
        episode_list = []
        i = 1
        for mp3_url in self._mp3_urls:
            episode = Episode(
                self._id * 10 + i,
                self._title,
                self._pub_date + datetime.timedelta(secondes=i),
                self._description,
                mp3_url,
                self._url
            )
            episode_list.append(episode)
            i += 1
        return episode_list
    
## 記事リストページを扱うクラス
class ArticleList:
    def __init__(self, base_url, page = 1, sort = "new"):
        self._page_url = base_url + "page/" + page + "/?sort=" + sort
        self._link_dict = {} # 記事のタイトル：URL
        self._datetime_dict = {} # 記事のURL：日時
        self.get_list()
    
    @property
    def url(self):
        return self._page_url
    
    ## 記事リストページ内にある記事URLを取得
    def get_list(self):
        try:
            res = requests.get(self._page_url)
        except requests.exceptions.HTTPError:
            res.raise_for_status()
            print(res.text)
            return False
        print("Getting links from " + urllib.parse.unquote(url) + "...")
        soup = BeautifulSoup(res.text, "html.parser")
        boxes = soup.select('div[class="box"]')
        if len(boxes) > 0:
            for box in boxes:
                links = box.find_all('a', attrs = {'href': re.compile(r'^(https://omocoro.jp/).*[0-9]+')})
                if len(links) < 2:
                    continue
                else:
                    url = links[0].get('href')
                    title = str(links[1].text)
                    self._link_dict[title] = url
        return True
    
    ## 記事リストページ内にある記事URLのリストを返す
    def link_dict(self):
        return list(self._link_dict)

## 指定タグを扱うクラス
class Tag:
    def __init__(self, tag):
        self._tag = tag
        self._base_url = 'https://omocoro.jp/tag/' + self._tag
        self._article_dict = {}
        self._load_list_datetime = dt.now()
        return True
    
    ## 記事を全部取得する
    def refresh(self):
        return True
    
    ## 記事の最新版を取得する