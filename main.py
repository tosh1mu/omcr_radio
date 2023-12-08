# -*- coding: utf-8 -*-
import pandas as pd

import omcr
import podcast

img_src = "https://tosh1mu.github.io/omcr_radio/img/"
owner_email = "namikibashi1987@gmail.com"
author = "Namikibashi"

channel_df = pd.read_excel('omcr_db.xlsx', sheet_name='channel', index_col=0)

for title, abb, description, logo_filename, tags, status in zip(channel_df['title'], channel_df['abbreviation'], channel_df['description'], channel_df['logo_filename'], channel_df['tags'], channel_df['status']):
    tag_list = tags.split(',')
    episodes = []
    for tag in tag_list:
        tag_handler = omcr.TagHandler(tag)
        load_flag = tag_handler.load()
        if load_flag is True:
            if status == 'active':
                tag_handler.update()
        else:
            tag_handler.refresh()
        tag_handler.save()
        for article in tag_handler.articles:
            for episode in article.get_episodes():
                episodes.append(episode)
    
    img_href = img_src + logo_filename
    channel_url = "https://omocoro.jp/tag/" + tag_list[0]

    rss_path = "docs/" + abb + ".rss"

    channel_podcast = podcast.Podcast(title, owner_email, author, description, img_href, channel_url)
    for episode in episodes:
        channel_podcast.add_episode(
            episode.title,
            episode.description,
            episode.pub_date,
            episode.mp3_url,
            episode.article_url
        )
    channel_podcast.create_rss(rss_path)
