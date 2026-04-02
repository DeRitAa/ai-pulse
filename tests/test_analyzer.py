import json
from unittest.mock import patch, MagicMock
from src.analyzer import (
    analyze_articles,
    build_analysis_prompt,
    parse_analysis_response,
    merge_scores,
    AnalysisResult,
)


SAMPLE_ARTICLES = [
    {
        "title": "OpenAI releases GPT-5 with 60% reasoning improvement",
        "summary": "OpenAI announced GPT-5 today with major improvements in reasoning benchmarks.",
        "link": "https://openai.com/blog/gpt-5",
        "source_name": "OpenAI Blog",
    },
    {
        "title": "Kimi completes $300M Series B funding",
        "summary": "Moonshot AI's Kimi raised $300M led by Sequoia China.",
        "link": "https://36kr.com/p/123",
        "source_name": "量子位",
    },
]

SAMPLE_CLAUDE_RESPONSE = {
    "scores": {
        "OpenAI": {
            "model": "GPT-5",
            "reasoning": 91,
            "multimodal": 88,
            "code": 85,
            "long_context": 78,
            "speed_cost": 80,
        }
    },
    "openness": {
        "OpenAI": {
            "open_source": "closed",
            "api": "open",
            "pricing": "transparent",
        }
    },
    "special_news": [
        {
            "type": "major_release",
            "title": "OpenAI releases GPT-5 with 60% reasoning improvement",
            "summary": "GPT-5 surpasses GPT-4o across MMLU, MATH benchmarks. Reasoning +60%, API pricing reduced 40%.",
            "source": "OpenAI Blog",
            "url": "https://openai.com/blog/gpt-5",
        },
        {
            "type": "funding",
            "title": "Kimi completes $300M Series B funding",
            "summary": "Moonshot AI's Kimi raised $300M led by Sequoia China, valued at $5B.",
            "source": "量子位",
            "url": "https://36kr.com/p/123",
        },
    ],
}


class TestBuildAnalysisPrompt:
    def test_includes_all_articles(self):
        prompt = build_analysis_prompt(SAMPLE_ARTICLES)
        assert "OpenAI releases GPT-5" in prompt
        assert "Kimi completes" in prompt

    def test_requests_json_output(self):
        prompt = build_analysis_prompt(SAMPLE_ARTICLES)
        assert "JSON" in prompt


class TestParseAnalysisResponse:
    def test_parses_valid_json(self):
        raw = json.dumps(SAMPLE_CLAUDE_RESPONSE)
        result = parse_analysis_response(raw)
        assert isinstance(result, AnalysisResult)
        assert result.scores["OpenAI"]["reasoning"] == 91
        assert len(result.special_news) == 2

    def test_handles_json_in_markdown_block(self):
        raw = f"```json\n{json.dumps(SAMPLE_CLAUDE_RESPONSE)}\n```"
        result = parse_analysis_response(raw)
        assert result.scores["OpenAI"]["reasoning"] == 91


class TestMergeScores:
    def test_updates_existing_vendor(self):
        previous = {"OpenAI": {"model": "GPT-4o", "reasoning": 80, "multimodal": 85, "code": 80, "long_context": 70, "speed_cost": 75}}
        new = {"OpenAI": {"model": "GPT-5", "reasoning": 91, "multimodal": 88, "code": 85, "long_context": 78, "speed_cost": 80}}
        merged = merge_scores(previous, new)
        assert merged["OpenAI"]["reasoning"] == 91
        assert merged["OpenAI"]["model"] == "GPT-5"

    def test_keeps_vendor_not_in_new(self):
        previous = {"Anthropic": {"model": "Claude", "reasoning": 90, "multimodal": 70, "code": 88, "long_context": 85, "speed_cost": 65}}
        new = {}
        merged = merge_scores(previous, new)
        assert merged["Anthropic"]["reasoning"] == 90

    def test_adds_new_vendor(self):
        previous = {}
        new = {"xAI": {"model": "Grok-3", "reasoning": 82, "multimodal": 60, "code": 72, "long_context": 50, "speed_cost": 70}}
        merged = merge_scores(previous, new)
        assert merged["xAI"]["reasoning"] == 82
