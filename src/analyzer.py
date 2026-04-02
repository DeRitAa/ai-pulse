"""Claude API analyzer for scoring AI vendors and identifying special news."""

import json
import os
import re
from dataclasses import dataclass, field

import anthropic


@dataclass
class AnalysisResult:
    scores: dict = field(default_factory=dict)
    openness: dict = field(default_factory=dict)
    special_news: list = field(default_factory=list)


DIMENSIONS = ["reasoning", "multimodal", "code", "long_context", "speed_cost"]

OPENNESS_VALUES = {
    "open_source": {"open": "🟢 完全开源", "partial": "🟡 部分开源", "closed": "🔴 不开源"},
    "api": {"open": "🟢 全量开放", "limited": "🟡 限速/邀请制", "closed": "🔴 未开放"},
    "pricing": {"transparent": "🟢 透明公开", "contact": "🟡 需联系销售", "unknown": "🔴 未知"},
}

NEWS_TYPES = {
    "major_release": {"emoji": "⚠️", "label": "重大发布", "color": "#f85149"},
    "funding": {"emoji": "💰", "label": "融资", "color": "#3fb950"},
    "report": {"emoji": "📋", "label": "年报/财报", "color": "#d29922"},
    "security": {"emoji": "🔒", "label": "安全/漏洞", "color": "#a371f7"},
    "regulation": {"emoji": "📜", "label": "监管/政策", "color": "#79c0ff"},
    "benchmark": {"emoji": "🏆", "label": "Benchmark", "color": "#ffa657"},
}


def build_analysis_prompt(articles: list[dict]) -> str:
    """Build the prompt for Claude analysis."""
    articles_text = ""
    for i, a in enumerate(articles, 1):
        articles_text += f"\n[{i}] {a['title']}\n来源: {a['source_name']}\n链接: {a['link']}\n摘要: {a.get('summary', 'N/A')}\n"

    return f"""你是一个 AI 行业分析助手。请分析以下 {len(articles)} 条新闻，输出严格 JSON（不要额外文字）。

## 输出格式

{{
  "scores": {{
    "厂商名": {{
      "model": "最新旗舰模型名称",
      "reasoning": 0-100,
      "multimodal": 0-100,
      "code": 0-100,
      "long_context": 0-100,
      "speed_cost": 0-100
    }}
  }},
  "openness": {{
    "厂商名": {{
      "open_source": "open|partial|closed",
      "api": "open|limited|closed",
      "pricing": "transparent|contact|unknown"
    }}
  }},
  "special_news": [
    {{
      "type": "major_release|funding|report|security|regulation|benchmark",
      "title": "新闻标题",
      "summary": "1-2句中文摘要",
      "source": "来源名称",
      "url": "原文链接"
    }}
  ]
}}

## 评分规则

- 仅对本期新闻涉及的厂商打分，不涉及的厂商不输出
- 厂商名统一为: OpenAI, Anthropic, Google, Meta, xAI, 阿里, 字节, MiniMax, Kimi, 百度
- 如果出现其他厂商/初创公司，也一并输出
- 评分基于公开信息和行业共识
- special_news 仅包含重大事件

## 本期新闻

{articles_text}
"""


def parse_analysis_response(raw_text: str) -> AnalysisResult:
    """Parse Claude's response text into an AnalysisResult."""
    cleaned = raw_text.strip()
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()

    data = json.loads(cleaned)

    return AnalysisResult(
        scores=data.get("scores", {}),
        openness=data.get("openness", {}),
        special_news=data.get("special_news", []),
    )


def merge_scores(previous: dict, new: dict) -> dict:
    """Merge new scores into previous. New scores overwrite, missing vendors are kept."""
    merged = dict(previous)
    for vendor, scores in new.items():
        merged[vendor] = scores
    return merged


def analyze_articles(articles: list[dict]) -> AnalysisResult:
    """Call Claude API to analyze articles. Requires ANTHROPIC_API_KEY env var."""
    if not articles:
        return AnalysisResult()

    client = anthropic.Anthropic()
    prompt = build_analysis_prompt(articles)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = message.content[0].text
    return parse_analysis_response(raw_text)
