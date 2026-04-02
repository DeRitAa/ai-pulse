# main.py
"""Main entry point: fetch → analyze → render → send → archive."""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

import yaml

from src.fetcher import fetch_all_feeds
from src.analyzer import analyze_articles, merge_scores
from src.renderer import render_email
from src.emailer import send_email, build_subject


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LATEST_SCORES_PATH = os.path.join(DATA_DIR, "latest_scores.json")


def load_config(path: str = "config.yaml") -> dict:
    """Load config.yaml from project root."""
    config_path = os.path.join(os.path.dirname(__file__), path)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_latest_scores() -> dict:
    """Load cumulative scores from previous runs."""
    if os.path.exists(LATEST_SCORES_PATH):
        with open(LATEST_SCORES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_run_data(run_dir: str, raw_articles: list, analysis_result, html: str) -> None:
    """Save raw data, scores, and HTML for this run."""
    os.makedirs(run_dir, exist_ok=True)

    with open(os.path.join(run_dir, "raw.json"), "w", encoding="utf-8") as f:
        serializable = []
        for a in raw_articles:
            entry = dict(a)
            entry.pop("published_parsed", None)
            serializable.append(entry)
        json.dump(serializable, f, ensure_ascii=False, indent=2)

    with open(os.path.join(run_dir, "scores.json"), "w", encoding="utf-8") as f:
        json.dump({"scores": analysis_result.scores, "openness": analysis_result.openness, "special_news": analysis_result.special_news}, f, ensure_ascii=False, indent=2)

    with open(os.path.join(run_dir, "email.html"), "w", encoding="utf-8") as f:
        f.write(html)


def run(dry_run: bool = False) -> None:
    """Execute one full digest cycle."""
    config = load_config()
    window_hours = config["schedule"]["window_hours"]

    # 1. Collect all RSS sources into a flat list
    all_sources = []
    for source_group in ["wechat_rss", "x_rss", "official_blogs"]:
        sources = config["sources"].get(source_group, [])
        all_sources.extend(sources)

    print(f"📡 Fetching from {len(all_sources)} RSS sources...")
    articles = fetch_all_feeds(all_sources, window_hours=window_hours)
    print(f"📰 Found {len(articles)} articles in the last {window_hours}h")

    if not articles:
        print("⚠️  No articles found. Skipping this run.")
        return

    # 2. Analyze with Claude
    print("🤖 Analyzing with Claude API...")
    result = analyze_articles(articles)
    print(f"   → {len(result.scores)} vendors scored, {len(result.special_news)} special news")

    # 3. Merge with previous scores
    previous_scores = load_latest_scores()
    merged_scores = merge_scores(previous_scores, result.scores)

    # 4. Render email
    now = datetime.now(timezone(timedelta(hours=8)))
    report_time = now.strftime("%Y-%m-%d %H:%M")
    dimensions = config["dimensions"]

    html = render_email(
        scores=merged_scores,
        openness=result.openness,
        special_news=result.special_news,
        dimensions=dimensions,
        total_articles=len(articles),
        report_time=report_time,
    )

    # 5. Archive
    run_dir = os.path.join(DATA_DIR, now.strftime("%Y-%m-%d-%H"))
    save_run_data(run_dir, articles, result, html)

    # Save cumulative scores
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LATEST_SCORES_PATH, "w", encoding="utf-8") as f:
        json.dump(merged_scores, f, ensure_ascii=False, indent=2)

    print(f"💾 Data archived to {run_dir}/")

    # 6. Send email
    if dry_run:
        print("🏃 Dry run — skipping email send. Email saved to archive.")
        return

    email_cfg = config["email"]
    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not password:
        print("❌ GMAIL_APP_PASSWORD environment variable not set. Skipping email.")
        return

    subject = build_subject(report_time, len(articles))
    send_email(
        html_body=html,
        subject=subject,
        from_addr=email_cfg["from_addr"],
        to_addrs=email_cfg["to_addrs"],
        smtp_host=email_cfg["smtp_host"],
        smtp_port=email_cfg["smtp_port"],
        password=password,
    )
    print(f"✅ Email sent to {', '.join(email_cfg['to_addrs'])}")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    run(dry_run=dry)
