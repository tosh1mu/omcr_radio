# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python scraper and RSS podcast feed generator for Omocoro (omocoro.jp) radio shows. Scrapes article pages, extracts MP3 links, and generates iTunes-compatible RSS 2.0 feeds. Channel configuration is stored in `omcr_db.xlsx`.

## Running

```bash
source myenv/bin/activate
python main.py
```

Output: RSS files written to `docs/`, pickle caches to `pickles/`.

## Dependencies

No requirements.txt exists. Install manually:
```bash
pip install beautifulsoup4 requests pandas openpyxl
```

## Architecture

Three modules with clear separation:

- **main.py** — Entry point and orchestration. Loads channel config from Excel (`omcr_db.xlsx`), iterates channels, collects episodes via `TagHandler`, deduplicates, and writes RSS feeds via `Podcast`. `Config` dataclass holds hardcoded settings (image URL base, email, author, paths).

- **omcr.py** — Web scraping layer. `TagHandler` manages episode collection per tag with pickle-based caching (MD5 of tag name as filename). `ArticleList` fetches paginated tag listings from omocoro.jp, filtering for radio content. `RadioPage` parses individual article pages to extract title, date, description, and MP3 URLs, producing `Episode` dataclass instances. A single article can yield multiple episodes (one per MP3).

- **podcast.py** — RSS generation. `Podcast` class builds XML DOM (via `xml.dom.minidom`) with iTunes podcast extensions. `ChannelInfo` and `EpisodeInfo` dataclasses carry metadata. Outputs `.rss` files with `audio/mpeg` enclosures.

## Data Flow

`omcr_db.xlsx` → channels → `TagHandler.update()` (scrape + cache) → `Episode` objects → deduplicate by `article_url` → `Podcast.create_rss()` → `docs/{abbreviation}.rss`

## Caching

- `TagHandler` objects are serialized to `pickles/` as pickle files
- Channel `status` field controls behavior: `active` runs `update()` (fetch latest), `end` loads cache only
- `TagHandler` has backward-compatibility migration for old pickle attribute names

## Key URL Patterns

- Tag listing: `https://omocoro.jp/tag/{tag}/page/{n}/?sort=new`
- Articles contain MP3 links extracted via BeautifulSoup (`a[href$=".mp3"]`)

## Language

Code comments and scraped content are in Japanese. RSS feeds use `ja-jp` locale.
