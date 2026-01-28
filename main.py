# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
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
                print(f"Tag '{tag}' loaded from cache (status: {status})")
        else:
            print(f"Tag '{tag}' not found in cache, refreshing...")
            tag_handler.refresh()

        tag_handler.save()

        episodes = [
            episode
            for article in tag_handler.articles
            for episode in article.get_episodes()
        ]
        
        print(f"Collected {len(episodes)} episode(s) from tag '{tag}'")
        return episodes
    except Exception as e:
        print(f"Warning: Failed to process tag '{tag}': {e}")
        return []


def build_podcast(channel: Channel, episodes: List[omcr.Episode], config: Config) -> podcast.Podcast:
    img_href = f"{config.img_src}{channel.logo_filename}"
    # 複数タグがある場合は最初のタグを使用（または別の方式に変更可能）
    primary_tag = channel.tags[0] if channel.tags else "unknown"
    channel_url = f"https://omocoro.jp/tag/{primary_tag}"

    pod = podcast.Podcast(
        channel.title,
        config.owner_email,
        config.author,
        channel.description,
        img_href,
        channel_url,
    )

    if not episodes:
        print(f"Warning: No episodes found for channel '{channel.title}'")

    for episode in sorted(episodes, reverse=True):
        try:
            pod.add_episode(
                episode.title,
                episode.description,
                episode.pub_date,
                episode.mp3_url,
                episode.article_url,
            )
        except Exception as e:
            print(f"Warning: Failed to add episode '{episode.title}': {e}")

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

    # 重複排除（article_url で一意性を保証）
    seen_urls = set()
    unique_episodes = []
    for episode in episodes:
        if episode.article_url not in seen_urls:
            unique_episodes.append(episode)
            seen_urls.add(episode.article_url)

    unique_episodes.sort(reverse=True)  # 新しい順にソート

    pod = build_podcast(channel, unique_episodes, config)
    save_podcast(pod, channel, config)


@dataclass
class ProcessStats:
    """処理統計情報"""
    processed_channels: int = 0
    successful_channels: int = 0
    failed_channels: int = 0
    total_episodes: int = 0
    total_unique_episodes: int = 0


def main() -> None:
    config = Config()
    stats = ProcessStats()

    try:
        channels = load_channels(config.db_path)
        stats.processed_channels = len(channels)

        for channel in channels:
            try:
                process_channel(channel, config)
                stats.successful_channels += 1
            except Exception as e:
                print(f"Error processing channel '{channel.title}': {e}")
                stats.failed_channels += 1

        # 処理結果のサマリー表示
        print("\n" + "="*50)
        print(f"Processing completed:")
        print(f"  Processed channels: {stats.processed_channels}")
        print(f"  Successful: {stats.successful_channels}")
        print(f"  Failed: {stats.failed_channels}")
        print("="*50)

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
