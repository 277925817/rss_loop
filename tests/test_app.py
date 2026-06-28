import unittest
from unittest import mock
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from pathlib import Path
from urllib.parse import quote

from app import (
    add_feed,
    backfill_untranslated_items,
    build_rss_payload,
    create_app,
    delete_feed,
    extract_article_text,
    fallback_translation,
    fetch_article_content,
    get_database_connection,
    get_item,
    init_database,
    list_feeds,
    list_items,
    llm_config_from_env,
    llm_proxy_url_from_env,
    parse_feed_xml,
    run_sync_once,
    save_items,
    sync_feeds_to_database,
    translate_item_with_llm,
)


DEVELOPERS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Docs MCP</title>
      <link>https://developers.openai.com/learn/docs-mcp/</link>
      <guid isPermaLink="true">https://developers.openai.com/learn/docs-mcp/</guid>
      <description>Connect coding agents to OpenAI docs.</description>
      <pubDate>Tue, 06 Jan 2026 00:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Realtime and audio guide</title>
      <link>https://platform.openai.com/docs/guides/realtime</link>
      <guid isPermaLink="true">https://platform.openai.com/docs/guides/realtime</guid>
      <description>Build realtime voice agents.</description>
      <pubDate>Mon, 21 Jul 2025 00:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


NEWS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title><![CDATA[Previewing GPT-5.6 Sol]]></title>
      <description><![CDATA[A next-generation model preview.]]></description>
      <link>https://openai.com/index/previewing-gpt-5-6-sol</link>
      <guid isPermaLink="true">https://openai.com/index/previewing-gpt-5-6-sol</guid>
      <category><![CDATA[Product]]></category>
      <pubDate>Fri, 26 Jun 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

HTML_DESCRIPTION_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Ask HN: Why did you learn Chinese?</title>
      <link>https://news.ycombinator.com/item?id=48701100</link>
      <guid isPermaLink="false">48701100</guid>
      <description><![CDATA[<p>Comments URL: <a href="https://news.ycombinator.com/item?id=48701100">https://news.ycombinator.com/item?id=48701100</a></p>
<p>Points: 1</p>
<p># Comments: 0</p>]]></description>
      <pubDate>Sat, 27 Jun 2026 19:45:43 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


ARTICLE_HTML = """<!doctype html>
<html>
  <head><title>Ignored chrome</title></head>
  <body>
    <nav>Navigation should not be used.</nav>
    <article>
      <h1>Article headline</h1>
      <p>First paragraph from the original article.</p>
      <p>Second paragraph with useful details.</p>
    </article>
  </body>
</html>
"""


def translate_for_test(item):
    return {
        "summaryZh": f"中文摘要：{item['description']}",
        "contentZh": f"中文内容：{item.get('content') or item['description']}",
        "classification": "产品",
        "translationStatus": "translated",
    }


class RssParserTests(unittest.TestCase):
    def test_parse_feed_xml_normalizes_items(self):
        items = parse_feed_xml(
            DEVELOPERS_FEED,
            {"id": "developers", "label": "OpenAI Developers"},
        )

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], "https://developers.openai.com/learn/docs-mcp/")
        self.assertEqual(items[0]["source"], "developers")
        self.assertEqual(items[0]["sourceLabel"], "OpenAI Developers")
        self.assertEqual(items[0]["title"], "Docs MCP")
        self.assertEqual(items[0]["link"], "https://developers.openai.com/learn/docs-mcp/")
        self.assertEqual(items[0]["description"], "Connect coding agents to OpenAI docs.")
        self.assertEqual(items[0]["publishedAt"], "2026-01-06T00:00:00+00:00")
        self.assertEqual(items[0]["publishedDisplay"], "2026-01-06 00:00 UTC")
        self.assertIsNone(items[0]["category"])

    def test_parse_feed_xml_converts_html_descriptions_to_plain_text(self):
        items = parse_feed_xml(
            HTML_DESCRIPTION_FEED,
            {"id": "hn-newest", "label": "HN Newest"},
        )

        self.assertNotIn("<p>", items[0]["description"])
        self.assertIn("Comments URL: https://news.ycombinator.com/item?id=48701100", items[0]["description"])
        self.assertIn("Points: 1", items[0]["description"])
        self.assertEqual(items[0]["content"], items[0]["description"])

    def test_build_rss_payload_merges_items_newest_first(self):
        feeds = [
            {"id": "developers", "label": "OpenAI Developers", "url": "developers"},
            {"id": "news", "label": "OpenAI News", "url": "news"},
        ]

        with TemporaryDirectory() as directory:
            payload = build_rss_payload(
                feeds,
                fetcher=lambda url: DEVELOPERS_FEED if url == "developers" else NEWS_FEED,
                now=lambda: datetime(2026, 6, 27, 15, 0, tzinfo=timezone.utc),
                db_path=Path(directory) / "rss.sqlite3",
                article_fetcher=lambda url: "",
                translator=translate_for_test,
            )

        self.assertEqual(payload["updatedAt"], "2026-06-27T15:00:00+00:00")
        self.assertEqual(payload["errors"], [])
        self.assertEqual([feed["id"] for feed in payload["feeds"]], ["developers", "news"])
        self.assertEqual([item["source"] for item in payload["items"]], ["news", "developers", "developers"])
        self.assertEqual(payload["items"][0]["title"], "Previewing GPT-5.6 Sol")
        self.assertEqual(payload["items"][0]["category"], "Product")

    def test_build_rss_payload_keeps_successful_source_when_one_feed_fails(self):
        feeds = [
            {"id": "developers", "label": "OpenAI Developers", "url": "developers"},
            {"id": "news", "label": "OpenAI News", "url": "news"},
        ]

        def fetcher(url):
            if url == "news":
                raise RuntimeError("network timeout")
            return DEVELOPERS_FEED

        with TemporaryDirectory() as directory:
            payload = build_rss_payload(
                feeds,
                fetcher=fetcher,
                now=lambda: datetime(2026, 6, 27, 15, 0, tzinfo=timezone.utc),
                db_path=Path(directory) / "rss.sqlite3",
                article_fetcher=lambda url: "",
                translator=translate_for_test,
            )

        self.assertEqual(len(payload["items"]), 2)
        self.assertEqual(payload["errors"], [{"source": "news", "message": "network timeout"}])

    def test_build_rss_payload_persists_items_and_returns_first_page_only(self):
        feeds = [
            {"id": "developers", "label": "OpenAI Developers", "url": "developers"},
            {"id": "news", "label": "OpenAI News", "url": "news"},
        ]

        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            payload = build_rss_payload(
                feeds,
                fetcher=lambda url: DEVELOPERS_FEED if url == "developers" else NEWS_FEED,
                now=lambda: datetime(2026, 6, 27, 15, 0, tzinfo=timezone.utc),
                db_path=db_path,
                limit=2,
                offset=0,
                refresh=True,
                article_fetcher=lambda url: "",
                translator=translate_for_test,
            )

            self.assertEqual([item["title"] for item in payload["items"]], ["Previewing GPT-5.6 Sol", "Docs MCP"])
            self.assertEqual(
                payload["pagination"],
                {"limit": 2, "offset": 0, "returned": 2, "total": 3, "hasMore": True, "nextOffset": 2},
            )

            next_page = build_rss_payload(
                feeds,
                fetcher=lambda url: (_ for _ in ()).throw(AssertionError("should not fetch while paginating")),
                now=lambda: datetime(2026, 6, 27, 15, 5, tzinfo=timezone.utc),
                db_path=db_path,
                limit=2,
                offset=2,
                refresh=False,
                article_fetcher=lambda url: "",
                translator=translate_for_test,
            )

            self.assertEqual([item["title"] for item in next_page["items"]], ["Realtime and audio guide"])
            self.assertEqual(next_page["errors"], [])
            self.assertFalse(next_page["pagination"]["hasMore"])

    def test_save_items_upserts_without_duplicates(self):
        items = parse_feed_xml(DEVELOPERS_FEED, {"id": "developers", "label": "OpenAI Developers"})

        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            with get_database_connection(db_path) as connection:
                init_database(connection)
                save_items(
                    connection,
                    items,
                    datetime(2026, 6, 27, 15, 0, tzinfo=timezone.utc),
                    translator=translate_for_test,
                )
                save_items(
                    connection,
                    items,
                    datetime(2026, 6, 27, 15, 5, tzinfo=timezone.utc),
                    translator=translate_for_test,
                )
                page, total = list_items(connection, limit=20, offset=0)

            self.assertEqual(total, 2)
            self.assertEqual([item["title"] for item in page], ["Docs MCP", "Realtime and audio guide"])

    def test_build_rss_payload_caps_limit_at_twenty(self):
        feeds = [
            {"id": "developers", "label": "OpenAI Developers", "url": "developers"},
            {"id": "news", "label": "OpenAI News", "url": "news"},
        ]

        with TemporaryDirectory() as directory:
            payload = build_rss_payload(
                feeds,
                fetcher=lambda url: DEVELOPERS_FEED if url == "developers" else NEWS_FEED,
                now=lambda: datetime(2026, 6, 27, 15, 0, tzinfo=timezone.utc),
                db_path=Path(directory) / "rss.sqlite3",
                limit=50,
                offset=-10,
                refresh=True,
                article_fetcher=lambda url: "",
                translator=translate_for_test,
            )

        self.assertEqual(payload["pagination"]["limit"], 20)
        self.assertEqual(payload["pagination"]["offset"], 0)
        self.assertLessEqual(len(payload["items"]), 20)

    def test_build_rss_payload_translates_failed_page_summaries_before_returning(self):
        items = parse_feed_xml(NEWS_FEED, {"id": "news", "label": "OpenAI News"})
        items[0]["content"] = "Full English article body."
        translated_items = []

        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            with get_database_connection(db_path) as connection:
                init_database(connection)
                save_items(
                    connection,
                    items,
                    datetime(2026, 6, 27, 15, 0, tzinfo=timezone.utc),
                    translator=lambda item: {
                        "summaryZh": item["description"],
                        "contentZh": item["content"],
                        "classification": "旧",
                        "translationStatus": "translation_failed",
                    },
                )

            payload = build_rss_payload(
                db_path=db_path,
                limit=20,
                offset=0,
                refresh=False,
                translator=lambda item: translated_items.append(item) or translate_for_test(item),
            )

        self.assertEqual(len(translated_items), 1)
        self.assertEqual(payload["items"][0]["description"], "中文摘要：A next-generation model preview.")
        self.assertEqual(payload["items"][0]["translationStatus"], "translated")

    def test_feed_configuration_can_list_add_and_delete_sources(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            with get_database_connection(db_path) as connection:
                init_database(connection)
                default_feeds = list_feeds(connection)
                added = add_feed(connection, "https://example.com/rss.xml", "Example Feed")
                after_add = list_feeds(connection)
                deleted = delete_feed(connection, added["id"])
                after_delete = list_feeds(connection)

        self.assertEqual(
            [feed["id"] for feed in default_feeds],
            [
                "developers",
                "dreyx",
                "hackernews",
                "hn-bestcomments",
                "hn-frontpage",
                "hn-newest",
                "news",
            ],
        )
        self.assertEqual(added["label"], "Example Feed")
        self.assertIn("https://example.com/rss.xml", [feed["url"] for feed in after_add])
        self.assertTrue(deleted)
        self.assertNotIn("https://example.com/rss.xml", [feed["url"] for feed in after_delete])

    def test_sync_translates_classifies_and_deduplicates_before_saving(self):
        feeds = [
            {"id": "first", "label": "First", "url": "first"},
            {"id": "second", "label": "Second", "url": "second"},
        ]

        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            with get_database_connection(db_path) as connection:
                init_database(connection)
                errors, _ = sync_feeds_to_database(
                    connection,
                    feeds=feeds,
                    fetcher=lambda url: NEWS_FEED,
                    translator=translate_for_test,
                    now=lambda: datetime(2026, 6, 27, 15, 0, tzinfo=timezone.utc),
                )
                page, total = list_items(connection, limit=20, offset=0)
                detail = get_item(connection, page[0]["id"])

        self.assertEqual(errors, [])
        self.assertEqual(total, 1)
        self.assertEqual(page[0]["title"], "Previewing GPT-5.6 Sol")
        self.assertEqual(page[0]["description"], "中文摘要：A next-generation model preview.")
        self.assertEqual(page[0]["classification"], "产品")
        self.assertEqual(detail["contentZh"], "中文内容：A next-generation model preview.")
        self.assertEqual(detail["originalLink"], "https://openai.com/index/previewing-gpt-5-6-sol")

    def test_flask_feed_config_and_item_detail_endpoints(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            flask_app = create_app(
                db_path=db_path,
                fetcher=lambda url: DEVELOPERS_FEED if "developers" in url else NEWS_FEED,
                translator=translate_for_test,
                article_fetcher=lambda url: "",
                start_scheduler=False,
            )
            client = flask_app.test_client()

            feeds_response = client.get("/api/feeds")
            add_response = client.post(
                "/api/feeds",
                json={"url": "https://example.com/rss.xml", "label": "Example Feed"},
            )
            delete_response = client.delete(f"/api/feeds/{add_response.get_json()['feed']['id']}")
            rss_response = client.get("/rss?limit=50&offset=-5&refresh=1")
            first_item = rss_response.get_json()["items"][0]
            item_response = client.get(f"/api/items/{first_item['id']}")

        self.assertEqual(feeds_response.status_code, 200)
        self.assertEqual(add_response.status_code, 201)
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(rss_response.get_json()["pagination"]["limit"], 20)
        self.assertEqual(rss_response.get_json()["pagination"]["offset"], 0)
        self.assertEqual(item_response.status_code, 200)
        self.assertIn("contentZh", item_response.get_json()["item"])

    def test_item_detail_endpoint_translates_failed_items_before_returning(self):
        items = parse_feed_xml(NEWS_FEED, {"id": "news", "label": "OpenAI News"})
        items[0]["content"] = "Full English article body."
        translated_items = []

        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            with get_database_connection(db_path) as connection:
                init_database(connection)
                save_items(
                    connection,
                    items,
                    datetime(2026, 6, 27, 15, 0, tzinfo=timezone.utc),
                    translator=lambda item: {
                        "summaryZh": item["description"],
                        "contentZh": item["content"],
                        "classification": "旧",
                        "translationStatus": "translation_failed",
                    },
                )
                item_id = list_items(connection, limit=20, offset=0)[0][0]["id"]

            flask_app = create_app(
                db_path=db_path,
                translator=lambda item: translated_items.append(item) or translate_for_test(item),
                start_scheduler=False,
            )
            client = flask_app.test_client()
            response = client.get(f"/api/items/{quote(item_id, safe='')}")

        payload = response.get_json()["item"]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(translated_items), 1)
        self.assertEqual(payload["summaryZh"], "中文摘要：A next-generation model preview.")
        self.assertEqual(payload["contentZh"], "中文内容：Full English article body.")
        self.assertEqual(payload["translationStatus"], "translated")

    def test_item_detail_endpoint_accepts_legacy_url_ids(self):
        item_id = "https://openai.com/index/previewing-gpt-5-6-sol"

        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            with get_database_connection(db_path) as connection:
                init_database(connection)
                connection.execute(
                    """
                    INSERT INTO rss_items (
                        id, dedupe_key, source, source_label, title, link, description,
                        original_description, original_content, summary_zh, content_zh,
                        published_at, published_display, category, classification,
                        translation_status, first_seen_at, last_seen_at, translated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_id,
                        item_id,
                        "news",
                        "OpenAI News",
                        "Previewing GPT-5.6 Sol",
                        item_id,
                        "中文摘要",
                        "Original summary",
                        "Original content",
                        "中文摘要",
                        "中文正文",
                        "2026-06-26T10:00:00+00:00",
                        "2026-06-26 10:00 UTC",
                        "Product",
                        "产品",
                        "translated",
                        "2026-06-27T15:00:00+00:00",
                        "2026-06-27T15:00:00+00:00",
                        "2026-06-27T15:00:00+00:00",
                    ),
                )
                connection.commit()

            flask_app = create_app(db_path=db_path, start_scheduler=False)
            client = flask_app.test_client()
            response = client.get(f"/api/items/{quote(item_id, safe='')}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["item"]["id"], item_id)
        self.assertEqual(response.get_json()["item"]["contentZh"], "中文正文")

    def test_invalid_feed_url_is_rejected(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            flask_app = create_app(db_path=db_path, start_scheduler=False)
            client = flask_app.test_client()

            response = client.post("/api/feeds", json={"url": "http://127.0.0.1/rss.xml", "label": "Local"})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()["error"]["code"], "VALIDATION_ERROR")

    def test_article_content_fetcher_prefers_extracted_article_text(self):
        calls = []

        def html_fetcher(url):
            calls.append(url)
            return ARTICLE_HTML

        content = fetch_article_content("https://example.com/article", fetcher=html_fetcher)

        self.assertIn("Article headline", content)
        self.assertIn("Second paragraph with useful details.", content)
        self.assertEqual(calls, ["https://example.com/article"])

    def test_extract_article_text_ignores_page_chrome(self):
        extracted = extract_article_text(ARTICLE_HTML)

        self.assertIn("First paragraph from the original article.", extracted)
        self.assertNotIn("Navigation should not be used.", extracted)

    def test_sync_uses_article_content_before_translation(self):
        seen_contents = []

        def translator(item):
            seen_contents.append(item["content"])
            return translate_for_test(item)

        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            with get_database_connection(db_path) as connection:
                init_database(connection)
                sync_feeds_to_database(
                    connection,
                    feeds=[{"id": "news", "label": "OpenAI News", "url": "news"}],
                    fetcher=lambda url: NEWS_FEED,
                    translator=translator,
                    article_fetcher=lambda url: "Extracted full article body.",
                    now=lambda: datetime(2026, 6, 27, 15, 0, tzinfo=timezone.utc),
                )
                item = list_items(connection, limit=20, offset=0)[0][0]

        self.assertEqual(seen_contents, ["Extracted full article body."])
        self.assertEqual(item["description"], "中文摘要：A next-generation model preview.")

    def test_zai_translator_uses_llm_env_config(self):
        class FakeMessage:
            content = '{"summaryZh":"中文摘要","contentZh":"中文正文","classification":"测试"}'

        class FakeChoice:
            message = FakeMessage()

        class FakeResponse:
            choices = [FakeChoice()]

        class FakeCompletions:
            def __init__(self):
                self.calls = []

            def create(self, **kwargs):
                self.calls.append(kwargs)
                return FakeResponse()

        class FakeChat:
            def __init__(self):
                self.completions = FakeCompletions()

        class FakeClient:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                self.chat = FakeChat()

        captured = {}

        def factory(**kwargs):
            client = FakeClient(**kwargs)
            captured["client"] = client
            return client

        with mock.patch.dict(
            "os.environ",
            {"LLM_API_KEY": "test-key", "LLM_BASE_URL": "https://example.test/api", "LLM_MODEL": "glm-test"},
            clear=False,
        ):
            config = llm_config_from_env()
            translated = translate_item_with_llm(
                {"title": "Title", "description": "Summary", "content": "Body", "category": None},
                client_factory=factory,
            )

        self.assertEqual(config["api_key"], "test-key")
        self.assertEqual(config["base_url"], "https://example.test/api")
        self.assertEqual(captured["client"].kwargs["api_key"], "test-key")
        self.assertEqual(captured["client"].kwargs["base_url"], "https://example.test/api")
        self.assertEqual(captured["client"].kwargs["max_retries"], 0)
        self.assertEqual(captured["client"].chat.completions.calls[0]["model"], "glm-test")
        self.assertEqual(translated["summaryZh"], "中文摘要")
        self.assertEqual(translated["contentZh"], "中文正文")
        self.assertEqual(translated["classification"], "测试")

    def test_fallback_translation_localizes_common_hn_metadata(self):
        translated = fallback_translation(
            {
                "title": "Ask HN: Why did you learn Chinese?",
                "description": "Comments URL: https://news.ycombinator.com/item?id=48701100 Points: 1 # Comments: 0",
                "content": "Comments URL: https://news.ycombinator.com/item?id=48701100 Points: 1 # Comments: 0",
                "category": None,
            },
            "translation_failed",
        )

        self.assertIn("评论链接", translated["summaryZh"])
        self.assertIn("积分：1", translated["summaryZh"])
        self.assertIn("评论数：0", translated["summaryZh"])

    def test_hn_metadata_translation_does_not_call_llm(self):
        def fail_if_called(**kwargs):
            raise AssertionError("metadata-only summaries should use local translation")

        with mock.patch.dict("os.environ", {"LLM_API_KEY": "test-key"}, clear=True):
            translated = translate_item_with_llm(
                {
                    "title": "Ask HN: Why did you learn Chinese?",
                    "description": "Comments URL: https://news.ycombinator.com/item?id=48701100 Points: 1 # Comments: 0",
                    "content": "Comments URL: https://news.ycombinator.com/item?id=48701100 Points: 1 # Comments: 0",
                    "category": None,
                },
                client_factory=fail_if_called,
            )

        self.assertEqual(translated["translationStatus"], "translated")
        self.assertIn("评论链接", translated["summaryZh"])
        self.assertIn("评论数：0", translated["contentZh"])

    def test_llm_proxy_prefers_http_proxy_over_all_proxy(self):
        with mock.patch.dict(
            "os.environ",
            {
                "HTTPS_PROXY": "http://127.0.0.1:7897/",
                "ALL_PROXY": "socks://127.0.0.1:7897/",
            },
            clear=True,
        ):
            proxy_url = llm_proxy_url_from_env()

        self.assertEqual(proxy_url, "http://127.0.0.1:7897/")

    def test_run_sync_once_skips_when_lock_is_already_held(self):
        lock = __import__("threading").Lock()
        lock.acquire()
        try:
            result = run_sync_once(lock=lock)
        finally:
            lock.release()

        self.assertTrue(result["skipped"])
        self.assertEqual(result["reason"], "sync_in_progress")

    def test_backfill_untranslated_items_processes_a_small_batch(self):
        items = parse_feed_xml(DEVELOPERS_FEED, {"id": "developers", "label": "OpenAI Developers"})

        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            with get_database_connection(db_path) as connection:
                init_database(connection)
                save_items(
                    connection,
                    items,
                    datetime(2026, 6, 27, 15, 0, tzinfo=timezone.utc),
                    translator=lambda item: {
                        "summaryZh": item["description"],
                        "contentZh": item["content"],
                        "classification": "旧",
                        "translationStatus": "missing_api_key",
                    },
                )
                processed = backfill_untranslated_items(connection, translate_for_test, batch_size=1)
                page, total = list_items(connection, limit=20, offset=0)

        self.assertEqual(processed, 1)
        self.assertEqual(total, 2)
        self.assertEqual(
            sum(1 for item in page if item["translationStatus"] == "translated"),
            1,
        )

    def test_existing_untranslated_rss_summaries_are_translated_on_sync(self):
        items = parse_feed_xml(NEWS_FEED, {"id": "news", "label": "OpenAI News"})

        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            with get_database_connection(db_path) as connection:
                init_database(connection)
                save_items(
                    connection,
                    items,
                    datetime(2026, 6, 27, 15, 0, tzinfo=timezone.utc),
                    translator=lambda item: {
                        "summaryZh": "",
                        "contentZh": "",
                        "classification": "产品",
                        "translationStatus": "missing_api_key",
                    },
                )

                translated_items = []

                save_items(
                    connection,
                    items,
                    datetime(2026, 6, 27, 16, 0, tzinfo=timezone.utc),
                    translator=lambda item: translated_items.append(item) or translate_for_test(item),
                )
                page, total = list_items(connection, limit=20, offset=0)

        self.assertEqual(total, 1)
        self.assertEqual(len(translated_items), 1)
        self.assertEqual(translated_items[0]["content"], "A next-generation model preview.")
        self.assertEqual(page[0]["description"], "中文摘要：A next-generation model preview.")
        self.assertEqual(page[0]["translationStatus"], "translated")

    def test_hn_reader_uses_rss_summary_when_scraped_content_is_page_chrome(self):
        items = parse_feed_xml(HTML_DESCRIPTION_FEED, {"id": "hn-newest", "label": "HN Newest"})
        items[0]["content"] = (
            "Hacker News new | past | comments | ask | show | jobs | submit login "
            "Ask HN: Why did you learn Chinese? 2 points by alonsovm44"
        )
        translated_items = []

        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            with get_database_connection(db_path) as connection:
                init_database(connection)
                save_items(
                    connection,
                    items,
                    datetime(2026, 6, 27, 15, 0, tzinfo=timezone.utc),
                    translator=lambda item: {
                        "summaryZh": item["description"],
                        "contentZh": item["content"],
                        "classification": "旧",
                        "translationStatus": "translation_failed",
                    },
                )
                item_id = list_items(connection, limit=20, offset=0)[0][0]["id"]

            flask_app = create_app(
                db_path=db_path,
                translator=lambda item: translated_items.append(item) or translate_for_test(item),
                start_scheduler=False,
            )
            client = flask_app.test_client()
            response = client.get(f"/api/items/{quote(item_id, safe='')}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(translated_items), 1)
        self.assertEqual(translated_items[0]["content"], translated_items[0]["description"])
        self.assertNotIn("Hacker News new | past", translated_items[0]["content"])

    def test_migrated_legacy_rows_are_not_duplicated_by_new_stable_ids(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "rss.sqlite3"
            with get_database_connection(db_path) as connection:
                connection.execute(
                    """
                    CREATE TABLE rss_items (
                        id TEXT PRIMARY KEY,
                        source TEXT NOT NULL,
                        source_label TEXT NOT NULL,
                        title TEXT NOT NULL,
                        link TEXT NOT NULL,
                        description TEXT NOT NULL,
                        published_at TEXT NOT NULL,
                        published_display TEXT NOT NULL,
                        category TEXT,
                        first_seen_at TEXT NOT NULL,
                        last_seen_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    INSERT INTO rss_items (
                        id, source, source_label, title, link, description,
                        published_at, published_display, category, first_seen_at, last_seen_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "https://openai.com/index/previewing-gpt-5-6-sol",
                        "news",
                        "OpenAI News",
                        "Previewing GPT-5.6 Sol",
                        "https://openai.com/index/previewing-gpt-5-6-sol",
                        "Old summary",
                        "2026-06-26T10:00:00+00:00",
                        "2026-06-26 10:00 UTC",
                        "Product",
                        "2026-06-27T15:00:00+00:00",
                        "2026-06-27T15:00:00+00:00",
                    ),
                )
                connection.commit()
                init_database(connection)
                sync_feeds_to_database(
                    connection,
                    feeds=[{"id": "news", "label": "OpenAI News", "url": "news"}],
                    fetcher=lambda url: NEWS_FEED,
                    translator=translate_for_test,
                    article_fetcher=lambda url: "",
                    now=lambda: datetime(2026, 6, 27, 16, 0, tzinfo=timezone.utc),
                )
                _, total = list_items(connection, limit=20, offset=0)

        self.assertEqual(total, 1)


if __name__ == "__main__":
    unittest.main()
