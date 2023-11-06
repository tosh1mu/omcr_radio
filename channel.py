# -*- coding: utf-8 -*-
# 番組を扱うためのクラス定義
import requests
from datetime import datetime as dt
from bs4 import BeautifulSoup
import article
import re
import pandas as pd
import urllib.parse

from xml.dom.minidom import parseString

class Channel:
    def __init__(self, channel_title, abbreviation, owner_email, author, description, img_href, channel_url):
        self._channel_title = channel_title
        self._abbreviation = abbreviation
        self._owner_email = owner_email
        self._author = author
        self._description = description
        self._img_href = img_href
        self._channel_url = channel_url
        self._article_dict = {}
        self._load_list_datetime = dt(1900, 1, 1, 0, 0, 0)
        self._load_articles_datetime = dt(1900, 1, 1, 0, 0, 0)
        self._episodes = []
        self._master_csv = "csv/" + self._abbreviation + "_master.csv"
        self._rss_file = "docs/" + self._abbreviation + ".rss"
    
    # ラジオページから記事タイトルとURLのリストを読み込む
    def get_article_list(self):
        self._load_list_datetime = dt.now()
        page = 1
        flag = True
        while flag is True:
            # url = self._channel_url + str(page) + "/"
            url = self._channel_url + str(page) + "/?sort=old"
            print("Getting episode list from " + urllib.parse.unquote(url) + "...")
            try:
                res = requests.get(url)
            except requests.exceptions.HTTPError:
                res.raise_for_status()
                print(res.text)
                flag = False
                continue
            soup = BeautifulSoup(res.text, "html.parser")
            boxes = soup.select('div[class="box"]')
            if len(boxes) < 1:
                break
            for box in boxes:
                links = box.find_all('a', attrs = {'href': re.compile(r'^(https://omocoro.jp/).*[0-9]+')})
                if len(links) < 2:
                    continue
                else:
                    article_url = links[0].get('href')
                    article_title = links[1].text
                    self._article_dict[article_title] = article_url
            page += 1

        return True
    
    # 読み込み済みの記事かどうかを判別する
    def check_article_duplication(self, url):
        duplication = False
        article_urls = []
        for ep in self._episodes:
            article_urls.append(ep.article_url)
        if url in article_urls:
            duplication = True

        return duplication
    
    # 読み込み済みのエピソードかどうかを判別する
    def check_episode_duplication(self, episode):
        duplication = False
        if episode in self._episodes:
            duplication = True
        return duplication
    
    # 記事ページを読み込み
    def load_article(self, url):
        atcl = article.Article(url)
        for ep in atcl.episodes():
            if ep not in self._episodes:
                self._episodes.append(ep)
        
        return True
    
    # CSVから読み込み
    def load_csv(self):
        eps = pd.read_csv(self._master_csv, encoding='utf8', index_col=0)

        for id, title, pub_date, description, mp3_url, article_url in zip(eps.index, eps['title'], eps['pub_date'], eps['description'], eps['mp3_url'], eps['article_url']):
            ep = article.Episode(
                int(id),
                title,
                dt.strptime(pub_date, '%Y-%m-%d %H:%M:%S'),
                description,
                mp3_url,
                article_url
                )
            if ep not in self._episodes:
                self._episodes.append(ep)

        return True
    
    # CSVに書き込み
    def save_csv(self):
        ids = []
        channels = []
        titles = []
        descriptions = []
        pub_dates = []
        mp3_urls = []
        article_urls = []

        self._episodes.sort()

        for ep in self._episodes:
            ids.append(ep.id)
            channels.append(self._channel_title)
            titles.append(ep.title)
            descriptions.append(ep.description)
            pub_dates.append(ep.pub_date)
            mp3_urls.append(ep.mp3_url)
            article_urls.append(ep.article_url)
                            
        episodes_df = pd.DataFrame(
            {'channel': channels,
             'title': titles,
             'description': descriptions,
             'pub_date': pub_dates,
             'mp3_url': mp3_urls,
             'article_url': article_urls},
             index = ids
        )

        episodes_df.sort_values('pub_date')
        episodes_df.to_csv(self._master_csv)

        return True
    
    # 全記事を読み込み直す
    def refresh(self):
        self._article_dict.clear()
        self.get_article_list()
        self._episodes.clear()
        for title, url in self._article_dict.items():
            self.load_article(url)
        
        self.save_csv()
        return True

    # まだ読み込んでいない記事のみ読み込む
    def update(self):
        self._article_dict.clear()
        self.get_article_list()
        self._episodes.clear()
        self.load_csv()

        for title, url in self._article_dict.items():
            if self.check_article_duplication(url) is False:
                self.load_article(url)
        
        self.save_csv()
        return True
    
    # rssに書き出す
    def make_rss(self):
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
        dom = parseString(xml_template)

        channel = dom.getElementsByTagName("channel")[0]

        channel.getElementsByTagName("title")[0].firstChild.data = self._channel_title
        channel.getElementsByTagName("itunes:email")[0].firstChild.data = self._owner_email
        channel.getElementsByTagName("itunes:author")[0].firstChild.data = self._author
        channel.getElementsByTagName("description")[0].firstChild.data = self._description
        channel.getElementsByTagName("itunes:image")[0].attributes["href"].value = self._img_href
        channel.getElementsByTagName("link")[0].firstChild.data = self._channel_url

        for episode in self._episodes:
            item = dom.createElement('item')
            channel.appendChild(item)
            # タイトルの設定
            title_node = dom.createElement('title')
            title_node.appendChild(dom.createTextNode(episode.title))
            item.appendChild(title_node)
            # 説明文の設定
            description_node = dom.createElement('description')
            description_node.appendChild(dom.createTextNode(str(episode.description)))
            item.appendChild(description_node)
            # 公開日の設定
            pubdate_node = dom.createElement('pubDate')
            pubdate_str = episode.pub_date.strftime('%a, %d %b %Y %H:%M:%S +0900')
            pubdate_node.appendChild(dom.createTextNode(pubdate_str))
            item.appendChild(pubdate_node)
            # mp3のURL
            enclosure_node = dom.createElement('enclosure')
            url_attr = dom.createAttribute('url')
            url_attr.value = str(episode.mp3_url)
            enclosure_node.setAttributeNode(url_attr)
            type_attr = dom.createAttribute('type')
            type_attr.value = "audio/mpeg"
            enclosure_node.setAttributeNode(type_attr)
            item.appendChild(enclosure_node)
            # GUID(記事URL)
            guid_node = dom.createElement('guid')
            guid_node.appendChild(dom.createTextNode(str(episode.article_url)))
            is_link_attr = dom.createAttribute('isPermaLink')
            is_link_attr.value = "True"
            guid_node.setAttributeNode(is_link_attr)
            item.appendChild(guid_node)

        with open(self._rss_file, "w") as file:
            file.write(dom.toprettyxml(indent = "  "))