# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python scraper and RSS podcast feed generator for Omocoro (omocoro.jp) radio shows. Scrapes article pages, extracts MP3 links, and generates iTunes-compatible RSS 2.0 feeds served via GitHub Pages from `docs/`. Channel configuration is stored in `omcr_db.xlsx` (sheet `channel`).

## Running

```bash
source myenv/bin/activate
python main.py
```

Output: RSS files written to `docs/{abbreviation}.rss`, pickle caches to `pickles/`. There are no tests or linters.

## Dependencies

No requirements.txt exists. Install manually:
```bash
pip install beautifulsoup4 requests pandas openpyxl
```

## Automation

`.github/workflows/update-rss.yml` runs `main.py` daily (cron `0 20 * * *` UTC = 5:00 JST, plus manual `workflow_dispatch`) and commits any changes to `docs/` and `pickles/` as "Update RSS feeds and caches". Most commits in history are these bot commits.

## Architecture

Three modules with clear separation:

- **main.py** — Entry point and orchestration. Loads channel config from Excel (`omcr_db.xlsx`), iterates channels, collects episodes via `TagHandler`, deduplicates by `article_url`, and writes RSS feeds via `Podcast`. `Config` dataclass holds hardcoded settings (image URL base `https://tosh1mu.github.io/omcr_radio/img/`, owner email, author, paths).

- **omcr.py** — Web scraping layer. `TagHandler` manages episode collection per tag with pickle-based caching (MD5 of tag name as filename). `ArticleList` fetches paginated tag listings from omocoro.jp, keeping only boxes whose category is "ラジオ". `RadioPage` parses individual article pages to extract title, date, description, and MP3 URLs, producing frozen `Episode` dataclass instances. A single article can yield multiple episodes (one per MP3); each episode's `pub_date` is offset by `i+1` seconds to preserve ordering. Also contains a self-rolled MP3 duration estimator (`get_mp3_duration`) that fetches the first 16KB via HTTP Range requests and parses frame headers (Xing/VBR or CBR estimate); failures return 0 ("unknown").

- **podcast.py** — RSS generation. `Podcast` class builds XML DOM (via `xml.dom.minidom`) with iTunes podcast extensions. `ChannelInfo` and `EpisodeInfo` dataclasses carry metadata. Outputs `.rss` files with `audio/mpeg` enclosures, `guid` set to the article URL, and `itunes:duration` when duration > 0.

## Data Flow

`omcr_db.xlsx` → channels → `TagHandler.update()`/`refresh()` (scrape + cache) → `RadioPage.get_episodes()` → deduplicate by `article_url` → `Podcast.create_rss()` → `docs/{abbreviation}.rss`

## Caching

- `TagHandler` objects are serialized to `pickles/` as pickle files (via `pd.to_pickle`); pickles are committed to git
- Channel `status` field controls behavior: `active` runs `update()` (crawl new pages until a page yields an already-cached article), any other value (e.g. `end`) loads cache only; a cache miss triggers `refresh()` (full crawl oldest-first, then update)
- `TagHandler.load()` and `_migrate_radio_page()` handle backward-compatibility migration from old pickle attribute names (`_articles`, `_url`, etc.) and fill in missing `mp3_durations`

## Repository Quirks

- The virtualenv `myenv/` is committed to git. Exclude it (and `_archive/`, `__pycache__/`) when searching the codebase.
- `_archive/` contains a legacy pre-refactor version of the scraper; do not modify it.
- `docs/` contains both current `{abbreviation}.rss` feeds and older Japanese-titled `.rss` files that current code no longer writes.

## Key URL Patterns

- Tag listing: `https://omocoro.jp/tag/{tag}/page/{n}/?sort=new`
- Article URLs must match `^https://omocoro\.jp/.*[0-9]+`; the article ID (first number in the URL) is used for sorting
- MP3 links extracted from article pages via BeautifulSoup anchor href pattern `.*.mp3`

## Language

Code comments and scraped content are in Japanese. RSS feeds use `ja-jp` locale.

## Error Handling Conventions

Custom exception hierarchies per module (`OMCRError`/`InvalidURLError`/`FetchError` in omcr.py, `PodcastError`/`RSSGenerationError` in podcast.py). Per-tag, per-episode, and per-channel failures are caught and printed as warnings so one broken page never aborts the whole run.
