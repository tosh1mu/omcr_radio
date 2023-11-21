# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

class ListPage:
    def __init__(self, base_url, page = 1, sort = "new", link_pattern = r''):
        self._page_url = base_url + "page/" + page + "/?sort=" + sort
        self._link_dict = {}
        self.get_list(link_pattern)
    
    @property
    def url(self):
        return self._page_url
    
    def get_list(self, pattern = r''):
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
                links = box.find_all('a', attrs = {'href': pattern})
                if len(links) < 2:
                    continue
                else:
                    url = links[0].get('href')
                    title = str(links[1].text)
                    self._link_dict[title] = url
        return True
    
    def links(self):
        return list(self._link_dict.values())