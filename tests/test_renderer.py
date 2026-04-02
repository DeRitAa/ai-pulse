from src.renderer import render_email


SAMPLE_SCORES = {
    "OpenAI": {"model": "GPT-5", "reasoning": 91, "multimodal": 88, "code": 85, "long_context": 78, "speed_cost": 80},
    "Anthropic": {"model": "Opus 4.5", "reasoning": 95, "multimodal": 72, "code": 92, "long_context": 85, "speed_cost": 65},
}

SAMPLE_OPENNESS = {
    "OpenAI": {"open_source": "closed", "api": "open", "pricing": "transparent"},
    "Anthropic": {"open_source": "closed", "api": "limited", "pricing": "transparent"},
}

SAMPLE_SPECIAL_NEWS = [
    {
        "type": "major_release",
        "title": "OpenAI GPT-5 发布",
        "summary": "GPT-5 推理能力提升60%，定价下调40%。",
        "source": "OpenAI Blog",
        "url": "https://openai.com/blog/gpt-5",
    },
]

SAMPLE_DIMENSIONS = [
    {"key": "reasoning", "label": "🧠 推理", "color": "#7ee787", "border": "#7ee787"},
    {"key": "multimodal", "label": "👁️ 多模态", "color": "#79c0ff", "border": "#79c0ff"},
    {"key": "code", "label": "💻 代码", "color": "#f78166", "border": "#f78166"},
    {"key": "long_context", "label": "📄 长上下文", "color": "#d2a8ff", "border": "#d2a8ff"},
    {"key": "speed_cost", "label": "⚡ 速度/成本", "color": "#ffa657", "border": "#ffa657"},
]


class TestRenderEmail:
    def test_returns_html_string(self):
        html = render_email(
            scores=SAMPLE_SCORES,
            openness=SAMPLE_OPENNESS,
            special_news=SAMPLE_SPECIAL_NEWS,
            dimensions=SAMPLE_DIMENSIONS,
            total_articles=47,
            report_time="2026-04-01 22:00",
        )
        assert isinstance(html, str)
        assert "<html" in html.lower()

    def test_contains_vendor_names(self):
        html = render_email(
            scores=SAMPLE_SCORES,
            openness=SAMPLE_OPENNESS,
            special_news=SAMPLE_SPECIAL_NEWS,
            dimensions=SAMPLE_DIMENSIONS,
            total_articles=47,
            report_time="2026-04-01 22:00",
        )
        assert "OpenAI" in html
        assert "Anthropic" in html

    def test_contains_special_news(self):
        html = render_email(
            scores=SAMPLE_SCORES,
            openness=SAMPLE_OPENNESS,
            special_news=SAMPLE_SPECIAL_NEWS,
            dimensions=SAMPLE_DIMENSIONS,
            total_articles=47,
            report_time="2026-04-01 22:00",
        )
        assert "GPT-5 发布" in html
        assert "openai.com/blog/gpt-5" in html

    def test_contains_dimension_modules(self):
        html = render_email(
            scores=SAMPLE_SCORES,
            openness=SAMPLE_OPENNESS,
            special_news=SAMPLE_SPECIAL_NEWS,
            dimensions=SAMPLE_DIMENSIONS,
            total_articles=47,
            report_time="2026-04-01 22:00",
        )
        assert "推理" in html
        assert "多模态" in html
        assert "代码" in html

    def test_handles_empty_scores(self):
        html = render_email(
            scores={},
            openness={},
            special_news=[],
            dimensions=SAMPLE_DIMENSIONS,
            total_articles=0,
            report_time="2026-04-01 10:00",
        )
        assert "0 条动态" in html
