"""Oracle evaluation metrics for Matcher-Oracle benchmark.

Extends OAEI-standard P/R/F1 with:
  - Oracle diagnostic: Sensitivity, Specificity, Youden's Index
  - 2x2 Oracle confusion matrix (TP_confirmed, FN_oracle, FP_confirmed, TN_rejected)
  - Simulated Oracle calibration (Or_0~Or_30, Lushnei et al. EACL 2026)

Reference:
  - OAEI: https://oaei.ontologymatching.org/
  - Lushnei et al., "LLMs as Oracles for OA", EACL 2026
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable

from comparison_data import SIMULATED_ORACLE, grade_youden


# ════════════════════════════════════════════════════════════
# Core data structures
# ════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Alignment:
    """A single correspondence between source and target."""

    source: str
    target: str
    confidence: float = 1.0
    tier: str = ""

    def key(self) -> tuple[str, str]:
        return (self.source, self.target)


@dataclass
class PhaseResult:
    """Evaluation result for a single phase (Phase 1 or Phase 2)."""

    label: str
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        predicted = self.tp + self.fp
        return self.tp / predicted if predicted > 0 else 0.0

    @property
    def recall(self) -> float:
        gold = self.tp + self.fn
        return self.tp / gold if gold > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    def __str__(self) -> str:
        return (
            f"{self.label}: P={self.precision:.4f} "
            f"R={self.recall:.4f} F1={self.f1:.4f} "
            f"(TP={self.tp} FP={self.fp} FN={self.fn})"
        )


@dataclass
class OracleEvaluation:
    """Full evaluation: Phase 1 baseline + Phase 2 oracle-verified result.

    Oracle diagnostic uses a 2x2 confusion matrix:
                        Oracle=Confirm   Oracle=Reject
    True Match:         tp_confirmed      fn_oracle
    False Match:        fp_confirmed      tn_rejected
    """

    mode: str = ""
    # Phase 1 (algorithm only)
    phase1: PhaseResult = field(default_factory=lambda: PhaseResult(label="Phase1"))
    # Phase 2 (post-oracle)
    phase2: PhaseResult = field(default_factory=lambda: PhaseResult(label="Phase2"))
    # Oracle confusion matrix
    tp_confirmed: int = 0
    fn_oracle: int = 0
    fp_confirmed: int = 0
    tn_rejected: int = 0
    # Oracle decisions on uncertain set
    oracle_confirm: int = 0
    oracle_reject: int = 0
    total_uncertain: int = 0
    llm_calls: int = 0

    # ── Derived properties ──

    @property
    def oracle_precision(self) -> float:
        return self.phase2.precision

    @property
    def oracle_recall(self) -> float:
        return self.phase2.recall

    @property
    def oracle_f1(self) -> float:
        return self.phase2.f1

    @property
    def phase1_f1(self) -> float:
        return self.phase1.f1

    @property
    def oracle_delta(self) -> float:
        """Oracle value-add: F1 improvement from Phase 1 to Phase 2."""
        return self.oracle_f1 - self.phase1_f1

    @property
    def sensitivity(self) -> float:
        """Se = TP_confirmed / (TP_confirmed + FN_oracle).
        How well the oracle confirms true matches."""
        denom = self.tp_confirmed + self.fn_oracle
        return self.tp_confirmed / denom if denom > 0 else 1.0

    @property
    def specificity(self) -> float:
        """Sp = TN_rejected / (TN_rejected + FP_confirmed).
        How well the oracle rejects false matches."""
        denom = self.tn_rejected + self.fp_confirmed
        return self.tn_rejected / denom if denom > 0 else 1.0

    @property
    def youden_index(self) -> float:
        """YI = Se + Sp - 1. Range: [0, 1]. 1.0=perfect, 0=random."""
        return self.sensitivity + self.specificity - 1.0

    @property
    def oracle_error_rate(self) -> float:
        """Fraction of wrong oracle decisions among all oracle decisions."""
        total = self.oracle_confirm + self.oracle_reject
        wrong = self.fn_oracle + self.fp_confirmed
        return wrong / total if total > 0 else 0.0

    @property
    def grade(self) -> tuple[str, str]:
        """Youden's Index grade (S/A+/A/B/C/D)."""
        return grade_youden(self.youden_index)

    @property
    def simulated_oracle_equivalent(self) -> str:
        """Which Or_N the engine's oracle error rate matches."""
        er = self.oracle_error_rate
        best_match = "Or_30+"
        best_diff = float("inf")
        for name, info in SIMULATED_ORACLE.items():
            diff = abs(er - info["error_rate"])
            if diff < best_diff:
                best_diff = diff
                best_match = name
        return best_match

    def __str__(self) -> str:
        grade, _ = self.grade
        return (
            f"[{self.mode}] Phase1 F1={self.phase1_f1:.4f} → "
            f"Oracle F1={self.oracle_f1:.4f} (Δ={self.oracle_delta:+.4f}) | "
            f"Se={self.sensitivity:.4f} Sp={self.specificity:.4f} "
            f"YI={self.youden_index:.4f} [{grade}] | "
            f"LLM calls={self.llm_calls} | "
            f"Oracle ≈ {self.simulated_oracle_equivalent}"
        )


# ════════════════════════════════════════════════════════════
# Evaluation functions
# ════════════════════════════════════════════════════════════

def evaluate_phase(
    label: str,
    system_alignments: Iterable[Alignment],
    reference_alignments: Iterable[Alignment],
) -> PhaseResult:
    """Evaluate a set of alignments against reference (P/R/F1)."""
    ref_set: set[tuple[str, str]] = {a.key() for a in reference_alignments}
    sys_pairs: set[tuple[str, str]] = {a.key() for a in system_alignments}

    tp = len(sys_pairs & ref_set)
    fp = len(sys_pairs - ref_set)
    fn = len(ref_set - sys_pairs)

    return PhaseResult(label=label, tp=tp, fp=fp, fn=fn)


def evaluate_oracle(
    mode: str,
    phase1_alignments: list[Alignment],
    phase2_alignments: list[Alignment],
    reference_alignments: list[Alignment],
    uncertain_set: list[Alignment] | None = None,
    oracle_decisions: dict[tuple[str, str], bool] | None = None,
    llm_calls: int = 0,
) -> OracleEvaluation:
    """Full 2-phase evaluation with oracle diagnostic.

    Args:
        mode: "LLM" | "Det" | "None"
        phase1_alignments: Phase 1 (algorithm) output.
        phase2_alignments: Phase 2 (post-oracle) output.
        reference_alignments: Gold-standard alignments.
        uncertain_set: Candidates that were sent to oracle (M_ask).
        oracle_decisions: {alignment.key(): True(confirm)/False(reject)}.
        llm_calls: Number of LLM API calls made.

    Returns:
        OracleEvaluation with both phase metrics + oracle diagnostic.
    """
    ref_set: set[tuple[str, str]] = {a.key() for a in reference_alignments}
    phase1_set: set[tuple[str, str]] = {a.key() for a in phase1_alignments}
    phase2_set: set[tuple[str, str]] = {a.key() for a in phase2_alignments}

    phase1 = evaluate_phase("Phase1", phase1_alignments, reference_alignments)

    if mode == "None":
        ev = OracleEvaluation(
            mode=mode, phase1=phase1,
            phase2=evaluate_phase("Phase2", phase2_alignments, reference_alignments),
            llm_calls=0,
        )
        return ev

    phase2 = evaluate_phase("Phase2", phase2_alignments, reference_alignments)

    # ── Oracle confusion matrix ──
    # Only the uncertain set was evaluated by the oracle
    if uncertain_set is None:
        uncertain_set = list(phase1_alignments)

    # For non-uncertain alignments, they pass through as "confirmed"
    non_uncertain_keys = phase1_set - {a.key() for a in uncertain_set}

    tp_confirmed = 0
    fn_oracle = 0
    fp_confirmed = 0
    tn_rejected = 0
    oracle_confirm_count = 0
    oracle_reject_count = 0

    # Process uncertain set through oracle decisions
    for align in uncertain_set:
        key = align.key()
        is_true_match = key in ref_set
        oracle_says = True  # default: pass through

        if oracle_decisions and key in oracle_decisions:
            oracle_says = oracle_decisions[key]

        if oracle_says:
            oracle_confirm_count += 1
            if is_true_match:
                tp_confirmed += 1
            else:
                fp_confirmed += 1
        else:
            oracle_reject_count += 1
            if is_true_match:
                fn_oracle += 1
            else:
                tn_rejected += 1

    return OracleEvaluation(
        mode=mode,
        phase1=phase1,
        phase2=phase2,
        tp_confirmed=tp_confirmed,
        fn_oracle=fn_oracle,
        fp_confirmed=fp_confirmed,
        tn_rejected=tn_rejected,
        oracle_confirm=oracle_confirm_count,
        oracle_reject=oracle_reject_count,
        total_uncertain=len(uncertain_set),
        llm_calls=llm_calls,
    )


# ════════════════════════════════════════════════════════════
# Simulated Oracle (Or_0~Or_30)
# ════════════════════════════════════════════════════════════

def simulate_oracle(
    phase1_alignments: list[Alignment],
    reference_alignments: list[Alignment],
    error_rate: float,
    uncertain_set: list[Alignment] | None = None,
    rng: random.Random | None = None,
) -> OracleEvaluation:
    """Simulate an oracle with a given error rate.

    For each candidate in uncertain_set:
      - With probability (1-error_rate): oracle makes correct decision
      - With probability error_rate: oracle makes wrong decision

    Args:
        phase1_alignments: Phase 1 algorithm output.
        reference_alignments: Gold standard.
        error_rate: Oracle error probability (0.0~0.3).
        uncertain_set: Candidates sent to oracle (default: all Phase 1).
        rng: Optional Random instance for reproducibility.

    Returns:
        OracleEvaluation with simulated oracle decisions.
    """
    if rng is None:
        rng = random.Random(42)

    ref_set: set[tuple[str, str]] = {a.key() for a in reference_alignments}

    if uncertain_set is None:
        uncertain_set = list(phase1_alignments)

    uncertain_keys = {a.key() for a in uncertain_set}
    non_uncertain = [a for a in phase1_alignments if a.key() not in uncertain_keys]

    oracle_decisions: dict[tuple[str, str], bool] = {}
    llm_calls = 0

    for align in uncertain_set:
        key = align.key()
        is_true = key in ref_set
        llm_calls += 1

        if rng.random() < error_rate:
            # Wrong decision
            oracle_decisions[key] = not is_true
        else:
            # Correct decision
            oracle_decisions[key] = is_true

    # Build Phase 2 output: non-uncertain pass through + oracle-confirmed
    phase2_alignments = list(non_uncertain)
    for align in uncertain_set:
        if oracle_decisions.get(align.key(), True):
            phase2_alignments.append(align)

    return evaluate_oracle(
        mode="Simulated",
        phase1_alignments=phase1_alignments,
        phase2_alignments=phase2_alignments,
        reference_alignments=reference_alignments,
        uncertain_set=uncertain_set,
        oracle_decisions=oracle_decisions,
        llm_calls=llm_calls,
    )


def run_simulated_oracle_calibration(
    phase1_alignments: list[Alignment],
    reference_alignments: list[Alignment],
    uncertain_set: list[Alignment] | None = None,
    seed: int = 42,
) -> dict[str, OracleEvaluation]:
    """Run Or_0~Or_30 simulated oracle calibration.

    Returns:
        {"Or_0": OracleEvaluation, "Or_5": ..., "Or_30": ...}
    """
    results: dict[str, OracleEvaluation] = {}
    for name, info in SIMULATED_ORACLE.items():
        rng = random.Random(seed)
        results[name] = simulate_oracle(
            phase1_alignments=phase1_alignments,
            reference_alignments=reference_alignments,
            error_rate=info["error_rate"],
            uncertain_set=uncertain_set,
            rng=rng,
        )
    return results
