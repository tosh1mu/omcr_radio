import requests
from bs4 import BeautifulSoup
import re

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
    print("***Page: " + str(page) + "***")
    
    for box in boxes:
        links = box.find_all('a', attrs={ 'href': re.compile(r'.*radio.*') })
        if len(links) < 2:
            continue
        else:
            radio_page_url = links[0].get('href')
            radio_title = links[1].text
            print(radio_title + ": " + radio_page_url)
    page += 1