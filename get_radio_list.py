# -*- coding: utf-8 -*-
import datetime
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

# 番組ページからURLリストを返すクラス
# ラジオページから情報を返すクラス

dt_now = datetime.datetime.now()
dt_now_str = dt_now.strftime('%Y%m%d_%H%M%S')
csv_name = "omcr_radio_list_" + dt_now_str + ".csv"

col_names = ['series', 'title', 'description', 'pub_date', 'mp3_url', 'page_url']

id_list = []
series_list = []
title_list = []
description_list = []
date_list = []
mp3_url_list = []
page_url_list = []

tokumei_url_base = "https://omocoro.jp/tag/%E5%8C%BF%E5%90%8D%E3%83%A9%E3%82%B8%E3%82%AA/page/"
mnf_url_base = ""
onsei_url_base = ""
ariari_url_base = ""
news_url_base = ""

base_url = "https://omocoro.jp/radio/page/"
url_postfix = "/?sort=new"

flag = True

page = 1

while flag is True:
    url = base_url + str(page) + url_postfix
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
        links = box.find_all('a', attrs={ 'href': re.compile(r'.*radio.*') })
        if len(links) < 2:
            continue
        else:
            radio_page_url = links[0].get('href')
            radio_title = links[1].text
            print("Getting " + radio_title + " from " + radio_page_url + "...")
            try:
                radio_page = requests.get(radio_page_url)
            except requests.exceptions.HTTPError:
                radio_page.raise_for_status()
                print(radio_page.text)
                continue
            page_soup = BeautifulSoup(radio_page.text, "html.parser")
            # 記事番号をインデックスとして取得
            id = re.findall('[0-9]+', radio_page_url)[0]
            id_list.append(id)
            # 記事タイトルを取得
            title = page_soup.select('div[class="title"]')[0].text
            title_list.append(radio_title)
            # 番組名をタグから取得
            series = ""
            tags = page_soup.select('div[class="tags"]')[0]
            tag_list = tags.find_all('a')
            for tag in tag_list:
                if tag.text != "#ラジオ":
                    series = tag.text.replace('#', '')
            series_list.append(series)
            # 公開日を取得
            date = page_soup.select('div[class="date"]')[0].text
            date_list.append(date)
            # 説明文を取得
            description = page_soup.select('div[class="description"]')[0].text
            description_list.append(date)
            # mp3のURLを取得
            mp3_url = page_soup.find('a', attrs={ 'href': re.compile(r'.*.mp3') }).get('href') if page_soup.find('a', attrs={ 'href': re.compile(r'.*.mp3') }) else ''
            mp3_url_list.append(mp3_url)
            # 記事ページのURLをリストに追加
            page_url_list.append(radio_page_url)
            
    page += 1

data = pd.DataFrame(
    {'series': series_list,
     'title': title_list,
     'description': description_list,
     'pub_date': date_list,
     'mp3_url': mp3_url_list,
     'page_url': page_url_list},
    index = id_list,
)

data.to_csv(csv_name)