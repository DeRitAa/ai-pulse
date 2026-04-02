"""Render HTML email from analysis results using Jinja2."""

import os
from jinja2 import Environment, FileSystemLoader

from src.analyzer import NEWS_TYPES

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")


def render_email(
    scores: dict,
    openness: dict,
    special_news: list,
    dimensions: list[dict],
    total_articles: int,
    report_time: str,
    recommended_reads: list | None = None,
    vendor_dashboard: dict | None = None,
) -> str:
    """Render the HTML email string."""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("email.html")

    return template.render(
        report_time=report_time,
        total_articles=total_articles,
        openness=openness,
        special_news=special_news,
        news_types=NEWS_TYPES,
        recommended_reads=recommended_reads or [],
        vendor_dashboard=vendor_dashboard or {},
    )
