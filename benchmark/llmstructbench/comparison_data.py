"""Published LLM SOB / LLMStructBench scores for comparison.

Sources:
- SOB (Structured Output Benchmark) arXiv:2604.25359 — multimodal structured output
- LLMStructBench paper (arXiv 2602.14743) — text-only structured extraction
- OAEI-LLM-T (arXiv:2503.21813) — hallucination analysis

SOB extends LLMStructBench to multimodal (image + audio + text, 5,000+ records).
f1_values = SOB Overall (composite of Value Acc + JSON Pass + Perfect rate)
json_validity = SOB JSON Pass (schema compliance rate)
value_accuracy = SOB Value Acc (actual value correctness)
perfect_rate = SOB Perfect (fully correct response rate)
"""

from __future__ import annotations

# ════════════════════════════════════════════════════════════
# Latest LLM scores (SOB Benchmark — arXiv:2604.25359)
# 5,000+ multimodal records: text + image (PDF scans) + audio
# ════════════════════════════════════════════════════════════

LLM_STRUCT_BENCH = {
    "GPT-5.4": {
        "f1_values": 0.870,
        "json_validity": 0.993,
        "value_accuracy": 0.798,
        "perfect_rate": 0.469,
        "developer": "OpenAI",
        "comment": "Highest Overall; near-perfect JSON Pass but 19.5%p Value-Acc gap",
    },
    "Gemini-3.1-Pro": {
        "f1_values": 0.869,
        "json_validity": 0.966,
        "value_accuracy": 0.820,
        "perfect_rate": 0.542,
        "developer": "Google",
        "comment": "Highest Value Acc & Perfect rate; large-context nesting optimized",
    },
    "GLM-5.1": {
        "f1_values": 0.866,
        "json_validity": 0.975,
        "value_accuracy": 0.806,
        "perfect_rate": 0.498,
        "developer": "Zhipu AI",
        "comment": "Best cost-performance ratio at $1.05/$3.50 per 1M tokens",
    },
    "Claude-Opus-4.7": {
        "f1_values": 0.864,
        "json_validity": 0.993,
        "value_accuracy": 0.787,
        "perfect_rate": 0.424,
        "developer": "Anthropic",
        "comment": "Tied for highest JSON Pass; lower Value Acc and Perfect rate",
    },
    "GLM-4.7": {
        "f1_values": 0.861,
        "json_validity": 0.965,
        "value_accuracy": 0.804,
        "perfect_rate": 0.508,
        "developer": "Zhipu AI",
        "comment": "Lowest cost among top-5 ($0.60/$2.20); 50.8% Perfect rate",
    },
    "Qwen3.5-35B": {
        "f1_values": 0.861,
        "json_validity": 0.969,
        "value_accuracy": 0.801,
        "perfect_rate": 0.500,
        "developer": "Alibaba",
        "comment": "Open-source MoE; ultra-low cost ($0.163/$1.30); 50% Perfect rate",
    },
    "GPT-5.5": {
        "f1_values": 0.860,
        "json_validity": 0.978,
        "value_accuracy": 0.795,
        "perfect_rate": 0.464,
        "developer": "OpenAI",
        "comment": "Slightly below GPT-5.4 in Overall; higher JSON Pass",
    },
    "Gemini-2.5-Flash": {
        "f1_values": 0.860,
        "json_validity": 0.972,
        "value_accuracy": 0.796,
        "perfect_rate": 0.498,
        "developer": "Google",
        "comment": "Best latency/cost ratio at $0.30/$2.50; near-equal to Pro tier",
    },
    "Gemma-3-27B": {
        "f1_values": 0.847,
        "json_validity": 0.969,
        "value_accuracy": 0.777,
        "perfect_rate": 0.454,
        "developer": "Google",
        "comment": "Open-source; align-up hallucination tendency (OAEI-LLM-T)",
    },
    "DS-R1-Distill-32B": {
        "f1_values": 0.827,
        "json_validity": 0.960,
        "value_accuracy": 0.747,
        "perfect_rate": 0.411,
        "developer": "DeepSeek",
        "comment": "Reasoning-focused distill; lower extraction accuracy",
    },
}

# ════════════════════════════════════════════════════════════
# Open-source LLM scores from LLMStructBench paper (arXiv 2602.14743)
# Best prompting strategy (PJ+), F1_micro / Doc_micro / Composite
# Cross-referenced with SOB Overall for models appearing in both
# ════════════════════════════════════════════════════════════

PAPER_OPENSOURCE = {
    "Gemma3-27B":      {"f1_micro": 0.82, "doc_micro": 0.79, "composite": 0.805, "sob_overall": 0.847},
    "Qwen3-14B":       {"f1_micro": 0.79, "doc_micro": 0.75, "composite": 0.770, "sob_overall": None},
    "Gemma3-12B":      {"f1_micro": 0.78, "doc_micro": 0.76, "composite": 0.770, "sob_overall": None},
    "Phi-4-14B":       {"f1_micro": 0.77, "doc_micro": 0.72, "composite": 0.745, "sob_overall": None},
    "Qwen3-8B":        {"f1_micro": 0.75, "doc_micro": 0.71, "composite": 0.730, "sob_overall": None},
    "Llama3.3-70B":    {"f1_micro": 0.74, "doc_micro": 0.68, "composite": 0.710, "sob_overall": None},
    "GPT-4o":          {"f1_micro": 0.76, "doc_micro": 0.73, "composite": 0.745, "sob_overall": None},
    "DS-R1-Distill-32B":{"f1_micro": 0.73, "doc_micro": 0.66, "composite": 0.695, "sob_overall": 0.827},
}


def get_all_comparison() -> dict[str, dict]:
    """Return all comparison data as a flat dict."""
    all_data: dict[str, dict] = {}

    for name, info in LLM_STRUCT_BENCH.items():
        all_data[name] = {
            "f1_micro": info["f1_values"],
            "json_validity": info["json_validity"],
            "category": "Latest LLM (2026)",
            "developer": info.get("developer", ""),
            "comment": info.get("comment", ""),
        }

    for name, info in PAPER_OPENSOURCE.items():
        all_data[f"{name} (paper)"] = {
            "f1_micro": info["f1_micro"],
            "doc_micro": info.get("doc_micro"),
            "composite": info.get("composite"),
            "category": "LLMStructBench Paper",
        }

    return all_data
