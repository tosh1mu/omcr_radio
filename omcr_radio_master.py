# -*- coding: utf-8 -*-
import pandas as pd

class OmcrRadioMaster:
    def __init__(self, db_file, channel_sheet = 'channel', radiopage_sheet = 'radio_page', mp3_sheet = 'mp3'):
        self._channel_df = pd.read_excel(db_file, sheet_name=channel_sheet, index_col=0)
        self._radiopage_df = pd.read_excel(db_file, sheet_name=radiopage_sheet, index_col=0)
        self._mp3_df = pd.read_excel(db_file, sheet_name=mp3_sheet, index_col=0)
        return True
    
    ## DB上にラジオページが登録されているか判定する
    def check_page(self, page_url):
        return True
    
    ## DB上にmp3が登録されているか判定する
    def check_mp3(self, mp3_url):
        return True
    
    ## mp3を登録する
    def append_mp3(self, mp3_url):
        return True

    ## ラジオページを登録する
    def append_page(self, page_url):
        return True
    
    ## 全ラジオをアップデートする
    def update_whole(self):
        return True
    
    ## 更新中のラジオのみアップデートする
    def update_active(self):
        return True
    
    ## タグを指定してDBをアップデートする
    def update_tag(self, tag):
        return True
    
    ## タグを指定してRSSを生成する
    def create_rss_tag(self, tag):
        return True

    ## 更新中のラジオのみRSSを更新する
    def create_rss_active(self, tag):
        return True
    
    ## DBに書き出す
    def save(self):
        return True