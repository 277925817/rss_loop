# 02_arch.md

## 1. Technology Stack（技术栈）

- Frontend: React + Vite
- Backend: Python FastAPI
- Database: SQLite
- Scheduler: In-process backend scheduler
- LLM: Structured JSON scoring and translation calls
- RSS parsing / scraping tools: RSS/XML parser, HTML content extractor

## 2. High-Level Architecture（整体架构）

The MVP runs as a single FastAPI application on one machine. The frontend is a React + Vite single-page app that reads data from the FastAPI backend. The backend owns RSS collection, LLM scoring, content fetching, LLM translation, scheduling, and SQLite persistence.

RSS sources provide the initial news entries. FastAPI reads RSS feeds, stores raw entries in SQLite, sends title and summary data to the LLM for scoring, keeps only high-value items for full-content fetching, sends ready content to the LLM for Chinese translation, and exposes display-ready records to the frontend.

Core data flow:

RSS → Crawl → Score → Filter → Fetch → Translate → UI

## 3. Core Modules（核心模块划分）

### 3.1 RSS Collector

### 3.2 News Scoring Service（LLM）

### 3.3 Content Fetcher

### 3.4 Translation Service（LLM）

### 3.5 Scheduler（定时任务）

### 3.6 API Service（FastAPI）

### 3.7 Frontend App

## 4. Module Interaction（模块交互）

1. RSS sources enter the system through the RSS Collector during scheduled crawling or manual refresh.
2. The RSS Collector parses enabled RSS feeds and writes new items as raw news records.
3. The News Scoring Service calls the LLM after a new raw item is available, using its title, summary, source, published time, and original link.
4. Items with score greater than or equal to `60` become selected for full-content fetching.
5. The Content Fetcher runs only for selected items and stores either extracted article content or RSS summary fallback content.
6. When usable content exists, the item becomes ready for display.
7. The Translation Service calls the LLM after the item is ready, using the original title, summary, content, source, and score.
8. The API Service reads displayable items from SQLite for the frontend.
9. The Frontend App renders the news list, 30-day high-score list, source configuration page, and news reading page from backend data.

## 5. Data Flow（数据流）

RSS → raw → scored → selected → fetched → ready → translated → UI

- RSS: Enabled RSS sources provide news entries.
- raw: New parsed entries are stored as unscored news.
- scored: The LLM returns a `0-100` value score for each raw item.
- selected: Items scoring `60` or higher are kept for full-content fetching.
- fetched: Selected items receive extracted article content or RSS summary fallback content.
- ready: High-value items with usable content become visible to the product surface.
- translated: Ready items are translated into Chinese by the LLM.
- UI: The frontend displays ready, translated, or translation-failed news according to lifecycle state.
