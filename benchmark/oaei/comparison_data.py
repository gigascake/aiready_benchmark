"""Published OAEI benchmark results for comparison.

Sources:
- OAEI 2024 Conference Track: https://oaei.ontologymatching.org/2024/results/conference/
- OAEI 2024 Results Paper: ceur-ws.org/Vol-3897/oaei2024_paper0.pdf
- LLMs4OM (ESWC 2024): https://2024.eswc-conferences.org/wp-content/uploads/2024/05/77770022.pdf
- Agent-OM (PVLDB 2024): https://www.vldb.org/pvldb/vol18/p516-qiang.pdf
- OAEI-LLM (ISWC 2024): https://arxiv.org/html/2409.14038v2

All values are F1-measure unless otherwise noted.
"""

from __future__ import annotations

# ════════════════════════════════════════════════════════════
# OAEI 2024 Conference Track (rar2-M3, sharp reference alignment)
# Micro-averaged Precision/Recall/F1 across 21 test cases
# Source: OAEI 2024 Results Paper, Table 10
# ════════════════════════════════════════════════════════════

OAEI_2024_CONFERENCE = {
    "ALIN":       {"precision": 0.82, "recall": 0.44, "f1": 0.57},
    "LogMap":     {"precision": 0.76, "recall": 0.56, "f1": 0.64},
    "Matcha":     {"precision": 0.66, "recall": 0.63, "f1": 0.64},
    "MDMapper":   {"precision": 0.66, "recall": 0.53, "f1": 0.59},
    "LogMapLt":   {"precision": 0.68, "recall": 0.47, "f1": 0.56},
    "OntoMatch":  {"precision": 0.82, "recall": 0.43, "f1": 0.56},
    "TOMATO":     {"precision": 0.57, "recall": 0.42, "f1": 0.48},
    "edna (baseline)":      {"precision": 0.74, "recall": 0.45, "f1": 0.56},
    "StringEquiv (baseline)": {"precision": 0.76, "recall": 0.41, "f1": 0.53},
}

# ════════════════════════════════════════════════════════════
# OAEI 2024 Anatomy Track (Mouse-Human)
# Source: OAEI 2024 Results Paper, Table 9
# ════════════════════════════════════════════════════════════

OAEI_2024_ANATOMY = {
    "Matcha":     {"precision": 0.951, "recall": 0.931, "f1": 0.941},
    "LogMapBio":  {"precision": 0.888, "recall": 0.908, "f1": 0.898},
    "MDMapper":   {"precision": 0.926, "recall": 0.881, "f1": 0.903},
    "LogMap":     {"precision": 0.917, "recall": 0.848, "f1": 0.881},
    "ALIN":       {"precision": 0.984, "recall": 0.750, "f1": 0.851},
    "LogMapLt":   {"precision": 0.962, "recall": 0.728, "f1": 0.828},
    "TOMATO":     {"precision": 0.955, "recall": 0.360, "f1": 0.523},
}

# ════════════════════════════════════════════════════════════
# OAEI 2024 Knowledge Graph Track (Overall)
# Source: OAEI 2024 Results Paper, Table 25
# ════════════════════════════════════════════════════════════

OAEI_2024_KG = {
    "BaselineAltLabel": {"precision": 0.89, "recall": 0.80, "f1": 0.84},
    "BaselineLabel":    {"precision": 0.95, "recall": 0.71, "f1": 0.80},
    "LogMap":           {"precision": 0.90, "recall": 0.68, "f1": 0.77},
    "Matcha":           {"precision": 0.55, "recall": 0.84, "f1": 0.63},
}

# ════════════════════════════════════════════════════════════
# LLMs4OM Results (ESWC 2024) — Zero-shot LLM Matching
# Best model per task with best concept representation
# Source: LLMs4OM Table 1 (GPT-3.5, LLaMA-2, Mistral)
# ════════════════════════════════════════════════════════════

LLMS4OM_RESULTS = {
    # Anatomy
    "GPT-3.5 (Anatomy)": {
        "precision": 0.9082, "recall": 0.8746, "f1": 0.8911,
        "model": "GPT-3.5", "retriever": "text-embedding-ada",
        "track": "Anatomy", "oaei_best": 0.941,
    },
    # CommonKG
    "GPT-3.5 (Nell-DBpedia)": {
        "precision": 1.0, "recall": 0.8914, "f1": 0.9426,
        "model": "GPT-3.5", "retriever": "text-embedding-ada",
        "track": "CommonKG", "oaei_best": 0.96,
    },
    "LLaMA-2 (YAGO-Wikidata)": {
        "precision": 1.0, "recall": 0.8552, "f1": 0.9219,
        "model": "LLaMA-2-7B", "retriever": "text-embedding-ada",
        "track": "CommonKG", "oaei_best": 0.94,
    },
    # Phenotype
    "Mistral (DOID-ORDO)": {
        "precision": 0.8579, "recall": 0.9426, "f1": 0.8983,
        "model": "Mistral-7B", "retriever": "sentence-BERT",
        "track": "Phenotype", "oaei_best": 0.755,
    },
    "Mistral (HP-MP)": {
        "precision": 0.7667, "recall": 0.954, "f1": 0.8501,
        "model": "Mistral-7B", "retriever": "sentence-BERT",
        "track": "Phenotype", "oaei_best": 0.818,
    },
    # MSE
    "LLaMA-2 (MI-EMMO)": {
        "precision": 0.9666, "recall": 0.9206, "f1": 0.943,
        "model": "LLaMA-2-7B", "retriever": "sentence-BERT",
        "track": "MSE", "oaei_best": 0.918,
    },
    # Bio-ML (best LLM)
    "GPT-3.5 (NCIT-DOID)": {
        "precision": 0.8619, "recall": 0.8006, "f1": 0.8301,
        "model": "GPT-3.5", "retriever": "text-embedding-ada",
        "track": "Bio-ML", "oaei_best": 0.908,
    },
}

# ════════════════════════════════════════════════════════════
# LLM-Specific OM Systems (from literature)
# ════════════════════════════════════════════════════════════

LLM_OM_SYSTEMS = {
    # Agent-OM (VLDB 2024) — GPT-4o based, Conference track
    "Agent-OM (GPT-4o)": {
        "precision": 0.89, "recall": 0.85, "f1": 0.87,
        "track": "Conference (subset)",
        "source": "VLDB 2024 — Qiang et al.",
    },
    # OLaLa (K-CAP 2023) — LLaMA-2 based
    "OLaLa (LLaMA-2)": {
        "precision": None, "recall": None, "f1": 0.80,
        "track": "Biodiversity (Fungi)",
        "source": "K-CAP 2023 — Hertling & Paulheim",
    },
    # CANARD 2024 — LLM embeddings (Complex Matching)
    "CANARD 2024 (Stella-base)": {
        "precision": 0.389, "recall": None, "f1": 0.623,
        "track": "Complex Matching (Conference)",
        "source": "OAEI 2024",
    },
    "CANARD 2024 (GritLM-7B)": {
        "precision": 0.359, "recall": None, "f1": 0.679,
        "track": "Complex Matching (Conference)",
        "source": "OAEI 2024",
    },
    # LLMap — Flan-T5 / GPT-3.5 zero-shot
    "LLMap (Flan-T5)": {
        "precision": None, "recall": None, "f1": None,
        "track": "Conference",
        "source": "ISWC 2023 — He et al.",
        "note": "Zero-shot, performance varies; generally F1 < 0.50",
    },
}


# ════════════════════════════════════════════════════════════
# Latest LLM Schema Alignment
# Source: SOB (Structured Output Benchmark) arXiv:2604.25359
# SOB Overall score used as schema alignment capability proxy
# Hallucination profile from OAEI-LLM-T (arXiv:2503.21813)
# ════════════════════════════════════════════════════════════

LLM_LATEST_SCHEMA_ALIGNMENT = {
    "GPT-5.4":           {"f1": 0.870, "hallucination": "매우 낮음"},
    "Gemini-3.1-Pro":    {"f1": 0.869, "hallucination": "간혹 단순화"},
    "GLM-5.1":           {"f1": 0.866, "hallucination": "낮음"},
    "Claude-Opus-4.7":   {"f1": 0.864, "hallucination": "낮음"},
    "GLM-4.7":           {"f1": 0.861, "hallucination": "낮음"},
    "Qwen3.5-35B":       {"f1": 0.861, "hallucination": "미세 오차"},
    "GPT-5.5":           {"f1": 0.860, "hallucination": "낮음"},
    "Gemini-2.5-Flash":  {"f1": 0.860, "hallucination": "간혹 단순화"},
    "Gemma-3-27B":       {"f1": 0.847, "hallucination": "구조적 환각 높음"},
    "DS-R1-Distill-32B": {"f1": 0.827, "hallucination": "구조적 환각 높음"},
}

# ════════════════════════════════════════════════════════════
# Matcher-Oracle (Hybrid matching + LLM oracle verification)
# F1 estimates based on SOB Overall ranking + LogMap-LLM (EACL 2026)
# Cost efficiency from SOB pricing ($/1M tokens)
# ════════════════════════════════════════════════════════════

LLM_MATCHER_ORACLE = {
    "GPT-5.4":           {"f1": 0.942, "cost_efficiency": "보통"},
    "Claude-Opus-4.7":   {"f1": 0.935, "cost_efficiency": "낮음"},
    "Gemini-3.1-Pro":    {"f1": 0.918, "cost_efficiency": "높음"},
    "GLM-5.1":           {"f1": 0.925, "cost_efficiency": "최상"},
    "GLM-4.7":           {"f1": 0.910, "cost_efficiency": "최상"},
    "Gemini-2.5-Flash":  {"f1": 0.884, "cost_efficiency": "최상"},
    "Qwen3.5-35B":       {"f1": 0.879, "cost_efficiency": "높음"},
    "GPT-5-Mini":        {"f1": 0.861, "cost_efficiency": "최상"},
    "Gemma-3-27B":       {"f1": 0.815, "cost_efficiency": "보통"},
    "DS-R1-Distill-32B": {"f1": 0.790, "cost_efficiency": "보통"},
}

# ════════════════════════════════════════════════════════════
# LLM Structured Data Conversion (SOB Benchmark)
# Source: SOB arXiv:2604.25359 — Overall score + JSON Pass rate
# SOB is the multimodal expansion of LLMStructBench (5,000+ records)
# ════════════════════════════════════════════════════════════

LLM_STRUCT_BENCH = {
    "GPT-5.4":           {"f1": 0.870, "json_validity": 0.993},
    "Gemini-3.1-Pro":    {"f1": 0.869, "json_validity": 0.966},
    "GLM-5.1":           {"f1": 0.866, "json_validity": 0.975},
    "Claude-Opus-4.7":   {"f1": 0.864, "json_validity": 0.993},
    "GLM-4.7":           {"f1": 0.861, "json_validity": 0.965},
    "Qwen3.5-35B":       {"f1": 0.861, "json_validity": 0.969},
    "GPT-5.5":           {"f1": 0.860, "json_validity": 0.978},
    "Gemini-2.5-Flash":  {"f1": 0.860, "json_validity": 0.972},
    "Gemma-3-27B":       {"f1": 0.847, "json_validity": 0.969},
    "DS-R1-Distill-32B": {"f1": 0.827, "json_validity": 0.960},
}


def get_all_comparison_data() -> dict[str, dict]:
    """Return all published results as a flat dict for comparison tables."""
    all_data: dict[str, dict] = {}

    for name, metrics in OAEI_2024_CONFERENCE.items():
        all_data[f"OAEI2024/Conference/{name}"] = {
            **metrics, "category": "OAEI 2024 Traditional", "track": "Conference",
        }

    for name, metrics in OAEI_2024_ANATOMY.items():
        all_data[f"OAEI2024/Anatomy/{name}"] = {
            **metrics, "category": "OAEI 2024 Traditional", "track": "Anatomy",
        }

    for name, metrics in OAEI_2024_KG.items():
        all_data[f"OAEI2024/KG/{name}"] = {
            **metrics, "category": "OAEI 2024 Traditional", "track": "Knowledge Graph",
        }

    for name, info in LLMS4OM_RESULTS.items():
        all_data[f"LLMs4OM/{name}"] = {
            "precision": info["precision"],
            "recall": info["recall"],
            "f1": info["f1"],
            "category": "LLM Zero-Shot",
            "track": info["track"],
        }

    for name, info in LLM_OM_SYSTEMS.items():
        all_data[f"LLM-OM/{name}"] = {
            "precision": info.get("precision"),
            "recall": info.get("recall"),
            "f1": info.get("f1"),
            "category": "LLM Agent",
            "track": info.get("track", ""),
        }

    return all_data
