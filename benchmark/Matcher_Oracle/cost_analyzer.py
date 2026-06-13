"""Cost analysis for Matcher-Oracle benchmark.

Estimates LLM API costs and computes cost-efficiency metrics
for each evaluation mode and comparison LLM model.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from oracle_metrics import OracleEvaluation
from comparison_data import LLM_MATCHER_ORACLE, estimate_cost_per_1k_calls


@dataclass
class ModeCost:
    """Cost breakdown for a single evaluation mode."""

    mode: str
    total_candidates: int
    uncertain_candidates: int
    llm_calls: int
    llm_call_ratio: float
    # Cost estimates per LLM model (if this mode used that model)
    cost_per_model: dict[str, float] = field(default_factory=dict)
    # Pure LLM baseline (all candidates to LLM)
    pure_llm_calls: int = 0
    pure_llm_cost: dict[str, float] = field(default_factory=dict)
    # Savings
    cost_saved_per_model: dict[str, float] = field(default_factory=dict)
    cost_saved_pct: float = 0.0


def analyze_costs(
    evaluations: dict[str, OracleEvaluation],
    total_candidates: int,
) -> dict[str, ModeCost]:
    """Analyze costs for all evaluation modes.

    Args:
        evaluations: {"LLM": ev, "Det": ev, "None": ev}
        total_candidates: Total Phase 1 candidate count.

    Returns:
        {"LLM": ModeCost, "Det": ModeCost, "None": ModeCost}
    """
    results: dict[str, ModeCost] = {}

    for mode, ev in evaluations.items():
        uncertain = ev.total_uncertain
        llm_calls = ev.llm_calls

        # Cost per model: what would it cost if this mode used model X?
        cost_per_model: dict[str, float] = {}
        for model_name, model_info in LLM_MATCHER_ORACLE.items():
            pricing = model_info.get("pricing", {})
            per_1k = estimate_cost_per_1k_calls(pricing)
            cost_per_model[model_name] = llm_calls / 1000 * per_1k

        # Pure LLM baseline: ALL candidates go to LLM
        pure_llm_calls = total_candidates
        pure_llm_cost: dict[str, float] = {}
        for model_name, model_info in LLM_MATCHER_ORACLE.items():
            pricing = model_info.get("pricing", {})
            per_1k = estimate_cost_per_1k_calls(pricing)
            pure_llm_cost[model_name] = pure_llm_calls / 1000 * per_1k

        # Savings: per model and average
        cost_saved: dict[str, float] = {}
        for model_name in LLM_MATCHER_ORACLE:
            saved = pure_llm_cost.get(model_name, 0) - cost_per_model.get(model_name, 0)
            cost_saved[model_name] = saved

        # Overall saved %
        avg_pure = sum(pure_llm_cost.values()) / len(pure_llm_cost) if pure_llm_cost else 0
        avg_actual = sum(cost_per_model.values()) / len(cost_per_model) if cost_per_model else 0
        saved_pct = (1 - avg_actual / avg_pure) if avg_pure > 0 else 0.0

        call_ratio = llm_calls / total_candidates if total_candidates > 0 else 0.0

        results[mode] = ModeCost(
            mode=mode,
            total_candidates=total_candidates,
            uncertain_candidates=uncertain,
            llm_calls=llm_calls,
            llm_call_ratio=call_ratio,
            cost_per_model=cost_per_model,
            pure_llm_calls=pure_llm_calls,
            pure_llm_cost=pure_llm_cost,
            cost_saved_per_model=cost_saved,
            cost_saved_pct=saved_pct,
        )

    return results


def get_cost_summary_table(costs: dict[str, ModeCost]) -> list[str]:
    """Generate markdown table for cost analysis section."""
    lines: list[str] = []

    lines.append("| Mode | Candidates | Uncertain | LLM Calls | Call Ratio | Cost Saved % |")
    lines.append("|------|-----------|-----------|-----------|------------|--------------|")

    for mode in ["LLM", "Det", "None"]:
        if mode not in costs:
            continue
        c = costs[mode]
        lines.append(
            f"| {mode} | {c.total_candidates} | {c.uncertain_candidates} | "
            f"{c.llm_calls} | {c.llm_call_ratio:.1%} | {c.cost_saved_pct:.1%} |"
        )
    lines.append("")

    # Per-model cost for Mode A (LLM Oracle)
    if "LLM" in costs:
        c = costs["LLM"]
        lines.append("\n### Per-Model Cost Estimation (Mode A: LLM Oracle)\n")
        lines.append("| Model | Oracle Calls | Est. Cost | Pure LLM Cost | Savings |")
        lines.append("|-------|-------------|-----------|---------------|---------|")
        for model_name in sorted(LLM_MATCHER_ORACLE.keys()):
            actual = c.cost_per_model.get(model_name, 0)
            pure = c.pure_llm_cost.get(model_name, 0)
            saved = c.cost_saved_per_model.get(model_name, 0)
            lines.append(
                f"| {model_name} | {c.llm_calls} | "
                f"${actual:.2f} | ${pure:.2f} | ${saved:.2f} |"
            )
        lines.append("")

    return lines
