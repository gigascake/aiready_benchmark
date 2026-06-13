"""Gap analysis for Matcher-Oracle benchmark.

All analysis computed from actual benchmark measurements — no hardcoded numbers.
Analyzes:
  1. Oracle value-add (Phase1 F1 → Phase2 F1 delta)
  2. LLM call reduction rate
  3. Cost savings vs Pure LLM
  4. Oracle quality grade (Youden's Index)
  5. Simulated Oracle equivalent (Or_N matching)
  6. LLM comparison gap (Engine vs published LLM scores)
  7. Phase 1 bottleneck analysis (FP/FN identification)
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from oracle_metrics import Alignment, OracleEvaluation, evaluate_phase
from comparison_data import LLM_MATCHER_ORACLE, SIMULATED_ORACLE, grade_youden


@dataclass
class GapResult:
    """Auto-computed gap analysis result."""

    # Oracle value-add
    oracle_delta_llm: float = 0.0
    oracle_delta_det: float = 0.0
    oracle_delta_best: float = 0.0

    # LLM call efficiency
    llm_call_ratio: float = 0.0
    llm_call_reduction: float = 0.0

    # Cost
    cost_saved_pct: float = 0.0

    # Oracle quality
    yi_best: float = 0.0
    grade_best: str = ""
    grade_desc: str = ""
    oracle_equivalent: str = ""

    # vs published LLM scores
    gap_vs_best_llm: float = 0.0
    gap_vs_gpt54: float = 0.0
    best_llm_name: str = ""
    best_llm_f1: float = 0.0

    # FP/FN
    fp_pairs: list[Alignment] = field(default_factory=list)
    fn_pairs: list[Alignment] = field(default_factory=list)
    fp_by_section: Counter = field(default_factory=Counter)
    fn_by_section: Counter = field(default_factory=Counter)

    # Phase 1 tier distribution
    tier_distribution: dict[str, int] = field(default_factory=dict)

    # Insights
    insights: list[str] = field(default_factory=list)


def run_gap_analysis(
    evaluations: dict[str, OracleEvaluation],
    phase1_alignments: list[Alignment],
    reference_alignments: list[Alignment],
    tier_distribution: dict[str, int],
    cost_saved_pct: float = 0.0,
) -> GapResult:
    """Run complete gap analysis from actual benchmark data.

    Args:
        evaluations: {"LLM": ev, "Det": ev, "None": ev}
        phase1_alignments: All Phase 1 output alignments.
        reference_alignments: Gold standard.
        tier_distribution: {tier: count} from Phase 1.
        cost_saved_pct: Cost saved percentage from cost analyzer.

    Returns:
        GapResult with all auto-computed values.
    """
    gap = GapResult()
    gap.tier_distribution = tier_distribution
    gap.cost_saved_pct = cost_saved_pct

    # 1. Oracle value-add
    if "None" in evaluations:
        baseline_f1 = evaluations["None"].phase1_f1
    else:
        p1 = evaluate_phase("P1", phase1_alignments, reference_alignments)
        baseline_f1 = p1.f1

    if "LLM" in evaluations:
        gap.oracle_delta_llm = evaluations["LLM"].oracle_f1 - baseline_f1
    if "Det" in evaluations:
        gap.oracle_delta_det = evaluations["Det"].oracle_f1 - baseline_f1

    gap.oracle_delta_best = max(gap.oracle_delta_llm, gap.oracle_delta_det)

    # 2. LLM call efficiency
    if "LLM" in evaluations:
        ev = evaluations["LLM"]
        gap.llm_call_ratio = ev.llm_calls / ev.total_uncertain if ev.total_uncertain > 0 else 0.0
        gap.llm_call_reduction = 1.0 - gap.llm_call_ratio

    # 3. Oracle quality (best mode)
    best_ev = None
    best_yi = -1.0
    for mode in ["Det", "LLM"]:
        if mode in evaluations:
            ev = evaluations[mode]
            if ev.youden_index > best_yi:
                best_yi = ev.youden_index
                best_ev = ev

    if best_ev:
        gap.yi_best = best_ev.youden_index
        gap.grade_best, gap.grade_desc = grade_youden(best_ev.youden_index)
        gap.oracle_equivalent = best_ev.simulated_oracle_equivalent

    # 4. vs published LLM scores
    best_llm_name = max(LLM_MATCHER_ORACLE, key=lambda k: LLM_MATCHER_ORACLE[k]["f1"])
    best_llm_f1 = LLM_MATCHER_ORACLE[best_llm_name]["f1"]
    gap.best_llm_name = best_llm_name
    gap.best_llm_f1 = best_llm_f1

    engine_best_f1 = max(
        (ev.oracle_f1 for ev in evaluations.values() if ev.oracle_f1 > 0),
        default=0.0,
    )
    gap.gap_vs_best_llm = engine_best_f1 - best_llm_f1
    gap.gap_vs_gpt54 = engine_best_f1 - LLM_MATCHER_ORACLE.get("GPT-5.4", {}).get("f1", 0.0)

    # 5. FP/FN identification (using best evaluation)
    ref_set = {a.key() for a in reference_alignments}
    sys_set = {a.key() for a in phase1_alignments}

    fp_keys = sys_set - ref_set
    fn_keys = ref_set - sys_set

    gap.fp_pairs = [a for a in phase1_alignments if a.key() in fp_keys][:20]
    gap.fn_pairs = [a for a in reference_alignments if a.key() in fn_keys][:20]

    for a in gap.fp_pairs:
        section = a.source.split("::")[0] if "::" in a.source else "unknown"
        gap.fp_by_section[section] += 1
    for a in gap.fn_pairs:
        section = a.source.split("::")[0] if "::" in a.source else "unknown"
        gap.fn_by_section[section] += 1

    # 6. Auto-generate insights
    gap.insights = _generate_insights(gap, evaluations)

    return gap


def _generate_insights(gap: GapResult, evaluations: dict[str, OracleEvaluation]) -> list[str]:
    """Auto-generate human-readable insights from gap analysis."""
    insights: list[str] = []

    # Oracle value
    if gap.oracle_delta_best > 0:
        insights.append(
            f"Oracle verification improved F1 by **+{gap.oracle_delta_best:.4f}** "
            f"(Det: {gap.oracle_delta_det:+.4f}, LLM: {gap.oracle_delta_llm:+.4f})"
        )
    elif gap.oracle_delta_best < 0:
        insights.append(
            f"Oracle verification **decreased** F1 by {gap.oracle_delta_best:+.4f} — "
            f"the oracle rejected some true matches"
        )
    else:
        insights.append(
            "Oracle verification **did not change** F1 — "
            "Phase 1 output was already optimal for this test set"
        )

    # LLM efficiency
    if gap.llm_call_reduction > 0:
        insights.append(
            f"Only **{1-gap.llm_call_reduction:.1%}** of candidates required LLM verification "
            f"({gap.llm_call_reduction:.1%} handled deterministically)"
        )

    # Cost
    if gap.cost_saved_pct > 0:
        insights.append(
            f"Cost savings vs Pure LLM: **{gap.cost_saved_pct:.1%}** "
            f"(algorithm pre-filtering eliminates most LLM calls)"
        )

    # Oracle quality
    insights.append(
        f"Oracle quality: Youden's Index = **{gap.yi_best:.4f}** [{gap.grade_best}] "
        f"({gap.grade_desc}) — equivalent to **{gap.oracle_equivalent}** simulated Oracle"
    )

    # vs LLM
    if gap.gap_vs_best_llm > 0:
        insights.append(
            f"Engine **outperforms** best published LLM ({gap.best_llm_name}: {gap.best_llm_f1:.1%}) "
            f"by **+{gap.gap_vs_best_llm:.4f}** F1"
        )
    else:
        insights.append(
            f"Engine F1 gap vs best LLM ({gap.best_llm_name}): {gap.gap_vs_best_llm:+.4f}"
        )

    return insights


def generate_gap_markdown(gap: GapResult) -> list[str]:
    """Generate gap analysis section as markdown lines."""
    lines: list[str] = []

    lines.append("\n## 7. Gap Analysis (Auto-computed)\n")
    lines.append("> All values below are **computed from actual benchmark data**.\n")

    # Summary metrics
    lines.append("### 7-1. Oracle Value-Add\n")
    lines.append("| Mode | Phase1 F1 | Oracle F1 | Delta |")
    lines.append("|------|-----------|-----------|-------|")
    lines.append(
        f"| Det Oracle | — | — | {gap.oracle_delta_det:+.4f} |"
    )
    lines.append(
        f"| LLM Oracle | — | — | {gap.oracle_delta_llm:+.4f} |"
    )
    lines.append(
        f"| **Best** | — | — | **{gap.oracle_delta_best:+.4f}** |"
    )
    lines.append("")

    # Oracle quality
    lines.append("### 7-2. Oracle Diagnostic Quality\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Youden's Index | {gap.yi_best:.4f} |")
    lines.append(f"| Grade | **{gap.grade_best}** ({gap.grade_desc}) |")
    lines.append(f"| Simulated Oracle Equivalent | **{gap.oracle_equivalent}** |")
    lines.append("")

    # Cost
    lines.append("### 7-3. Cost Efficiency\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| LLM Call Ratio | {1-gap.llm_call_reduction:.1%} of uncertain set |")
    lines.append(f"| LLM Call Reduction | {gap.llm_call_reduction:.1%} |")
    lines.append(f"| Cost Saved vs Pure LLM | {gap.cost_saved_pct:.1%} |")
    lines.append("")

    # vs LLM
    lines.append("### 7-4. vs Published LLM Scores\n")
    lines.append(f"| Comparison | F1 Gap |")
    lines.append(f"|------------|--------|")
    lines.append(f"| vs {gap.best_llm_name} (best LLM) | {gap.gap_vs_best_llm:+.4f} |")
    lines.append(f"| vs GPT-5.4 | {gap.gap_vs_gpt54:+.4f} |")
    lines.append("")

    # FP/FN
    if gap.fp_pairs:
        lines.append("### 7-5. False Positive Analysis\n")
        lines.append(f"**Total FP: {len(gap.fp_pairs)}+**\n")
        if gap.fp_by_section:
            lines.append("| Section | FP Count |")
            lines.append("|---------|----------|")
            for section, count in gap.fp_by_section.most_common(10):
                lines.append(f"| {section} | {count} |")
            lines.append("")

    if gap.fn_pairs:
        lines.append("### 7-6. False Negative Analysis\n")
        lines.append(f"**Total FN: {len(gap.fn_pairs)}+**\n")
        if gap.fn_by_section:
            lines.append("| Section | FN Count |")
            lines.append("|---------|----------|")
            for section, count in gap.fn_by_section.most_common(10):
                lines.append(f"| {section} | {count} |")
            lines.append("")

    # Tier distribution
    if gap.tier_distribution:
        lines.append("### 7-7. Phase 1 Tier Distribution\n")
        lines.append("| Tier | Count | % |")
        lines.append("|------|-------|---|")
        total = sum(gap.tier_distribution.values())
        for tier in sorted(gap.tier_distribution.keys()):
            count = gap.tier_distribution[tier]
            lines.append(f"| {tier} | {count} | {count/total:.1%} |" if total > 0 else f"| {tier} | {count} | 0% |")
        lines.append("")

    # Auto insights
    lines.append("### 7-8. Auto-generated Insights\n")
    for i, insight in enumerate(gap.insights, 1):
        lines.append(f"{i}. {insight}")
    lines.append("")

    return lines
