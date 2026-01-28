# -*- coding: utf-8 -*-
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd

import omcr
import podcast


@dataclass(frozen=True)
class Config:
    img_src: str = "https://tosh1mu.github.io/omcr_radio/img/"
    owner_email: str = "namikibashi1987@gmail.com"
    author: str = "Namikibashi"
    db_path: str = "omcr_db.xlsx"
    output_dir: str = "docs"


@dataclass
class Channel:
    title: str
    abbreviation: str
    description: str
    logo_filename: str
    tags: List[str]
    status: str

    @classmethod
    def from_row(cls, row: pd.Series) -> "Channel":
        return cls(
            title=row["title"],
            abbreviation=row["abbreviation"],
            description=row["description"],
            logo_filename=row["logo_filename"],
            tags=row["tags"].split(","),
            status=row["status"],
        )


def load_channels(db_path: str) -> List[Channel]:
    try:
        df = pd.read_excel(db_path, sheet_name="channel", index_col=0)
        return [Channel.from_row(row) for _, row in df.iterrows()]
    except Exception as e:
        raise RuntimeError(f"Failed to load channel data: {e}") from e


def collect_episodes(tag: str, status: str) -> List[omcr.Episode]:
    tag_handler = omcr.TagHandler(tag)

    try:
        if tag_handler.load():
            if status == "active":
                tag_handler.update()
        else:
            tag_handler.refresh()

        tag_handler.save()

        return [
            episode
            for article in tag_handler.articles
            for episode in article.get_episodes()
        ]
    except Exception as e:
        print(f"Warning: Failed to process tag {tag}: {e}")
        return []


def build_podcast(channel: Channel, episodes: List[omcr.Episode], config: Config) -> podcast.Podcast:
    img_href = f"{config.img_src}{channel.logo_filename}"
    channel_url = f"https://omocoro.jp/tag/{channel.tags[0]}"

    pod = podcast.Podcast(
        channel.title,
        config.owner_email,
        config.author,
        channel.description,
        img_href,
        channel_url,
    )

    for episode in episodes:
        pod.add_episode(
            episode.title,
            episode.description,
            episode.pub_date,
            episode.mp3_url,
            episode.article_url,
        )

    return pod


def save_podcast(pod: podcast.Podcast, channel: Channel, config: Config) -> None:
    rss_path = Path(config.output_dir) / f"{channel.abbreviation}.rss"

    try:
        pod.create_rss(str(rss_path))
        print(f"Created/Updated RSS file: {rss_path}")
    except podcast.RSSGenerationError as e:
        print(f"Warning: Failed to create RSS for {channel.title}: {e}")


def process_channel(channel: Channel, config: Config) -> None:
    episodes = [
        episode
        for tag in channel.tags
        for episode in collect_episodes(tag, channel.status)
    ]

    pod = build_podcast(channel, episodes, config)
    save_podcast(pod, channel, config)


def main() -> None:
    config = Config()

    try:
        channels = load_channels(config.db_path)
        for channel in channels:
            process_channel(channel, config)
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
