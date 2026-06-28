from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html import unescape
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import sqlite3
import threading
import time
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - exercised when optional dependency is missing
    BeautifulSoup = None

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - exercised when optional dependency is missing
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parent
if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env")

DATABASE_PATH = Path(os.environ.get("RSS_DB_PATH", BASE_DIR / "rss.sqlite3"))
DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 20
SYNC_INTERVAL_SECONDS = int(os.environ.get("RSS_SYNC_INTERVAL_SECONDS", str(6 * 60 * 60)))
BACKFILL_BATCH_SIZE = int(os.environ.get("RSS_BACKFILL_BATCH_SIZE", "20"))
DEFAULT_LLM_MODEL = os.environ.get("LLM_MODEL", "glm-4")
LLM_TIMEOUT_SECONDS = float(os.environ.get("LLM_TIMEOUT_SECONDS", "20"))
LLM_MAX_RETRIES = int(os.environ.get("LLM_MAX_RETRIES", "0"))
SYNC_LOCK = threading.Lock()


DEFAULT_FEEDS = [
    {
        "id": "developers",
        "label": "OpenAI Developers",
        "url": "https://developers.openai.com/rss.xml",
    },
    {
        "id": "news",
        "label": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
    },
    {
        "id": "dreyx",
        "label": "DreyX Digest",
        "url": "https://dreyx.com/digest/rss",
    },
    {
        "id": "hackernews",
        "label": "Hacker News",
        "url": "https://news.ycombinator.com/rss",
    },
    {
        "id": "hn-frontpage",
        "label": "HN Frontpage",
        "url": "https://hnrss.org/frontpage",
    },
    {
        "id": "hn-newest",
        "label": "HN Newest",
        "url": "https://hnrss.org/newest",
    },
    {
        "id": "hn-bestcomments",
        "label": "HN Best Comments",
        "url": "https://hnrss.org/bestcomments",
    },
]

FEEDS = DEFAULT_FEEDS


def utc_now():
    return datetime.now(timezone.utc)


def local_name(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def text_of(element, tag_name):
    for child in element:
        if local_name(child.tag) == tag_name:
            if child.text is None:
                return None
            value = child.text.strip()
            return value or None
    return None


def plain_text_from_markup(value):
    if not value:
        return ""
    looks_like_markup = bool(re.search(r"<[A-Za-z!/][^>]*>", value))
    if BeautifulSoup is not None and looks_like_markup:
        text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    elif looks_like_markup:
        text = re.sub(r"<[^>]+>", " ", value)
    else:
        text = value
    return " ".join(unescape(text).split())


def localize_common_rss_metadata(value):
    text = plain_text_from_markup(value)
    text = re.sub(r"\bComments URL:\s*", "评论链接：", text)
    text = re.sub(r"\bArticle URL:\s*", "文章链接：", text)
    text = re.sub(r"\bPoints:\s*([0-9,]+)", r"积分：\1", text)
    text = re.sub(r"#\s*Comments:\s*([0-9,]+)", r"评论数：\1", text)
    return text


def is_common_rss_metadata(value):
    text = plain_text_from_markup(value)
    has_link = text.startswith("Comments URL:") or text.startswith("Article URL:")
    return has_link and "Points:" in text and "# Comments:" in text


def is_hacker_news_page_chrome(content, link):
    host = urlparse(link or "").hostname or ""
    return host == "news.ycombinator.com" and content.startswith("Hacker News new | past | comments")


def parse_pub_date(value):
    if not value:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)

    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_display_date(value):
    return value.strftime("%Y-%m-%d %H:%M UTC")


def clamp_limit(value):
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return DEFAULT_PAGE_LIMIT
    return min(max(limit, 1), MAX_PAGE_LIMIT)


def normalize_offset(value):
    try:
        offset = int(value)
    except (TypeError, ValueError):
        return 0
    return max(offset, 0)


def canonical_url(value):
    if not value:
        return ""
    parsed = urlparse(value.strip())
    if not parsed.scheme or not parsed.netloc:
        return value.strip()

    query = [
        (key, val)
        for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path or "/",
            "",
            urlencode(query, doseq=True),
            "",
        )
    )


def stable_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


def dedupe_key_for_item(item):
    if item.get("link"):
        return canonical_url(item["link"])
    return f"{item['source']}:{item.get('guid') or item['title']}:{item['publishedAt']}"


def stable_item_id(item):
    return stable_hash(dedupe_key_for_item(item))


def normalize_feed_url(url, resolve=False):
    if not isinstance(url, str):
        raise ValueError("Feed URL must be a string")
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        raise ValueError("Feed URL must be an absolute http(s) URL")

    try:
        literal_ip = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        literal_ip = None
    if literal_ip is not None and not literal_ip.is_global:
        raise ValueError("Feed URL host must be public")

    if resolve:
        addresses = socket.getaddrinfo(parsed.hostname, None)
        for address in {entry[4][0] for entry in addresses}:
            try:
                resolved_ip = ipaddress.ip_address(address)
            except ValueError:
                continue
            if not resolved_ip.is_global:
                raise ValueError("Feed URL host must resolve to public addresses")

    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path or "/",
            "",
            parsed.query,
            "",
        )
    )


def parse_feed_xml(xml_text, feed):
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("RSS channel not found")

    items = []
    for entry in channel.findall("item"):
        title = text_of(entry, "title") or "Untitled"
        link = text_of(entry, "link") or ""
        guid = text_of(entry, "guid")
        description = plain_text_from_markup(text_of(entry, "description") or "")
        encoded_content = text_of(entry, "encoded")
        content = plain_text_from_markup(encoded_content) if encoded_content else description
        pub_date = parse_pub_date(text_of(entry, "pubDate"))

        items.append(
            {
                "id": guid or link or f"{feed['id']}:{title}:{pub_date.isoformat()}",
                "guid": guid,
                "source": feed["id"],
                "sourceLabel": feed["label"],
                "title": title,
                "link": link,
                "description": description,
                "content": content,
                "publishedAt": pub_date.isoformat(),
                "publishedDisplay": format_display_date(pub_date),
                "category": text_of(entry, "category"),
            }
        )

    return items


def fetch_text(url):
    safe_url = normalize_feed_url(url, resolve=True)
    request = Request(
        safe_url,
        headers={
            "User-Agent": "OpenAI RSS Reader/1.0",
            "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        },
    )
    with urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_article_text(html_text):
    if not html_text:
        return ""
    if BeautifulSoup is None:
        return ""

    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside"]):
        tag.decompose()

    container = soup.find("article") or soup.find("main") or soup.body or soup
    parts = []
    for element in container.find_all(["h1", "h2", "h3", "p", "li"], recursive=True):
        text = " ".join(element.get_text(" ", strip=True).split())
        if text and text not in parts:
            parts.append(text)

    if not parts:
        text = " ".join(container.get_text(" ", strip=True).split())
        return text[:20000]
    return "\n\n".join(parts)[:20000]


def fetch_article_content(url, fetcher=fetch_text):
    if not url:
        return ""
    html_text = fetcher(url)
    return extract_article_text(html_text)


def get_database_connection(db_path=DATABASE_PATH):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def table_columns(connection, table_name):
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def add_column_if_missing(connection, table_name, column_name, column_sql):
    if column_name not in table_columns(connection, table_name):
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


def backfill_dedupe_keys(connection):
    rows = connection.execute(
        """
        SELECT id, source, title, link, published_at
        FROM rss_items
        WHERE dedupe_key IS NULL OR dedupe_key = ''
        """
    ).fetchall()
    for row in rows:
        key = canonical_url(row["link"]) if row["link"] else f"{row['source']}:{row['title']}:{row['published_at']}"
        connection.execute("UPDATE rss_items SET dedupe_key = ? WHERE id = ?", (key, row["id"]))


def collapse_duplicate_dedupe_keys(connection):
    connection.execute(
        """
        DELETE FROM rss_items
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM rss_items
            WHERE dedupe_key IS NOT NULL AND dedupe_key != ''
            GROUP BY dedupe_key
        )
        AND dedupe_key IS NOT NULL
        AND dedupe_key != ''
        """
    )


def init_database(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS rss_feeds (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS rss_items (
            id TEXT PRIMARY KEY,
            dedupe_key TEXT UNIQUE,
            source TEXT NOT NULL,
            source_label TEXT NOT NULL,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            description TEXT NOT NULL,
            original_description TEXT,
            original_content TEXT,
            summary_zh TEXT,
            content_zh TEXT,
            published_at TEXT NOT NULL,
            published_display TEXT NOT NULL,
            category TEXT,
            classification TEXT,
            translation_status TEXT,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            translated_at TEXT
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS rss_sync_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL,
            status TEXT NOT NULL,
            total_items INTEGER NOT NULL,
            errors_json TEXT NOT NULL
        )
        """
    )
    for column_name, column_sql in [
        ("dedupe_key", "dedupe_key TEXT"),
        ("original_description", "original_description TEXT"),
        ("original_content", "original_content TEXT"),
        ("summary_zh", "summary_zh TEXT"),
        ("content_zh", "content_zh TEXT"),
        ("classification", "classification TEXT"),
        ("translation_status", "translation_status TEXT"),
        ("translated_at", "translated_at TEXT"),
    ]:
        add_column_if_missing(connection, "rss_items", column_name, column_sql)
    backfill_dedupe_keys(connection)
    collapse_duplicate_dedupe_keys(connection)

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_rss_items_published
        ON rss_items (published_at DESC, id ASC)
        """
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_rss_items_dedupe
        ON rss_items (dedupe_key)
        """
    )
    created_at = utc_now().isoformat()
    connection.executemany(
        """
        INSERT OR IGNORE INTO rss_feeds (id, label, url, created_at)
        VALUES (?, ?, ?, ?)
        """,
        [(feed["id"], feed["label"], feed["url"], created_at) for feed in DEFAULT_FEEDS],
    )
    connection.commit()


def list_feeds(connection):
    rows = connection.execute(
        """
        SELECT id, label, url, created_at
        FROM rss_feeds
        ORDER BY created_at ASC, id ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def add_feed(connection, url, label=None):
    safe_url = normalize_feed_url(url)
    feed_id = stable_hash(safe_url)
    feed_label = (label or urlparse(safe_url).hostname or safe_url).strip() or safe_url
    created_at = utc_now().isoformat()
    connection.execute(
        """
        INSERT INTO rss_feeds (id, label, url, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET label = excluded.label
        """,
        (feed_id, feed_label, safe_url, created_at),
    )
    connection.commit()
    row = connection.execute(
        "SELECT id, label, url, created_at FROM rss_feeds WHERE url = ?",
        (safe_url,),
    ).fetchone()
    return dict(row)


def delete_feed(connection, feed_id):
    result = connection.execute("DELETE FROM rss_feeds WHERE id = ?", (feed_id,))
    connection.commit()
    return result.rowcount > 0


def classify_item(item):
    raw_category = (item.get("category") or "").strip()
    mapping = {
        "product": "产品",
        "company": "公司",
        "security": "安全",
        "global affairs": "全球事务",
        "applied ai": "应用 AI",
        "ai adoption": "AI 应用",
    }
    if raw_category:
        return mapping.get(raw_category.lower(), raw_category)

    text = f"{item.get('title', '')} {item.get('description', '')}".lower()
    checks = [
        (("security", "cyber", "vulnerability"), "安全"),
        (("agent", "agents", "agentic"), "智能体"),
        (("audio", "voice", "speech", "realtime"), "音频"),
        (("image", "video", "sora"), "多模态"),
        (("api", "sdk", "developer", "docs", "cookbook"), "开发者"),
        (("model", "gpt", "o3", "o4"), "模型"),
    ]
    for keywords, label in checks:
        if any(keyword in text for keyword in keywords):
            return label
    return "综合"


def fallback_translation(item, status):
    source_text = item.get("description") or item.get("content") or ""
    summary = localize_common_rss_metadata(source_text)
    content = localize_common_rss_metadata(item.get("content") or source_text)
    return {
        "summaryZh": summary,
        "contentZh": content,
        "classification": classify_item(item),
        "translationStatus": status,
    }


def llm_config_from_env():
    return {
        "api_key": os.environ.get("LLM_API_KEY") or os.environ.get("ZHIPU_API_KEY"),
        "base_url": os.environ.get("LLM_BASE_URL"),
        "model": os.environ.get("LLM_MODEL", DEFAULT_LLM_MODEL),
    }


def llm_proxy_url_from_env():
    for name in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        value = os.environ.get(name)
        if value:
            return value

    for name in ("ALL_PROXY", "all_proxy"):
        value = os.environ.get(name)
        if value and value.lower().startswith("socks://"):
            return "socks5://" + value[len("socks://") :]
        if value:
            return value
    return None


def create_llm_http_client():
    proxy_url = llm_proxy_url_from_env()
    if not proxy_url:
        return None

    import httpx

    return httpx.Client(proxy=proxy_url, timeout=LLM_TIMEOUT_SECONDS)


def parse_translation_json(text):
    if not text:
        raise ValueError("Empty LLM response")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def extract_response_text(payload):
    if payload.get("output_text"):
        return payload["output_text"]

    parts = []
    for output in payload.get("output", []):
        for content in output.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                parts.append(content["text"])
    return "\n".join(parts).strip()


def translate_item_with_llm(item, client_factory=None):
    if is_common_rss_metadata(item.get("description") or ""):
        translated = fallback_translation(item, "translated")
        translated["classification"] = classify_item(item)
        return translated

    config = llm_config_from_env()
    if not config["api_key"]:
        return fallback_translation(item, "missing_api_key")

    prompt_payload = {
        "title": item.get("title", ""),
        "summary": item.get("description", ""),
        "content": item.get("content", ""),
        "category": item.get("category"),
    }
    http_client = None
    try:
        if client_factory is None:
            from zai import ZaiClient

            client_factory = ZaiClient
            http_client = create_llm_http_client()

        client_kwargs = {"api_key": config["api_key"], "max_retries": LLM_MAX_RETRIES}
        if config["base_url"]:
            client_kwargs["base_url"] = config["base_url"]
        if http_client is not None:
            client_kwargs["http_client"] = http_client
        else:
            client_kwargs["timeout"] = LLM_TIMEOUT_SECONDS
        client = client_factory(**client_kwargs)
        response = client.chat.completions.create(
            model=config["model"],
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是 RSS 阅读器的数据处理器。请把 summary 和 content 翻译为简体中文，"
                        "并给出一个简短中文分类。标题保持原文，不要翻译标题。"
                        "只输出 JSON，字段为 summaryZh、contentZh、classification。"
                    ),
                },
                {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=False)},
            ],
        )
        text = response.choices[0].message.content
        translated = parse_translation_json(text)
        return {
            "summaryZh": str(translated.get("summaryZh") or item.get("description") or ""),
            "contentZh": str(translated.get("contentZh") or item.get("content") or item.get("description") or ""),
            "classification": str(translated.get("classification") or classify_item(item)),
            "translationStatus": "translated",
        }
    except Exception:
        return fallback_translation(item, "translation_failed")
    finally:
        if http_client is not None:
            http_client.close()


def existing_row_for_item(connection, item_id, dedupe_key):
    return connection.execute(
        """
        SELECT
            id,
            description,
            original_description,
            original_content,
            summary_zh,
            content_zh,
            classification,
            translation_status
        FROM rss_items
        WHERE id = ? OR dedupe_key = ?
        ORDER BY CASE WHEN id = ? THEN 0 ELSE 1 END
        LIMIT 1
        """,
        (item_id, dedupe_key, item_id),
    ).fetchone()


def existing_translation(connection, item_id, dedupe_key, item, row=None):
    row = row or existing_row_for_item(connection, item_id, dedupe_key)
    if row is None:
        return None

    original_description = item.get("description") or ""
    original_content = item.get("content") or original_description
    stored_description = row["original_description"] if row["original_description"] is not None else row["description"]
    stored_content = row["original_content"] or stored_description or ""
    if (
        stored_description == original_description
        and stored_content == original_content
    ):
        if row["translation_status"] == "translated" and row["summary_zh"] and row["content_zh"]:
            return {
                "summaryZh": row["summary_zh"],
                "contentZh": row["content_zh"],
                "classification": row["classification"] or classify_item(item),
                "translationStatus": row["translation_status"] or "cached",
            }
    return None


def enrich_items_with_article_content(items, article_fetcher=None, connection=None):
    if article_fetcher is None:
        article_fetcher = fetch_article_content

    enriched = []
    for item in items:
        next_item = dict(item)
        if connection is not None:
            item_id = stable_item_id(next_item)
            row = existing_row_for_item(connection, item_id, dedupe_key_for_item(next_item))
            stored_description = None
            if row is not None:
                stored_description = row["original_description"] if row["original_description"] is not None else row["description"]
            if row is not None and stored_description == (next_item.get("description") or ""):
                next_item["content"] = row["original_content"] or stored_description or next_item.get("content") or ""
                enriched.append(next_item)
                continue

        try:
            article_content = article_fetcher(item.get("link"))
        except Exception:
            article_content = ""
        if article_content:
            next_item["content"] = article_content
        enriched.append(next_item)
    return enriched


def save_items(connection, items, synced_at, translator=None):
    synced_at_iso = synced_at.astimezone(timezone.utc).isoformat()
    translate = translator or translate_item_with_llm
    rows = []

    for item in items:
        item_id = stable_item_id(item)
        dedupe_key = dedupe_key_for_item(item)
        existing_row = existing_row_for_item(connection, item_id, dedupe_key)
        original_description = item.get("description") or ""
        original_content = item.get("content") or original_description
        translated = existing_translation(connection, item_id, dedupe_key, item, existing_row) or translate(item)
        summary_zh = translated.get("summaryZh") or original_description
        content_zh = translated.get("contentZh") or original_content
        classification = translated.get("classification") or classify_item(item)
        translation_status = translated.get("translationStatus") or "translated"

        rows.append(
            (
                item_id,
                dedupe_key,
                item["source"],
                item["sourceLabel"],
                item["title"],
                item["link"],
                summary_zh,
                original_description,
                original_content,
                summary_zh,
                content_zh,
                item["publishedAt"],
                item["publishedDisplay"],
                item["category"],
                classification,
                translation_status,
                synced_at_iso,
                synced_at_iso,
                synced_at_iso,
            )
        )

    connection.executemany(
        """
        INSERT INTO rss_items (
            id,
            dedupe_key,
            source,
            source_label,
            title,
            link,
            description,
            original_description,
            original_content,
            summary_zh,
            content_zh,
            published_at,
            published_display,
            category,
            classification,
            translation_status,
            first_seen_at,
            last_seen_at,
            translated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(dedupe_key) DO UPDATE SET
            source = excluded.source,
            source_label = excluded.source_label,
            title = excluded.title,
            link = excluded.link,
            description = excluded.description,
            original_description = excluded.original_description,
            original_content = excluded.original_content,
            summary_zh = excluded.summary_zh,
            content_zh = excluded.content_zh,
            published_at = excluded.published_at,
            published_display = excluded.published_display,
            category = excluded.category,
            classification = excluded.classification,
            translation_status = excluded.translation_status,
            last_seen_at = excluded.last_seen_at,
            translated_at = excluded.translated_at
        """,
        rows,
    )
    connection.commit()


def row_to_item(row, include_content=False):
    item = {
        "id": row["id"],
        "source": row["source"],
        "sourceLabel": row["source_label"],
        "title": row["title"],
        "link": row["link"],
        "originalLink": row["link"],
        "description": row["summary_zh"] or row["description"],
        "summaryZh": row["summary_zh"] or row["description"],
        "originalDescription": row["original_description"] or "",
        "publishedAt": row["published_at"],
        "publishedDisplay": row["published_display"],
        "category": row["category"],
        "classification": row["classification"],
        "translationStatus": row["translation_status"],
    }
    if include_content:
        item["contentZh"] = row["content_zh"] or row["summary_zh"] or row["description"]
        item["originalContent"] = row["original_content"] or row["original_description"] or ""
    return item


TRANSLATION_ROW_COLUMNS = """
    id,
    source,
    source_label,
    title,
    link,
    description,
    original_description,
    original_content,
    published_at,
    published_display,
    category,
    summary_zh,
    content_zh,
    translation_status
"""


def row_needs_translation(row):
    return row["translation_status"] != "translated" or not row["summary_zh"] or not row["content_zh"]


def translation_item_from_row(row, content=None):
    description = plain_text_from_markup(row["original_description"] or row["description"] or "")
    source_content = content if content is not None else row["original_content"] or description
    cleaned_content = plain_text_from_markup(source_content)
    if description and is_hacker_news_page_chrome(cleaned_content, row["link"]):
        cleaned_content = description
    return {
        "id": row["id"],
        "source": row["source"],
        "sourceLabel": row["source_label"],
        "title": row["title"],
        "link": row["link"],
        "description": description,
        "content": cleaned_content,
        "publishedAt": row["published_at"],
        "publishedDisplay": row["published_display"],
        "category": row["category"],
    }


def update_item_translation(connection, row, translator=None, now=utc_now, article_fetcher=None):
    if not row_needs_translation(row):
        return False

    content = row["original_content"] or row["original_description"] or row["description"] or ""
    if article_fetcher is not None:
        try:
            article_content = article_fetcher(row["link"])
        except Exception:
            article_content = ""
        if article_content:
            content = article_content

    item = translation_item_from_row(row, content)
    translate = translator or translate_item_with_llm
    translated = translate(item)
    translated_at = now().astimezone(timezone.utc).isoformat()
    connection.execute(
        """
        UPDATE rss_items
        SET
            original_content = ?,
            description = ?,
            summary_zh = ?,
            content_zh = ?,
            classification = ?,
            translation_status = ?,
            translated_at = ?
        WHERE id = ?
        """,
        (
            item["content"],
            translated.get("summaryZh") or item["description"],
            translated.get("summaryZh") or item["description"],
            translated.get("contentZh") or item["content"],
            translated.get("classification") or classify_item(item),
            translated.get("translationStatus") or "translated",
            translated_at,
            row["id"],
        ),
    )
    return True


def ensure_items_translated(connection, item_ids, translator=None, now=utc_now, article_fetcher=None):
    if not item_ids:
        return 0

    placeholders = ",".join("?" for _ in item_ids)
    rows = connection.execute(
        f"""
        SELECT {TRANSLATION_ROW_COLUMNS}
        FROM rss_items
        WHERE id IN ({placeholders})
        """,
        item_ids,
    ).fetchall()
    processed = 0
    for row in rows:
        if update_item_translation(connection, row, translator, now, article_fetcher):
            processed += 1
    if processed:
        connection.commit()
    return processed


def page_item_ids(connection, limit=DEFAULT_PAGE_LIMIT, offset=0):
    rows = connection.execute(
        """
        SELECT id
        FROM rss_items
        ORDER BY published_at DESC, id ASC
        LIMIT ? OFFSET ?
        """,
        (clamp_limit(limit), normalize_offset(offset)),
    ).fetchall()
    return [row["id"] for row in rows]


def list_items(connection, limit=DEFAULT_PAGE_LIMIT, offset=0):
    normalized_limit = clamp_limit(limit)
    normalized_offset = normalize_offset(offset)
    total = connection.execute("SELECT COUNT(*) FROM rss_items").fetchone()[0]
    rows = connection.execute(
        """
        SELECT
            id,
            source,
            source_label,
            title,
            link,
            description,
            original_description,
            original_content,
            summary_zh,
            content_zh,
            published_at,
            published_display,
            category,
            classification,
            translation_status
        FROM rss_items
        ORDER BY published_at DESC, id ASC
        LIMIT ? OFFSET ?
        """,
        (normalized_limit, normalized_offset),
    ).fetchall()
    return [row_to_item(row) for row in rows], total


def get_item(connection, item_id):
    row = connection.execute(
        """
        SELECT
            id,
            source,
            source_label,
            title,
            link,
            description,
            original_description,
            original_content,
            summary_zh,
            content_zh,
            published_at,
            published_display,
            category,
            classification,
            translation_status
        FROM rss_items
        WHERE id = ?
        """,
        (item_id,),
    ).fetchone()
    return row_to_item(row, include_content=True) if row else None


def backfill_untranslated_items(
    connection,
    translator=None,
    batch_size=BACKFILL_BATCH_SIZE,
    now=utc_now,
    article_fetcher=None,
):
    translate = translator or translate_item_with_llm
    rows = connection.execute(
        """
        SELECT
            id,
            source,
            source_label,
            title,
            link,
            description,
            original_description,
            original_content,
            published_at,
            published_display,
            category
        FROM rss_items
        WHERE translation_status IS NULL OR translation_status != 'translated'
        ORDER BY published_at DESC, id ASC
        LIMIT ?
        """,
        (max(int(batch_size), 0),),
    ).fetchall()
    processed = 0
    translated_at = now().astimezone(timezone.utc).isoformat()

    for row in rows:
        content = row["original_content"] or row["original_description"] or row["description"] or ""
        if article_fetcher is not None:
            try:
                article_content = article_fetcher(row["link"])
            except Exception:
                article_content = ""
            if article_content:
                content = article_content

        item = {
            "id": row["id"],
            "source": row["source"],
            "sourceLabel": row["source_label"],
            "title": row["title"],
            "link": row["link"],
            "description": row["original_description"] or row["description"] or "",
            "content": content,
            "publishedAt": row["published_at"],
            "publishedDisplay": row["published_display"],
            "category": row["category"],
        }
        translated = translate(item)
        connection.execute(
            """
            UPDATE rss_items
            SET
                original_content = ?,
                description = ?,
                summary_zh = ?,
                content_zh = ?,
                classification = ?,
                translation_status = ?,
                translated_at = ?
            WHERE id = ?
            """,
            (
                content,
                translated.get("summaryZh") or item["description"],
                translated.get("summaryZh") or item["description"],
                translated.get("contentZh") or item["content"],
                translated.get("classification") or classify_item(item),
                translated.get("translationStatus") or "translated",
                translated_at,
                row["id"],
            ),
        )
        processed += 1

    connection.commit()
    return processed


def record_sync_run(connection, started_at, finished_at, status, total_items, errors):
    connection.execute(
        """
        INSERT INTO rss_sync_runs (started_at, finished_at, status, total_items, errors_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            started_at.isoformat(),
            finished_at.isoformat(),
            status,
            total_items,
            json.dumps(errors, ensure_ascii=False),
        ),
    )
    connection.commit()


def sync_feeds_to_database(
    connection,
    feeds=None,
    fetcher=fetch_text,
    translator=None,
    now=utc_now,
    article_fetcher=None,
):
    errors = []
    synced_at = now().astimezone(timezone.utc)
    feed_list = feeds if feeds is not None else list_feeds(connection)

    for feed in feed_list:
        try:
            xml_text = fetcher(feed["url"])
            items = enrich_items_with_article_content(parse_feed_xml(xml_text, feed), article_fetcher, connection)
            save_items(connection, items, synced_at, translator)
        except Exception as exc:
            errors.append({"source": feed["id"], "message": str(exc)})

    return errors, synced_at


def build_rss_payload(
    feeds=None,
    fetcher=fetch_text,
    now=utc_now,
    db_path=DATABASE_PATH,
    limit=DEFAULT_PAGE_LIMIT,
    offset=0,
    refresh=True,
    translator=None,
    article_fetcher=None,
):
    normalized_limit = clamp_limit(limit)
    normalized_offset = normalize_offset(offset)
    errors = []
    updated_at = now().astimezone(timezone.utc)

    with get_database_connection(db_path) as connection:
        init_database(connection)
        if refresh:
            errors, updated_at = sync_feeds_to_database(connection, feeds, fetcher, translator, now, article_fetcher)
        ensure_items_translated(
            connection,
            page_item_ids(connection, normalized_limit, normalized_offset),
            translator=translator,
            now=now,
        )
        items, total = list_items(connection, normalized_limit, normalized_offset)
        feed_list = feeds if feeds is not None else list_feeds(connection)

    next_offset = normalized_offset + len(items)
    has_more = next_offset < total

    return {
        "updatedAt": updated_at.isoformat(),
        "feeds": [{"id": feed["id"], "label": feed["label"], "url": feed["url"]} for feed in feed_list],
        "items": items,
        "errors": errors,
        "pagination": {
            "limit": normalized_limit,
            "offset": normalized_offset,
            "returned": len(items),
            "total": total,
            "hasMore": has_more,
            "nextOffset": next_offset if has_more else None,
        },
    }


def run_sync_once(
    db_path=DATABASE_PATH,
    fetcher=fetch_text,
    translator=None,
    now=utc_now,
    article_fetcher=None,
    lock=SYNC_LOCK,
    backfill_batch_size=BACKFILL_BATCH_SIZE,
):
    if lock is not None and not lock.acquire(blocking=False):
        return {"skipped": True, "reason": "sync_in_progress"}

    started_at = now().astimezone(timezone.utc)
    errors = []
    total = 0
    backfilled = 0
    status = "ok"
    try:
        with get_database_connection(db_path) as connection:
            init_database(connection)
            errors, synced_at = sync_feeds_to_database(
                connection,
                fetcher=fetcher,
                translator=translator,
                now=now,
                article_fetcher=article_fetcher,
            )
            backfilled = backfill_untranslated_items(
                connection,
                translator=translator,
                batch_size=backfill_batch_size,
                now=now,
                article_fetcher=article_fetcher,
            )
            total = connection.execute("SELECT COUNT(*) FROM rss_items").fetchone()[0]
            status = "partial_error" if errors else "ok"
            finished_at = now().astimezone(timezone.utc)
            record_sync_run(connection, started_at, finished_at, status, total, errors)
        return {
            "updatedAt": synced_at.isoformat(),
            "errors": errors,
            "total": total,
            "backfilled": backfilled,
            "skipped": False,
            "status": status,
        }
    finally:
        if lock is not None:
            lock.release()


def start_background_sync(
    db_path=DATABASE_PATH,
    fetcher=fetch_text,
    translator=None,
    article_fetcher=None,
    interval=SYNC_INTERVAL_SECONDS,
):
    def loop():
        while True:
            try:
                run_sync_once(db_path=db_path, fetcher=fetcher, translator=translator, article_fetcher=article_fetcher)
            except Exception as exc:
                print(f"RSS background sync failed: {exc}", flush=True)
            time.sleep(interval)

    thread = threading.Thread(target=loop, name="rss-background-sync", daemon=True)
    thread.start()
    return thread


def legacy_run_sync_once(db_path=DATABASE_PATH, fetcher=fetch_text, translator=None, now=utc_now):
    with get_database_connection(db_path) as connection:
        init_database(connection)
        errors, synced_at = sync_feeds_to_database(connection, fetcher=fetcher, translator=translator, now=now)
        total = connection.execute("SELECT COUNT(*) FROM rss_items").fetchone()[0]
    return {"updatedAt": synced_at.isoformat(), "errors": errors, "total": total}


def create_app(
    db_path=DATABASE_PATH,
    fetcher=fetch_text,
    translator=None,
    article_fetcher=None,
    start_scheduler=False,
):
    from flask import Flask, jsonify, request, send_file

    flask_app = Flask(__name__)
    translate = translator or translate_item_with_llm

    with get_database_connection(db_path) as connection:
        init_database(connection)

    if start_scheduler:
        start_background_sync(db_path=db_path, fetcher=fetcher, translator=translate, article_fetcher=article_fetcher)

    @flask_app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @flask_app.get("/")
    def index():
        return send_file(BASE_DIR / "index.html")

    @flask_app.get("/rss")
    def rss():
        refresh = request.args.get("refresh", "0") == "1"
        return jsonify(
            build_rss_payload(
                limit=request.args.get("limit", DEFAULT_PAGE_LIMIT),
                offset=request.args.get("offset", 0),
                refresh=refresh,
                db_path=db_path,
                fetcher=fetcher,
                translator=translate,
                article_fetcher=article_fetcher,
            )
        )

    @flask_app.get("/api/feeds")
    def api_feeds():
        with get_database_connection(db_path) as connection:
            init_database(connection)
            return jsonify({"feeds": list_feeds(connection)})

    @flask_app.post("/api/feeds")
    def api_add_feed():
        payload = request.get_json(silent=True) or {}
        try:
            with get_database_connection(db_path) as connection:
                init_database(connection)
                feed = add_feed(connection, payload.get("url"), payload.get("label"))
        except ValueError as exc:
            return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(exc)}}), 422
        return jsonify({"feed": feed}), 201

    @flask_app.delete("/api/feeds/<feed_id>")
    def api_delete_feed(feed_id):
        with get_database_connection(db_path) as connection:
            init_database(connection)
            deleted = delete_feed(connection, feed_id)
        if not deleted:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Feed not found"}}), 404
        return jsonify({"deleted": True})

    @flask_app.get("/api/items/<path:item_id>")
    def api_get_item(item_id):
        with get_database_connection(db_path) as connection:
            init_database(connection)
            ensure_items_translated(
                connection,
                [item_id],
                translator=translate,
                article_fetcher=article_fetcher,
            )
            item = get_item(connection, item_id)
        if item is None:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Item not found"}}), 404
        return jsonify({"item": item})

    @flask_app.post("/api/sync")
    def api_sync():
        result = run_sync_once(db_path=db_path, fetcher=fetcher, translator=translate, article_fetcher=article_fetcher)
        return jsonify(result)

    return flask_app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app = create_app(start_scheduler=True)
    app.run(host="127.0.0.1", port=port)
