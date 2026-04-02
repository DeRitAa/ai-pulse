"""Fetch model data from OpenRouter API for capability dashboard."""

import requests
from dataclasses import dataclass

# Map vendor names to OpenRouter model ID prefixes
VENDOR_PREFIXES = {
    "OpenAI": "openai/",
    "Anthropic": "anthropic/",
    "Google": "google/",
    "Meta": "meta-llama/",
    "xAI": "x-ai/",
    "阿里": "qwen/",
    "字节": "bytedance/",  # not on openrouter yet, but ready
    "MiniMax": "minimax/",
    "Kimi": "moonshotai/",
    "DeepSeek": "deepseek/",
    "Mistral": "mistralai/",
}

# Models we want to track (flagship per vendor)
FLAGSHIP_MODELS = {
    "OpenAI": ["openai/gpt-4.1", "openai/o4-mini", "openai/gpt-5.4"],
    "Anthropic": ["anthropic/claude-sonnet-4", "anthropic/claude-opus-4"],
    "Google": ["google/gemini-2.5-pro-preview", "google/gemini-2.5-flash-preview"],
    "Meta": ["meta-llama/llama-4-maverick", "meta-llama/llama-4-scout"],
    "xAI": ["x-ai/grok-3-mini-beta", "x-ai/grok-3-beta"],
    "DeepSeek": ["deepseek/deepseek-r1", "deepseek/deepseek-chat"],
    "阿里": ["qwen/qwen-2.5-72b-instruct"],
    "Mistral": ["mistralai/mistral-large"],
}


@dataclass
class ModelInfo:
    vendor: str
    model_id: str
    name: str
    context_length: int
    input_price: float  # per million tokens
    output_price: float  # per million tokens
    modalities: list[str]
    is_free: bool


def fetch_openrouter_models() -> list[ModelInfo]:
    """Fetch all models from OpenRouter API and filter to tracked vendors."""
    try:
        resp = requests.get("https://openrouter.ai/api/v1/models", timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"⚠️  Failed to fetch OpenRouter models: {e}")
        return []

    models_data = data.get("data", [])
    results = []

    for vendor, prefixes_or_ids in FLAGSHIP_MODELS.items():
        for target_id in prefixes_or_ids:
            for m in models_data:
                if m["id"] == target_id:
                    pricing = m.get("pricing", {})
                    input_price = float(pricing.get("prompt", "0")) * 1_000_000
                    output_price = float(pricing.get("completion", "0")) * 1_000_000

                    arch = m.get("architecture", {})
                    modalities = arch.get("input_modalities", ["text"])

                    results.append(ModelInfo(
                        vendor=vendor,
                        model_id=m["id"],
                        name=m.get("name", m["id"]),
                        context_length=m.get("context_length", 0),
                        input_price=round(input_price, 2),
                        output_price=round(output_price, 2),
                        modalities=modalities,
                        is_free=(input_price == 0 and output_price == 0),
                    ))
                    break

    return results


def build_vendor_dashboard(models: list[ModelInfo]) -> dict:
    """Group models by vendor for dashboard display."""
    dashboard = {}
    for m in models:
        if m.vendor not in dashboard:
            dashboard[m.vendor] = []
        dashboard[m.vendor].append({
            "name": m.name,
            "model_id": m.model_id,
            "context_length": m.context_length,
            "context_display": f"{m.context_length // 1000}K" if m.context_length < 1_000_000 else f"{m.context_length // 1_000_000}M",
            "input_price": m.input_price,
            "output_price": m.output_price,
            "price_display": f"${m.input_price:.1f} / ${m.output_price:.1f}" if not m.is_free else "Free",
            "modalities": m.modalities,
            "has_vision": "image" in m.modalities,
            "has_audio": "audio" in m.modalities,
        })
    return dashboard
