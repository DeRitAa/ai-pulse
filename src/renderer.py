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
) -> str:
    """Render the HTML email string."""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("email.html")

    # Pre-sort vendors by score for each dimension (descending)
    scores_by_dim = {}
    for dim in dimensions:
        key = dim["key"]
        vendor_scores = []
        for vendor_name, data in scores.items():
            score = data.get(key)
            if score is not None and score > 0:
                vendor_scores.append((vendor_name, data.get("model", ""), score))
        vendor_scores.sort(key=lambda x: x[2], reverse=True)
        scores_by_dim[key] = vendor_scores

    dim_article_counts = {dim["key"]: len(scores_by_dim[dim["key"]]) for dim in dimensions}

    return template.render(
        report_time=report_time,
        total_articles=total_articles,
        dimensions=dimensions,
        scores_by_dim=scores_by_dim,
        dim_article_counts=dim_article_counts,
        openness=openness,
        special_news=special_news,
        news_types=NEWS_TYPES,
    )
