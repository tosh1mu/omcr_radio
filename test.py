# -*- coding: utf-8 -*-
import channel

tokumei_channel = channel.Channel(
    "Tokumei Radio",
    "tokumei",
    "namikibashi1987@gmail.com",
    "Tokumei Radio",
    "Just personal use.",
    "https://podcast.namikibashi.net/tokumei/artwork/tokumei_logo_1400.jpg",
    "https://omocoro.jp/tag/%E5%8C%BF%E5%90%8D%E3%83%A9%E3%82%B8%E3%82%AA/page/"
)

# tokumei_channel.get_episode_list()
# tokumei_channel.get_all_episodes()

tokumei_channel.make_rss()