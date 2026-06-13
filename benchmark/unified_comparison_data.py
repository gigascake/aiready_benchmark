"""Unified LLM comparison data across all 3 benchmarks.

Aggregates published LLM scores from:
  - OAEI: oaei/comparison_data.py (LLM_LATEST_SCHEMA_ALIGNMENT)
  - LLMStructBench: llmstructbench/comparison_data.py (LLM_STRUCT_BENCH)
  - Matcher-Oracle: Matcher_Oracle/comparison_data.py (LLM_MATCHER_ORACLE)

Source: SOB Benchmark (arXiv:2604.25359) + LogMap-LLM (EACL 2026)
"""

from __future__ import annotations


# ════════════════════════════════════════════════════════════
# Cross-Benchmark LLM Performance Matrix
# Each model has scores in 1-3 benchmarks. Missing = None.
# oaei: SOB Overall (schema alignment proxy)
# llmstructbench: SOB Overall (structured data conversion)
# matcher_oracle: Estimated pipeline F1 (Phase1 algo + Phase2 LLM oracle)
# ════════════════════════════════════════════════════════════

UNIFIED_LLM_SCORES = {
    "GPT-5.4": {
        "oaei": 0.870,
        "llmstructbench": 0.870,
        "matcher_oracle": 0.942,
        "type": "Closed",
        "cost": "보통",
    },
    "Gemini-3.1-Pro": {
        "oaei": 0.869,
        "llmstructbench": 0.869,
        "matcher_oracle": 0.918,
        "type": "Closed",
        "cost": "높음",
    },
    "GLM-5.1": {
        "oaei": 0.866,
        "llmstructbench": 0.866,
        "matcher_oracle": 0.925,
        "type": "Open",
        "cost": "최상",
    },
    "Claude-Opus-4.7": {
        "oaei": 0.864,
        "llmstructbench": 0.864,
        "matcher_oracle": 0.935,
        "type": "Closed",
        "cost": "낮음",
    },
    "GLM-4.7": {
        "oaei": 0.861,
        "llmstructbench": 0.861,
        "matcher_oracle": 0.910,
        "type": "Open",
        "cost": "최상",
    },
    "Qwen3.5-35B": {
        "oaei": 0.861,
        "llmstructbench": 0.861,
        "matcher_oracle": 0.879,
        "type": "Open",
        "cost": "최상",
    },
    "GPT-5.5": {
        "oaei": 0.860,
        "llmstructbench": 0.860,
        "matcher_oracle": None,
        "type": "Closed",
        "cost": "보통",
    },
    "Gemini-2.5-Flash": {
        "oaei": 0.860,
        "llmstructbench": 0.860,
        "matcher_oracle": 0.884,
        "type": "Closed",
        "cost": "최상",
    },
    "Gemma-3-27B": {
        "oaei": 0.847,
        "llmstructbench": 0.847,
        "matcher_oracle": 0.815,
        "type": "Open",
        "cost": "보통",
    },
    "DS-R1-Distill-32B": {
        "oaei": 0.827,
        "llmstructbench": 0.827,
        "matcher_oracle": 0.790,
        "type": "Open",
        "cost": "보통",
    },
}


# ════════════════════════════════════════════════════════════
# Grade thresholds
# ════════════════════════════════════════════════════════════

GRADE_THRESHOLDS = [
    (0.97, "S",  "최상위 / Supreme"),
    (0.92, "A+", "탁월 / Excellent"),
    (0.87, "A",  "우수 / Very Good"),
    (0.82, "B",  "양호 / Good"),
    (0.75, "C",  "보통 / Fair"),
    (0.00, "D",  "불량 / Poor"),
]


def compute_grade(avg_f1: float) -> tuple[str, str]:
    """Return (grade, description) for a given average F1."""
    for threshold, grade, desc in GRADE_THRESHOLDS:
        if avg_f1 >= threshold:
            return grade, desc
    return "D", "불량 / Poor"


def avg_llm_scores(model: str) -> float | None:
    """Compute average F1 across available benchmarks for a model."""
    info = UNIFIED_LLM_SCORES.get(model, {})
    scores = [v for k, v in info.items() if k in ("oaei", "llmstructbench", "matcher_oracle") and v is not None]
    return sum(scores) / len(scores) if scores else None
