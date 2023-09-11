# -*- coding: utf-8 -*-
import channel

img_src = "https://tosh1mu.github.io/omcr_radio/img/"

tokumei_channel = channel.Channel(
    "Tokumei Radio",
    "tokumei",
    "namikibashi1987@gmail.com",
    "Tokumei Radio",
    "Just personal use.",
    img_src + "tokumei_logo.jpg",
    "https://omocoro.jp/tag/%E5%8C%BF%E5%90%8D%E3%83%A9%E3%82%B8%E3%82%AA/page/"
)
# tokumei_channel.refresh()
tokumei_channel.update()
tokumei_channel.make_rss()

onsei_channel = channel.Channel(
    "Onsei Housou",
    "onsei",
    "namikibashi1987@gmail.com",
    "Onsei Housou",
    "Just personal use.",
    img_src + "onsei_logo.jpg",
    "https://omocoro.jp/tag/%E9%9F%B3%E5%A3%B0%E6%94%BE%E9%80%81/page/"
)
# onsei_channel.refresh()
onsei_channel.update()
onsei_channel.make_rss()

mnf_channel = channel.Channel(
    "MNF",
    "mnf",
    "namikibashi1987@gmail.com",
    "MNF",
    "Just personal use.",
    img_src + "mnf_logo.jpg",
    "https://omocoro.jp/tag/%E3%83%A2%E3%83%B3%E3%82%B4%E3%83%AB%E3%83%8A%E3%82%A4%E3%83%88%E3%83%95%E3%82%A3%E3%83%BC%E3%83%90%E3%83%BC/page/"
)
# mnf_channel.refresh()
mnf_channel.update()
mnf_channel.make_rss()

now_channel = channel.Channel(
    "NOW",
    "now",
    "namikibashi1987@gmail.com",
    "NOW",
    "Just personal use.",
    img_src + "now_logo.jpg",
    "https://omocoro.jp/tag/%E3%83%8B%E3%83%A5%E3%83%BC%E3%82%B9%EF%BC%81%E3%82%AA%E3%83%A2%E3%82%B3%E3%83%AD%E3%82%A6%E3%82%A9%E3%83%83%E3%83%81%EF%BC%81/page/"
)
# now_channel.refresh()
now_channel.update()
now_channel.make_rss()

ariari_channel = channel.Channel(
    "Ari Ari",
    "ariari",
    "namikibashi1987@gmail.com",
    "Ari Ari",
    "Just personal use.",
    img_src + "ariari_logo.jpg",
    "https://omocoro.jp/tag/%E3%81%82%E3%82%8A%E3%81%A3%E3%81%A1%E3%82%83%E3%81%82%E3%82%8A%E3%82%A2%E3%83%AF%E3%83%BC/page/"
)
# ariari_channel.refresh()
ariari_channel.update()
ariari_channel.make_rss()
