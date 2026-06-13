"""Published LLM Matcher-Oracle benchmark data + Simulated Oracle calibration.

Data sources:
  - SOB (arXiv:2604.25359) — model pricing & capability ranking
  - LogMap-LLM (EACL 2026, arXiv:2508.08500) — oracle verification architecture
  - Lushnei et al. (EACL 2026) — Or_0~Or_30 simulated Oracle error rates
  - Agent-OM (PVLDB 2024) — Siamese LLM agents
  - Matchmaker (ICML 2025) — self-improving schema matching
"""

from __future__ import annotations


# ════════════════════════════════════════════════════════════
# LLM Matcher-Oracle (Hybrid matching + LLM oracle verification)
# F1: estimated pipeline F1 (Phase1 algo + Phase2 LLM oracle)
# Pricing: SOB Benchmark $/1M tokens (arXiv:2604.25359)
# Architecture: LogMap-LLM style uncertain-set verification
# ════════════════════════════════════════════════════════════

LLM_MATCHER_ORACLE = {
    "GPT-5.4": {
        "f1": 0.942,
        "cost_efficiency": "보통",
        "pricing": {"input_per_m": 2.50, "output_per_m": 15.00},
        "type": "Closed",
    },
    "Claude-Opus-4.7": {
        "f1": 0.935,
        "cost_efficiency": "낮음",
        "pricing": {"input_per_m": 15.0, "output_per_m": 75.0},
        "type": "Closed",
    },
    "GLM-5.1": {
        "f1": 0.925,
        "cost_efficiency": "최상",
        "pricing": {"input_per_m": 1.05, "output_per_m": 3.50},
        "type": "Open",
    },
    "Gemini-3.1-Pro": {
        "f1": 0.918,
        "cost_efficiency": "높음",
        "pricing": {"input_per_m": 2.00, "output_per_m": 12.00},
        "type": "Closed",
    },
    "GLM-4.7": {
        "f1": 0.910,
        "cost_efficiency": "최상",
        "pricing": {"input_per_m": 0.60, "output_per_m": 2.20},
        "type": "Open",
    },
    "Gemini-2.5-Flash": {
        "f1": 0.884,
        "cost_efficiency": "최상",
        "pricing": {"input_per_m": 0.30, "output_per_m": 2.50},
        "type": "Closed",
    },
    "Qwen3.5-35B": {
        "f1": 0.879,
        "cost_efficiency": "최상",
        "pricing": {"input_per_m": 0.163, "output_per_m": 1.30},
        "type": "Open",
    },
    "GPT-5-Mini": {
        "f1": 0.861,
        "cost_efficiency": "최상",
        "pricing": {"input_per_m": 0.50, "output_per_m": 1.50},
        "type": "Closed",
    },
    "Gemma-3-27B": {
        "f1": 0.815,
        "cost_efficiency": "보통",
        "pricing": {"input_per_m": 0.0, "output_per_m": 0.0},
        "type": "Open",
    },
    "DS-R1-Distill-32B": {
        "f1": 0.790,
        "cost_efficiency": "보통",
        "pricing": {"input_per_m": 0.0, "output_per_m": 0.0},
        "type": "Open",
    },
}


# ════════════════════════════════════════════════════════════
# Simulated Oracle Calibration (Lushnei et al. EACL 2026)
# Or_N = Oracle with N% error rate
# Key finding: LLM-Oracle ≈ Or_20 (~80% correct on uncertain mappings)
# ════════════════════════════════════════════════════════════

SIMULATED_ORACLE = {
    "Or_0":  {"error_rate": 0.00, "label": "Perfect Oracle"},
    "Or_5":  {"error_rate": 0.05, "label": "Near-Perfect"},
    "Or_10": {"error_rate": 0.10, "label": "Excellent"},
    "Or_15": {"error_rate": 0.15, "label": "Very Good"},
    "Or_20": {"error_rate": 0.20, "label": "Good (≈ LLM-Oracle baseline)"},
    "Or_25": {"error_rate": 0.25, "label": "Fair"},
    "Or_30": {"error_rate": 0.30, "label": "Marginal"},
}


# ════════════════════════════════════════════════════════════
# Architecture Comparison
# ════════════════════════════════════════════════════════════

ARCHITECTURE_COMPARISON = {
    "CostReady (Hybrid Engine)": {
        "phase1": "8-Tier T0a-T5 (Path/Fuzzy/DAL)",
        "oracle": "M1-M5 Det + T6 LLM fallback",
        "llm_usage": "Minimal (T6 for unmatched only)",
        "cost": "$0 (self-hosted)",
        "verifier": "Deterministic (M1-M5, 14 codes)",
    },
    "LogMap + LLM Oracle": {
        "phase1": "LogMap (lexical + structural)",
        "oracle": "LLM Yes/No (all uncertain)",
        "llm_usage": "Moderate (uncertain subset only)",
        "cost": "$$ (API per call)",
        "verifier": "LLM (probabilistic)",
    },
    "Pure LLM Matching": {
        "phase1": "— (no algorithm matcher)",
        "oracle": "LLM full matching",
        "llm_usage": "Maximum (all pairs)",
        "cost": "$$$ (highest)",
        "verifier": "None or LLM self-check",
    },
}


# ════════════════════════════════════════════════════════════
# Youden's Index Grade Thresholds
# ════════════════════════════════════════════════════════════

YI_GRADES = [
    (0.95, "S", "완벽 / Perfect"),
    (0.90, "A+", "탁월 / Excellent"),
    (0.80, "A",  "우수 / Very Good"),
    (0.70, "B",  "양호 / Good"),
    (0.50, "C",  "보통 / Fair"),
    (0.00, "D",  "불량 / Poor"),
]


def grade_youden(yi: float) -> tuple[str, str]:
    """Return (grade, description) for a given Youden's Index."""
    for threshold, grade, desc in YI_GRADES:
        if yi >= threshold:
            return grade, desc
    return "D", "불량 / Poor"


# ════════════════════════════════════════════════════════════
# Cost estimation helper
# ════════════════════════════════════════════════════════════

def estimate_cost_per_1k_calls(pricing: dict) -> float:
    """Estimate cost per 1000 oracle calls.

    Assumes ~100 input tokens + ~5 output tokens per oracle call.
    """
    input_per_m = pricing.get("input_per_m", 0.0)
    output_per_m = pricing.get("output_per_m", 0.0)
    return (100 * input_per_m + 5 * output_per_m) / 1_000_000 * 1000


def get_all_comparison_data() -> dict:
    """Return all comparison data as a single dict."""
    return {
        "llm_matcher_oracle": LLM_MATCHER_ORACLE,
        "simulated_oracle": SIMULATED_ORACLE,
        "architecture_comparison": ARCHITECTURE_COMPARISON,
        "yi_grades": YI_GRADES,
    }
