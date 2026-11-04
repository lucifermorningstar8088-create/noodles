"""Ranked search presets for the manual GGUF model picker.

The presets only search Hugging Face metadata. They never download or load files.
Every returned repository must be inspected for its exact revision, GGUF files,
artifact size, and license before the user can explicitly request a download.
"""

from __future__ import annotations

from typing import Final, TypedDict


class ModelSearchPreset(TypedDict):
    rank: int
    query: str
    label: str
    parameters: str
    reason: str
    suggested_quantization: str


MODEL_SEARCH_PRESETS: Final[tuple[ModelSearchPreset, ...]] = (
    {
        "rank": 1,
        "query": "Qwen3 1.7B",
        "label": "Qwen3 1.7B",
        "parameters": "1.7B",
        "reason": "Small first model for a low-resource local smoke test.",
        "suggested_quantization": "Q4_K_M",
    },
    {
        "rank": 2,
        "query": "Qwen2.5 1.5B Instruct",
        "label": "Qwen2.5 1.5B Instruct",
        "parameters": "1.5B",
        "reason": "Very small instruction-following alternative.",
        "suggested_quantization": "Q4_K_M",
    },
    {
        "rank": 3,
        "query": "SmolLM2 1.7B Instruct",
        "label": "SmolLM2 1.7B Instruct",
        "parameters": "1.7B",
        "reason": "Compact instruction model for lightweight tasks.",
        "suggested_quantization": "Q4_K_M",
    },
    {
        "rank": 4,
        "query": "Qwen2.5 3B Instruct",
        "label": "Qwen2.5 3B Instruct",
        "parameters": "3B",
        "reason": "More capable general assistant when memory permits.",
        "suggested_quantization": "Q4_K_M",
    },
    {
        "rank": 5,
        "query": "Llama 3.2 3B Instruct",
        "label": "Llama 3.2 3B Instruct",
        "parameters": "3B",
        "reason": "Alternative compact instruction-following model.",
        "suggested_quantization": "Q4_K_M",
    },
    {
        "rank": 6,
        "query": "Qwen3 4B",
        "label": "Qwen3 4B",
        "parameters": "4B",
        "reason": "Higher-capability option with greater RAM requirements.",
        "suggested_quantization": "Q4_K_M",
    },
)


def recommendation_payload() -> list[ModelSearchPreset]:
    """Return independent dictionaries in stable, smallest-first order."""
    return [dict(item) for item in MODEL_SEARCH_PRESETS]
