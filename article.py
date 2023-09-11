# -*- coding: utf-8 -*-
from dataclasses import dataclass
from datetime import datetime as dt
import requests
from bs4 import BeautifulSoup
import re

@dataclass(frozen = True, order = True)
class Episode:
    id: int
    title: str
    pub_date: dt
    description: str
    mp3_url: str
    article_url: str

class Article:
    def __init__(self, url=""):
        self._id = 0
        self._title = ""
        self._pub_date = dt(1900, 1, 1, 0, 0 ,0)
        self._description = ""
        self._tags = []
        self._mp3_urls = []
        self._url = ""
        if len(url) > 0:
            self.load(url)
            
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
    
    def load(self, url):
        self._url = url
        try:
            res = requests.get(self._url)
        except requests.exceptions.HTTPError:
            res.raise_for_status()
            print(res.text)
        soup = BeautifulSoup(res.text, "html.parser")
        self._id = int(re.findall('[0-9]+', self._url)[0])
        self._title = soup.select('div[class="title"]')[0].text.strip()
        tags = soup.select('div[class="tags"]')[0]
        tag_list = tags.find_all('a')
        for tag in tag_list:
            if tag.text != "#ラジオ":
                self._tags.append(tag)
        self._pub_date = dt.strptime(soup.select('div[class="date"]')[0].text, '%Y-%m-%d')
        self._description = soup.select('div[class="description"]')[0].text
        if soup.find('a', attrs={ 'href': re.compile(r'.*.mp3') }):
            for result in soup.find_all('a', attrs={ 'href': re.compile(r'.*.mp3') }):
                mp3_url = result.get('href')
                if mp3_url not in self._mp3_urls:
                    self._mp3_urls.append(mp3_url)
        
        print('Article loaded: ' + self._title + '.')
        return True
    
    def episode_count(self):
        return len(self._mp3_urls)
    
    def episodes(self):
        episodes = []
        i = 1
        for mp3_url in self._mp3_urls:
            episode = Episode(
                self._id * 10 + i,
                self._title,
                self._pub_date,
                self._description,
                mp3_url,
                self._url
            )
            episodes.append(episode)
            i += 1
        return episodes