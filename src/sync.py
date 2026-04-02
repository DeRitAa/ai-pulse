"""Sync RSS sources from WeWeRSS to config.yaml."""

import requests


def fetch_wewerss_feeds(base_url: str) -> list[dict]:
    """Fetch all subscribed feeds from WeWeRSS instance.

    Returns list of {"id": "MP_WXS_xxx", "name": "公众号名"}.
    """
    url = base_url.rstrip("/") + "/feeds"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"⚠️  Failed to fetch WeWeRSS feeds: {e}")
        return []


def sync_wechat_sources(config: dict, wewerss_base_url: str) -> tuple[dict, dict]:
    """Sync WeWeRSS feeds → config.yaml wechat_rss section.

    Returns (updated_config, changes_summary).
    """
    remote_feeds = fetch_wewerss_feeds(wewerss_base_url)
    if not remote_feeds:
        return config, {"added": [], "removed": [], "unchanged": 0}

    # Build lookup of existing sources by feed ID
    existing = config.get("sources", {}).get("wechat_rss", [])
    existing_ids = {}
    for s in existing:
        # Extract feed ID from URL like .../feeds/MP_WXS_xxx.atom
        feed_id = s["url"].split("/feeds/")[-1].replace(".atom", "").replace(".rss", "").replace(".json", "")
        existing_ids[feed_id] = s

    # Build new list from remote
    remote_ids = {f["id"] for f in remote_feeds}
    new_sources = []
    added = []
    removed = []

    for feed in remote_feeds:
        feed_id = feed["id"]
        if feed_id in existing_ids:
            # Keep existing entry (preserve any custom fields)
            new_sources.append(existing_ids[feed_id])
        else:
            # New feed — generate URL
            entry = {
                "url": f"{wewerss_base_url.rstrip('/')}/feeds/{feed_id}.atom",
                "name": feed["name"],
            }
            new_sources.append(entry)
            added.append(feed["name"])

    # Check what was removed
    for feed_id, source in existing_ids.items():
        if feed_id not in remote_ids:
            removed.append(source["name"])

    config["sources"]["wechat_rss"] = new_sources

    summary = {
        "added": added,
        "removed": removed,
        "unchanged": len(new_sources) - len(added),
    }
    return config, summary
