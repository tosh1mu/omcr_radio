# -*- coding: utf-8 -*-
# 番組を扱うためのクラス定義
import requests
from datetime import datetime as dt
from bs4 import BeautifulSoup
import episode
import re
import pandas as pd

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
        self._episode_dict = {}
        self._load_list_datetime = dt(1900, 1, 1, 0, 0, 0)
        self._load_episodes_datetime = dt(1900, 1, 1, 0, 0, 0)
        self._master_csv = self._abbreviation + "_master.csv"
        self._rss_file = self._abbreviation + ".rss"
    
    # ラジオページからエピソードタイトルとURLのリストを読み込む
    def get_episode_list(self):
        self._load_list_datetime = dt.now()
        page = 1
        flag = True
        while flag is True:
            url = self._channel_url + str(page) + "/"
            print("Getting episode list from " + url + "...")
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
                    radio_page_url = links[0].get('href')
                    radio_title = links[1].text
                    self._episode_dict[radio_title] = radio_page_url
            page += 1

        return True

    # 全てのエピソードを取得
    def get_all_episodes(self):
        self._load_episodes_datetime = dt.now()

        ids = []
        channels = []
        titles = []
        descriptions = []
        pub_dates = []
        mp3_urls = []
        episode_urls = []

        self.get_episode_list()

        for title, url in self._episode_dict.items():
            ep = episode.Episode(url)
            ep_data = ep.data()
            print("Loading " + ep_data.title)
            ids.append(ep_data.id)
            channels.append(self._channel_title)
            titles.append(ep_data.title)
            descriptions.append(ep_data.description)
            pub_dates.append(ep_data.pub_date)
            mp3_urls.append(ep_data.mp3_url)
            episode_urls.append(url)

        all_episodes = pd.DataFrame(
            {'channel': channels,
             'title': titles,
             'description': descriptions,
             'pub_date': pub_dates,
             'mp3_url': mp3_urls,
             'episode_url': episode_urls},
             index = ids
        )

        all_episodes.sort_values('pub_date')
        all_episodes.to_csv(self._master_csv)
        
        return True

    # 新しいエピソードを取得
    def get_new_episodes(self):
        existing_episodes = pd.read_csv(self._master_csv, encoding='utf8', index_col=0)
        self.get_episode_list()

        new_ids = []
        new_channels = []
        new_titles = []
        new_descriptions = []
        new_pub_dates = []
        new_mp3_urls = []
        new_episode_urls = []

        for title, url in self._episode_dict.items():
            if url in existing_episodes['episode_url'].values:
                continue
            else:
                new_ep = episode.Episode(url)
                new_ep_data = new_ep.data()
                print("Loading " + new_ep_data.title)
                new_ids.append(new_ep_data.id)
                new_channels.append(self._channel_title)
                new_titles.append(new_ep_data.title)
                new_descriptions.append(new_ep_data.description)
                new_pub_dates.append(new_ep_data.pub_date.strftime('%Y-%m-%d'))
                new_mp3_urls.append(new_ep_data.mp3_url)
                new_episode_urls.append(url)
        
        updated_episodes = existing_episodes

        if len(new_ids) > 0:
            new_episodes = pd.DataFrame(
                {'channes': new_channels,
                 'title': new_titles,
                 'description': new_descriptions,
                 'pub_date': new_pub_dates,
                 'mp3_url': new_mp3_urls,
                 'episode_url': new_episode_urls},
                 index = new_ids
            )
            updated_episodes = pd.concat([existing_episodes, new_episodes])
        
        updated_episodes.sort_values('pub_date')
        updated_episodes.to_csv(self._master_csv)

        return True
    
    # rssに書き出す
    def make_rss(self):
        episodes = pd.read_csv(self._master_csv, encoding='utf8', index_col=0)
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

        for title, description, pub_date, mp3_url, episode_url in zip(episodes['title'], episodes['description'], episodes['pub_date'], episodes['mp3_url'], episodes['episode_url']):
            item = dom.createElement('item')
            channel.appendChild(item)
            # タイトルの設定
            title_node = dom.createElement('title')
            title_node.appendChild(dom.createTextNode(title))
            item.appendChild(title_node)
            # 説明文の設定
            description_node = dom.createElement('description')
            description_node.appendChild(dom.createTextNode(str(description)))
            item.appendChild(description_node)
            # 公開日の設定
            pubdate_node = dom.createElement('pubDate')
            pubdate = dt.strptime(pub_date, '%Y-%m-%d')
            pubdate_str = pubdate.strftime('%a, %d %b %Y %H:%M:%S +0900')
            pubdate_node.appendChild(dom.createTextNode(pubdate_str))
            item.appendChild(pubdate_node)
            # mp3のURL
            enclosure_node = dom.createElement('enclosure')
            url_attr = dom.createAttribute('url')
            url_attr.value = str(mp3_url)
            enclosure_node.setAttributeNode(url_attr)
            type_attr = dom.createAttribute('type')
            type_attr.value = "audio/mpeg"
            enclosure_node.setAttributeNode(type_attr)
            item.appendChild(enclosure_node)
            # GUID(記事URL)
            guid_node = dom.createElement('guid')
            guid_node.appendChild(dom.createTextNode(str(episode_url)))
            is_link_attr = dom.createAttribute('isPermaLink')
            is_link_attr.value = "True"
            guid_node.setAttributeNode(is_link_attr)
            item.appendChild(guid_node)

        with open(self._rss_file, "w") as file:
            file.write(dom.toprettyxml(indent = "  "))