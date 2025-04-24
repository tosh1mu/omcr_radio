# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path
from typing import List, Tuple
import omcr
import podcast

class Config:
    IMG_SRC = "https://tosh1mu.github.io/omcr_radio/img/"
    OWNER_EMAIL = "namikibashi1987@gmail.com"
    AUTHOR = "Namikibashi"
    DB_PATH = "omcr_db.xlsx"
    OUTPUT_DIR = "docs"

def load_channel_data() -> pd.DataFrame:
    try:
        return pd.read_excel(Config.DB_PATH, sheet_name='channel', index_col=0)
    except Exception as e:
        raise RuntimeError(f'Failed to load channel data: {str(e)}')

def process_tag(tag: str, status: str) -> List[omcr.Episode]:
    tag_handler = omcr.TagHandler(tag)
    
    try:
        if tag_handler.load():
            if status == 'active':
                tag_handler.update()
        else:
            tag_handler.refresh()
        
        tag_handler.save()
        
        episodes = []
        for article in tag_handler.articles:
            episodes.extend(article.get_episodes())
        return episodes
    except Exception as e:
        print(f'Warning: Failed to process tag {tag}: {str(e)}')
        return []

def create_podcast(
    title: str,
    description: str,
    logo_filename: str,
    tag_list: List[str],
    episodes: List[omcr.Episode]
) -> None:
    img_href = f"{Config.IMG_SRC}{logo_filename}"
    channel_url = f"https://omocoro.jp/tag/{tag_list[0]}"
    rss_path = Path(Config.OUTPUT_DIR) / f"{tag_list[0]}.rss"

    channel_podcast = podcast.Podcast(
        title,
        Config.OWNER_EMAIL,
        Config.AUTHOR,
        description,
        img_href,
        channel_url
    )

    for episode in episodes:
        channel_podcast.add_episode(
            episode.title,
            episode.description,
            episode.pub_date,
            episode.mp3_url,
            episode.article_url
        )

    try:
        channel_podcast.create_rss(str(rss_path))
    except podcast.RSSGenerationError as e:
        print(f'Warning: Failed to create RSS for {title}: {str(e)}')

def main() -> None:
    try:
        channel_df = load_channel_data()
        
        for _, row in channel_df.iterrows():
            tag_list = row['tags'].split(',')
            episodes = []
            
            for tag in tag_list:
                episodes.extend(process_tag(tag, row['status']))
            
            create_podcast(
                row['title'],
                row['description'],
                row['logo_filename'],
                tag_list,
                episodes
            )
    except Exception as e:
        print(f'Error: {str(e)}')
        raise

if __name__ == '__main__':
    main()
