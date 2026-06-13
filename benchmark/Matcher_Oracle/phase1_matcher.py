"""Phase 1: Algorithm matching via engine's DM pipeline (full 8-Tier).

Uses DynamicTemplateMapper.auto_match() which internally invokes the full
StrategySelector → TopologicalMatcher pipeline with all tiers (T-1~T5)
enabled via proper path construction and DAL map injection.

Produces candidate alignments and identifies the uncertain set (M_ask)
for Phase 2 oracle verification.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from dataclasses import dataclass, field

from oracle_metrics import Alignment


_ENGINE_SRC = str(
    Path(__file__).resolve().parent.parent.parent / "src"
)
_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent


def _ensure_path() -> None:
    if _ENGINE_SRC not in sys.path:
        sys.path.insert(0, _ENGINE_SRC)


UNCERTAIN_CONFIDENCE_THRESHOLD = 0.85


# ════════════════════════════════════════════════════════════
# Data structures
# ════════════════════════════════════════════════════════════

@dataclass
class Phase1Result:
    """Result of Phase 1 algorithm matching."""

    alignments: list[Alignment] = field(default_factory=list)
    uncertain_set: list[Alignment] = field(default_factory=list)
    confident_set: list[Alignment] = field(default_factory=list)
    tier_distribution: dict[str, int] = field(default_factory=dict)
    elapsed: float = 0.0

    @property
    def total_candidates(self) -> int:
        return len(self.alignments)

    @property
    def uncertain_count(self) -> int:
        return len(self.uncertain_set)


# ════════════════════════════════════════════════════════════
# Phase 1 matching via DM auto_match (full 8-Tier pipeline)
# ════════════════════════════════════════════════════════════

def run_phase1_for_case(
    extraction_xlsx: str | Path,
    template_xlsx: str | Path,
) -> Phase1Result:
    """Run Phase 1 matching via DM auto_match (full 8-Tier).

    Uses DynamicTemplateMapper.auto_match() which internally invokes
    StrategySelector → TopologicalMatcher with all tiers (T-1~T5)
    enabled via proper path construction and DAL map injection.

    Args:
        extraction_xlsx: Pipeline output file (_맵핑.xlsx).
        template_xlsx: Golden template file.

    Returns:
        Phase1Result with alignments + uncertain/confident split.
    """
    _ensure_path()
    t0 = time.time()

    from mapper.dynamic_template_mapper import (
        DynamicTemplateMapper,
        load_source_data,
    )

    mapper = DynamicTemplateMapper()
    ts = mapper.parse_template(str(template_xlsx), sheet_name="")
    source = load_source_data(str(extraction_xlsx), sheet_name_filter="")

    mappings = mapper.auto_match(ts, source["source_columns"])

    all_alignments: list[Alignment] = []
    uncertain: list[Alignment] = []
    confident: list[Alignment] = []
    tier_dist: dict[str, int] = {}

    for fm in mappings:
        if not fm.matched or fm.excluded:
            continue
        if fm.confidence <= 0:
            continue

        src = fm.source_field or fm.source_path.split("::")[-1]
        tgt = fm.target_field
        section = fm.section or ""
        tier = fm.match_tier or "T?"

        if "::" in tgt:
            tgt = tgt.split("::")[-1]

        ns = f"{section}::" if section else ""
        align = Alignment(
            source=f"{ns}{src}",
            target=f"{ns}{tgt}",
            confidence=fm.confidence,
            tier=tier,
        )

        all_alignments.append(align)
        tier_dist[tier] = tier_dist.get(tier, 0) + 1

        if fm.confidence < UNCERTAIN_CONFIDENCE_THRESHOLD or tier == "T5":
            uncertain.append(align)
        else:
            confident.append(align)

    elapsed = time.time() - t0

    return Phase1Result(
        alignments=all_alignments,
        uncertain_set=uncertain,
        confident_set=confident,
        tier_distribution=tier_dist,
        elapsed=elapsed,
    )
