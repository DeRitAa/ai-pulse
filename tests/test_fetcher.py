import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from src.fetcher import fetch_all_feeds, filter_by_time, deduplicate


def _make_entry(title, published_ts, link="https://example.com/article"):
    """Helper to create a mock RSS entry dict."""
    return {
        "title": title,
        "link": link,
        "published_parsed": time.gmtime(published_ts),
        "summary": f"Summary of {title}",
        "source_name": "Test Source",
    }


class TestFilterByTime:
    def test_keeps_recent_articles(self):
        now = datetime.now(timezone.utc)
        recent_ts = (now - timedelta(hours=2)).timestamp()
        entries = [_make_entry("Recent Article", recent_ts)]
        result = filter_by_time(entries, window_hours=12)
        assert len(result) == 1
        assert result[0]["title"] == "Recent Article"

    def test_drops_old_articles(self):
        now = datetime.now(timezone.utc)
        old_ts = (now - timedelta(hours=24)).timestamp()
        entries = [_make_entry("Old Article", old_ts)]
        result = filter_by_time(entries, window_hours=12)
        assert len(result) == 0

    def test_handles_empty_list(self):
        result = filter_by_time([], window_hours=12)
        assert result == []


class TestDeduplicate:
    def test_removes_exact_duplicate_titles(self):
        entries = [
            _make_entry("OpenAI launches GPT-5", 1000, "https://a.com"),
            _make_entry("OpenAI launches GPT-5", 1001, "https://b.com"),
        ]
        result = deduplicate(entries)
        assert len(result) == 1

    def test_removes_similar_titles(self):
        entries = [
            _make_entry("OpenAI launches GPT-5 model", 1000, "https://a.com"),
            _make_entry("OpenAI launches its GPT-5 model today", 1001, "https://b.com"),
        ]
        result = deduplicate(entries)
        assert len(result) == 1

    def test_keeps_different_titles(self):
        entries = [
            _make_entry("OpenAI launches GPT-5", 1000),
            _make_entry("Anthropic releases Claude 4", 1001),
        ]
        result = deduplicate(entries)
        assert len(result) == 2


class TestFetchAllFeeds:
    @patch("src.fetcher.feedparser.parse")
    def test_fetches_and_normalizes_entries(self, mock_parse):
        now = datetime.now(timezone.utc)
        recent_ts = (now - timedelta(hours=1)).timestamp()

        mock_parse.return_value = MagicMock(
            entries=[
                MagicMock(
                    title="Test Article",
                    link="https://example.com/1",
                    published_parsed=time.gmtime(recent_ts),
                    get=lambda k, d=None: f"Summary text" if k == "summary" else d,
                )
            ],
            bozo=False,
        )

        sources = [{"url": "https://example.com/rss", "name": "Test"}]
        result = fetch_all_feeds(sources, window_hours=12)
        assert len(result) == 1
        assert result[0]["title"] == "Test Article"
        assert result[0]["source_name"] == "Test"
