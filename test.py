# -*- coding: utf-8 -*-
import radio_page as rp
import pandas as pd

channel_df = pd.read_excel('csv/omcr_radio.xlsx', sheet_name='channel', index_col=0)
radiopage_df = pd.read_excel('csv/omcr_radio.xlsx', sheet_name='radio_page', index_col=0)



