# -*- coding: utf-8 -*-
from datetime import datetime as dt
import datetime
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import pandas as pd

import omcr

# channel_df = pd.read_excel('csv/omcr_radio.xlsx', sheet_name='channel', index_col=0)
# radiopage_df = pd.read_excel('csv/omcr_radio.xlsx', sheet_name='radio_page', index_col=0)

tokumei = omcr.TagHandler('ニュース！オモコロウォッチ！')
tokumei.refresh()