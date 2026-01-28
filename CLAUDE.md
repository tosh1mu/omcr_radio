# CLAUDE.md - AI Assistant Guide for omcr_radio

## Project Overview

**omcr_radio** is a Python-based podcast/RSS feed generator that scrapes radio episodes from [omocoro.jp](https://omocoro.jp) (a Japanese comedy media platform), organizes them by channel/tag, and generates iTunes-compatible RSS feeds for podcast distribution.

### Key Functionality
- Fetches radio episodes from omocoro.jp tag pages
- Caches article data using pickle serialization
- Generates iTunes-compatible RSS feeds with proper metadata
- Supports multiple channels with configurable tags

## Directory Structure

```
omcr_radio/
├── main.py              # Entry point - orchestrates the pipeline
├── omcr.py              # Web scraping and data handling
├── podcast.py           # RSS feed generation
├── omcr_db.xlsx         # Excel database with channel definitions
├── .gitignore           # Git ignore rules
├── CLAUDE.md            # This file
│
├── docs/                # Output directory for generated content
│   ├── *.rss           # Generated RSS feed files (27 files)
│   └── img/            # Channel logo images (PNG/JPG)
│
├── pickles/             # Cache directory for serialized data
│   └── *.pkl           # Pickle files (MD5 hash of tag name)
│
├── _archive/            # Old implementation (gitignored)
│   ├── *.py            # Legacy Python modules
│   ├── csv/            # Historical CSV exports
│   └── rss/            # Old RSS outputs
│
└── myenv/               # Python virtual environment
```

## Architecture

### Module Responsibilities

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `main.py` | Orchestration, config, entry point | `Config`, `Channel`, `main()`, `process_channel()` |
| `omcr.py` | Web scraping, caching, data models | `Episode`, `RadioPage`, `ArticleList`, `TagHandler` |
| `podcast.py` | RSS XML generation | `Podcast`, `ChannelInfo`, `EpisodeInfo` |

### Data Flow

```
omcr_db.xlsx (channel definitions)
       ↓
load_channels() → Parse Excel
       ↓
For each channel:
  ├─ collect_episodes() → Fetch from omocoro.jp/tag/{tag}/
  │   └─ TagHandler.load() / update() / refresh() / save()
  ├─ Deduplicate by article_url
  ├─ build_podcast() → Create Podcast with episodes
  └─ save_podcast() → Write RSS to docs/
       ↓
Output: docs/{abbreviation}.rss
```

## Key Classes

### main.py

- **`Config`** (frozen dataclass): Hardcoded configuration
  - `img_src`: Base URL for channel images
  - `owner_email`, `author`: Podcast metadata
  - `db_path`: Path to Excel database
  - `output_dir`: RSS output directory

- **`Channel`** (dataclass): Channel metadata
  - Created via `Channel.from_row()` factory method
  - Properties: `title`, `abbreviation`, `description`, `logo_filename`, `tags`, `status`

### omcr.py

- **`Episode`** (frozen dataclass): Immutable episode data
- **`RadioPage`**: Represents a single article page with MP3 links
  - Fetches and parses HTML from omocoro.jp
  - `get_episodes()`: Returns list of Episode objects
- **`TagHandler`**: Manages tag-based article collection
  - `update()`: Fetch only new articles
  - `refresh()`: Full refresh from scratch
  - `save()`/`load()`: Pickle-based persistence

### podcast.py

- **`Podcast`**: RSS feed builder using XML DOM
  - `add_episode()`: Add episode to feed
  - `create_rss()`: Write RSS file

## Custom Exceptions

```python
# omcr.py
OMCRError           # Base exception
├── InvalidURLError # Invalid omocoro.jp URLs
└── FetchError      # Network/parsing failures

# podcast.py
PodcastError        # Base exception
└── RSSGenerationError  # RSS file creation failures
```

## Configuration

### omcr_db.xlsx (channel sheet)
| Column | Description |
|--------|-------------|
| `title` | Full channel name |
| `abbreviation` | Short ID (used for RSS filename) |
| `description` | Channel description |
| `logo_filename` | Image file in docs/img/ |
| `tags` | Comma-separated tags for filtering |
| `status` | "active" or "inactive" |

### Hardcoded Config (main.py:12-18)
```python
img_src = "https://tosh1mu.github.io/omcr_radio/img/"
owner_email = "namikibashi1987@gmail.com"
author = "Namikibashi"
db_path = "omcr_db.xlsx"
output_dir = "docs"
```

## Development Workflow

### Prerequisites
- Python 3.11+ (virtual environment in `myenv/`)
- Dependencies: pandas, requests, beautifulsoup4, openpyxl

### Running the Application
```bash
# Activate virtual environment
source myenv/bin/activate

# Run the main script
python main.py
```

### Expected Output
- Updates cache files in `pickles/`
- Generates/updates RSS files in `docs/`
- Prints processing statistics

## Code Conventions

### Style Guidelines
1. **Encoding**: UTF-8 with `# -*- coding: utf-8 -*-` header
2. **Type hints**: Use throughout for function signatures
3. **Dataclasses**: Preferred for data structures
4. **Frozen dataclasses**: Use for immutable data (Config, Episode, etc.)
5. **Comments**: Japanese comments are present (for Japanese audience)

### Naming Conventions
- Classes: PascalCase (`RadioPage`, `TagHandler`)
- Functions/methods: snake_case (`load_channels`, `_parse_page`)
- Private methods: Prefix with underscore (`_fetch_page`)
- Constants: UPPER_SNAKE_CASE (`PICKLE_DIR`, `MP3_LINK_PATTERN`)

### Error Handling Pattern
```python
try:
    # Operation
except SpecificException as e:
    raise CustomError(f"Context: {e}") from e
```

### Caching Strategy
- Pickle files stored in `pickles/`
- Filenames: MD5 hash of tag name
- Backwards compatibility with old attribute names (`_articles` → `articles`)

## Important Patterns

### Episode Deduplication (main.py:129-134)
```python
seen_urls = set()
unique_episodes = []
for episode in episodes:
    if episode.article_url not in seen_urls:
        unique_episodes.append(episode)
        seen_urls.add(episode.article_url)
```

### Backwards Compatibility Migration (omcr.py:263-278)
The codebase maintains compatibility with older pickle formats by migrating old attribute names.

## External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pandas | 2.2.2 | Data manipulation, Excel reading, pickle I/O |
| requests | 2.32.3 | HTTP requests to omocoro.jp |
| beautifulsoup4 | 4.12.3 | HTML parsing |
| openpyxl | 3.1.5 | Excel file handling |

## Important Notes for AI Assistants

### Do's
- Keep the modular structure (main, omcr, podcast separation)
- Use dataclasses for new data structures
- Add type hints to all new functions
- Handle errors gracefully with custom exceptions
- Maintain backwards compatibility for pickle files
- Test changes with inactive channels first (less network requests)

### Don'ts
- Don't modify files in `_archive/` (historical reference only)
- Don't commit pickle files to git (cache only)
- Don't hardcode new configuration - add to Config class
- Don't remove backwards compatibility code without migration plan
- Don't make requests without proper error handling

### Common Tasks

**Add a new channel:**
1. Add entry to `omcr_db.xlsx` channel sheet
2. Add logo image to `docs/img/`
3. Run `python main.py`

**Force refresh a tag's cache:**
1. Delete the corresponding pickle file in `pickles/`
2. Run the script (will trigger full refresh)

**Debug a specific channel:**
```python
# In Python shell
from main import Config, load_channels, process_channel
config = Config()
channels = load_channels(config.db_path)
channel = [c for c in channels if c.abbreviation == "target"][0]
process_channel(channel, config)
```

## Testing

Currently no automated tests exist. Manual testing approach:
1. Set channel status to "inactive" for testing (uses cache only)
2. Verify RSS output format
3. Check pickle file persistence

## Git Workflow

- Main branch contains production code
- Feature branches for development
- `_archive/` directory is gitignored
- RSS files in `docs/` are committed (published via GitHub Pages)
