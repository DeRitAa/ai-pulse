"""RSS feed fetcher with time filtering and deduplication."""

import re
import time
from datetime import datetime, timezone, timedelta
from calendar import timegm
from difflib import SequenceMatcher
from html.parser import HTMLParser

import feedparser


class _WeChatContentExtractor(HTMLParser):
    """Extract plain text from WeChat's js_content / rich_media_content div."""

    def __init__(self):
        super().__init__()
        self._in_content = False
        self._depth = 0
        self.texts: list[str] = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if attr_dict.get("id") in ("js_content", "rich_media_content"):
            self._in_content = True
            self._depth = 0
        elif self._in_content:
            self._depth += 1

    def handle_endtag(self, tag):
        if self._in_content:
            if self._depth == 0:
                self._in_content = False
            else:
                self._depth -= 1

    def handle_data(self, data):
        if self._in_content and data.strip():
            self.texts.append(data.strip())


def _extract_summary(entry) -> str:
    """Return the best available plain-text summary for an entry.

    WeWeRSS stores full 3MB WeChat page HTML in <content>. feedparser's
    default sanitizer reduces it to garbage like '&&&&&&&&&&'.
    We parse the raw HTML to extract real article text.
    """
    # 1. Try unsanitized content (WeWeRSS WeChat feeds)
    if hasattr(entry, "content") and entry.content:
        raw_html = entry.content[0].get("value", "")
        if raw_html and len(raw_html) > 200:
            extractor = _WeChatContentExtractor()
            try:
                extractor.feed(raw_html)
            except Exception:
                pass
            text = " ".join(extractor.texts)
            if len(text) > 50:
                return text[:2000]  # cap for LLM context

    # 2. Fall back to entry.summary if it looks non-garbage
    summary = entry.get("summary", "")
    if summary and not all(c in "&; \n\t" for c in summary):
        return summary[:2000]

    # 3. Fall back to title
    return ""


def fetch_all_feeds(sources: list[dict], window_hours: int = 12) -> list[dict]:
    """Fetch all RSS sources, filter by time, deduplicate, return normalized entries."""
    all_entries = []
    for source in sources:
        entries = _fetch_single_feed(source["url"], source["name"])
        all_entries.extend(entries)

    recent = filter_by_time(all_entries, window_hours)
    unique = deduplicate(recent)
    return unique


def _fetch_single_feed(url: str, source_name: str) -> list[dict]:
    """Parse one RSS feed and normalize entries to a common dict format."""
    try:
        feed = feedparser.parse(url, sanitize_html=False)
    except Exception:
        return []

    entries = []
    for entry in feed.entries:
        # WeWeRSS Atom feeds use updated_parsed; standard RSS uses published_parsed
        parsed_time = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if parsed_time is None:
            continue
        entries.append({
            "title": entry.title,
            "link": entry.link,
            "published_parsed": parsed_time,
            "published_ts": timegm(parsed_time),
            "summary": _extract_summary(entry),
            "source_name": source_name,
        })
    return entries


def filter_by_time(entries: list[dict], window_hours: int = 12) -> list[dict]:
    """Keep only entries published within the last `window_hours` hours.
    Adds a 30-minute grace buffer to avoid losing articles on the boundary."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours, minutes=30)
    cutoff_ts = cutoff.timestamp()

    result = []
    for entry in entries:
        entry_ts = timegm(entry["published_parsed"])
        if entry_ts >= cutoff_ts:
            result.append(entry)
    return result


def deduplicate(entries: list[dict], threshold: float = 0.75) -> list[dict]:
    """Remove entries with similar titles. Keeps the first occurrence."""
    unique = []
    seen_titles: list[str] = []

    for entry in entries:
        title = entry["title"].strip().lower()
        is_dup = False
        for seen in seen_titles:
            ratio = SequenceMatcher(None, title, seen).ratio()
            if ratio >= threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(entry)
            seen_titles.append(title)
    return unique
