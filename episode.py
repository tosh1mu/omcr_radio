# -*- coding: utf-8 -*-
# エピソードを扱うためのクラス定義
from dataclasses import dataclass
from datetime import datetime as dt
import requests
from bs4 import BeautifulSoup
import re

@dataclass(frozen = True)
class EpisodeData:
    id: int
    title: str
    series: str
    pub_date: dt
    description: str
    mp3_url: str
    page_url: str

class Episode:
    def __init__(self, episode_url=""):
        if len(episode_url) > 0:
            self.load(episode_url)
        else:
            self._id = 0
            self._title = ""
            self._series = ""
            self._pub_date = dt(1900, 1, 1, 0, 0 ,0)
            self._description = ""
            self._mp3_url = ""
            self._url = ""
            
    def load(self, episode_url):
        self._url = episode_url
        try:
            res = requests.get(self._url)
        except requests.exceptions.HTTPError:
            res.raise_for_status()
            print(res.text)
        soup = BeautifulSoup(self._res.text, "html.parser")
        self._id = re.findall('[0-9]+', self._url)[0]
        self._title = soup.select('div[class="title"]')[0].text
        self._series = ""
        tags = soup.select('div[class="tags"]')[0]
        tag_list = tags.find_all('a')
        for tag in tag_list:
            if tag.text != "#ラジオ":
                self._series = tag.text.replace('#', '')
        self._pub_date = soup.select('div[class="date"]')[0].text
        self._description = soup.select('div[class="description"]')[0].text
        self._mp3_url = soup.find('a', attrs={ 'href': re.compile(r'.*.mp3') }).get('href') if page_soup.find('a', attrs={ 'href': re.compile(r'.*.mp3') }) else ''
        self._page_url = self._url
    
    def data(self):
        return EpisodeData(
            self._id,
            self._title,
            self._series,
            self._pub_date,
            self._description,
            self._mp3_url,
            self._page_url
        )