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
        self._url = ""
        self._id = 0
        self._title = ""
        self._pub_date = dt(1900, 1, 1, 0, 0 ,0)
        self._description = ""
        self._tags = []
        self._mp3_urls = []
        if len(url) > 0:
            self.set_url(url)

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
    def check_url(self, url):
        res = re.match(r'^(https://omocoro.jp/).*[0-9]+', url)
        if res:
            return True
        else:
            return False
    
    ## URLを設定し、ページの内容を読み込む
    def set_url(self, url):
        genuine = self.check_url(url)
        if genuine:
            self._url = url
            self.load_page()
            return True
        else:
            print('Invalid URL: ' + url)
            return False

    ## ラジオページの内容を読み込む
    def load_page(self):
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
        
        print(str(len(self._mp3_urls)) + ' mp3(s) found from ' + self._title + '.')
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
        self._page_url = base_url + "page/" + str(page) + "/?sort=" + sort
        self._links = self.get_links() # 記事のタイトル：URL
    
    @property
    def url(self):
        return self._page_url

    @property
    def links(self):
        return self._links
    
    ## 記事リストページ内にある記事URLを取得
    def get_links(self):
        links = []
        try:
            res = requests.get(self._page_url)
        except requests.exceptions.HTTPError:
            res.raise_for_status()
            print(res.text)
            return links
        soup = BeautifulSoup(res.text, "html.parser")
        boxes = soup.select('div[class="box"]')
        if len(boxes) > 0:
            for box in boxes:
                category = box.select_one('div[class="category"]').select_one("span").text
                date = dt.strptime(box.select_one('div[class="date"]').text, '%Y.%m.%d')
                title = box.select_one('div[class="title"]').select_one("a").text
                link = box.select_one('div[class="title"]').find('a').get('href')
                links.append((category, date, title, link))
        print(str(len(links)) + ' link(s) found from ' + urllib.parse.unquote(self._page_url) + '.')
        return links

## 指定タグを扱うクラス
class TagHandler:
    def __init__(self, tag):
        self._tag = tag
        self._base_url = 'https://omocoro.jp/tag/' + self._tag + '/'
        self._article_dict = {}
        self._last_update = dt(1900, 1, 1, 0, 0 ,0)
    
    ## 指定のページ内にある記事を取得する
    def get(self, page = 1, sort = "new"):
        article_list = ArticleList(self._base_url, page, sort)
        links = article_list.links
        if len(links) < 1:
            return False
        for link in links:
            if (link[0] == 'ラジオ') and (link[1] > self._last_update):
                title = link[2]
                radio_page = RadioPage(link[3])
                if title not in self._article_dict.keys():
                    self._article_dict[title] = radio_page
        return True
    
    ## 記事の最新版を取得する
    def update(self, max_page = 1):
        page = 1
        update_dt = dt.now()
        while page <= max_page:
            self.get(page)
            page += 1
        self._last_update = update_dt
        return True
    
    ## 新しい順に全数取得する
    def get_all(self, sort = "new"):
        flag = True
        page = 1
        update_dt = dt.now()
        while flag is True:
            flag = self.get(page, sort)
            page += 1
        self._last_update = update_dt
        return True
    
    ## 記事を全部取得する
    def refresh(self):
        self.get_all("old")
        self.get_all("new")
        return True
