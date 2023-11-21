# -*- coding: utf-8 -*-
import radio_page as rp
import pandas as pd

test_url = "https://omocoro.jp/radio/396342/"

test_page = rp.RadioPage(test_url)

pd.to_pickle(test_page, "test.pkl")

read_test = pd.read_pickle("test.pkl")
print(read_test.mp3_urls)

channel_df = pd.read_excel('csv/omcr_radio.xlsx', sheet_name='channel', index_col=0)
print(channel_df)

radiopage_df = pd.read_excel('csv/omcr_radio.xlsx', sheet_name='radio_page', index_col=0)
print(radiopage_df)



