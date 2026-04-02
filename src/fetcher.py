"""RSS feed fetcher with time filtering and deduplication."""

import time
from datetime import datetime, timezone, timedelta
from calendar import timegm
from difflib import SequenceMatcher

import feedparser


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
        feed = feedparser.parse(url)
    except Exception:
        return []

    entries = []
    for entry in feed.entries:
        published_parsed = getattr(entry, "published_parsed", None)
        if published_parsed is None:
            continue
        entries.append({
            "title": entry.title,
            "link": entry.link,
            "published_parsed": published_parsed,
            "published_ts": timegm(published_parsed),
            "summary": entry.get("summary", ""),
            "source_name": source_name,
        })
    return entries


def filter_by_time(entries: list[dict], window_hours: int = 12) -> list[dict]:
    """Keep only entries published within the last `window_hours` hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
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
