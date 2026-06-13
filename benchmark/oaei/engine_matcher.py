"""Wrapper to run the engine's DM pipeline for OAEI benchmarking.

Uses DynamicTemplateMapper.auto_match() which internally invokes the full
8-Tier (T-1~T5) StrategySelector → TopologicalMatcher pipeline with proper
path construction and DAL map injection — identical to production behavior.

Produces system alignments (source_field -> target_field) that can be
compared against reference alignments using standard OAEI metrics.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from oaei_metrics import Alignment


_ENGINE_SRC = str(
    Path(__file__).resolve().parent.parent.parent / "src"
)


def _ensure_path() -> None:
    if _ENGINE_SRC not in sys.path:
        sys.path.insert(0, _ENGINE_SRC)


def run_engine_match_for_case(
    extraction_xlsx: str | Path,
    template_xlsx: str | Path,
    enable_llm: bool = False,
) -> tuple[list[Alignment], float]:
    """Run full DM pipeline matching for a single test case.

    Uses DynamicTemplateMapper.auto_match() which internally invokes
    StrategySelector → TopologicalMatcher with all 8 tiers (T-1~T5)
    enabled via proper path construction and DAL map injection.

    Args:
        extraction_xlsx: Pipeline output (_맵핑.xlsx or _맵핑_allobject.xlsx).
        template_xlsx: Golden template file.
        enable_llm: If True, enable T6 LLM tier (requires VLM server).

    Returns:
        (alignments, elapsed_seconds)
    """
    _ensure_path()

    from mapper.dynamic_template_mapper import (
        DynamicTemplateMapper,
        load_source_data,
    )

    t0 = time.time()

    mapper = DynamicTemplateMapper()
    ts = mapper.parse_template(str(template_xlsx), sheet_name="")
    source = load_source_data(str(extraction_xlsx), sheet_name_filter="")

    mappings = mapper.auto_match(ts, source["source_columns"])

    alignments: list[Alignment] = []
    for fm in mappings:
        if not fm.matched or fm.excluded:
            continue
        if fm.confidence <= 0:
            continue

        src = fm.source_field or fm.source_path.split("::")[-1]
        tgt = fm.target_field
        section = fm.section or ""

        if "::" in tgt:
            tgt = tgt.split("::")[-1]

        ns = f"{section}::" if section else ""
        alignments.append(Alignment(
            source=f"{ns}{src}",
            target=f"{ns}{tgt}",
            confidence=fm.confidence,
        ))

    elapsed = time.time() - t0
    return alignments, elapsed


def run_engine_benchmark(
    cases: list[dict],
    reference_per_case: dict[str, list[Alignment]],
    use_llm: bool = False,
) -> tuple[object, dict[str, list[Alignment]]]:
    """Run engine DM matching for all cases and evaluate.

    Args:
        cases: List of case dicts with stem/extraction_xlsx/template_xlsx.
        reference_per_case: Gold-standard alignments per case.
        use_llm: Enable LLM semantic tier (T6).

    Returns:
        (AggregateResult, system_alignments_per_case)
    """
    from oaei_metrics import evaluate_batch

    system_per_case: dict[str, list[Alignment]] = {}

    for case in cases:
        stem = case["stem"]
        extraction_xlsx = case.get("extraction_xlsx", "")
        template_xlsx = case.get("template_xlsx", "")

        print(f"\n{'='*60}")
        print(f"Processing: {stem}")

        if not extraction_xlsx or not template_xlsx:
            print(f"  [SKIP] Missing extraction or template file")
            continue

        alignments, elapsed = run_engine_match_for_case(
            extraction_xlsx=extraction_xlsx,
            template_xlsx=template_xlsx,
            enable_llm=use_llm,
        )

        system_per_case[stem] = alignments
        matched = sum(1 for a in alignments if a.confidence > 0)
        print(f"  DM auto_match: {matched} alignments in {elapsed:.1f}s")

    valid_refs = {
        stem: refs for stem, refs in reference_per_case.items()
        if stem in {c["stem"] for c in cases}
    }

    if not valid_refs:
        print("\n[WARN] No matching reference cases found. Using all references.")
        valid_refs = reference_per_case

    agg = evaluate_batch(system_per_case, valid_refs)
    return agg, system_per_case
