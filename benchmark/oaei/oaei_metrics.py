"""OAEI-standard evaluation metrics: Precision, Recall, F1-measure.

Follows the OAEI evaluation protocol:
- Micro-averaged Precision/Recall across all test cases (absolute TP/FP/FN)
- F1-measure = harmonic mean of Precision and Recall
- Confidence-thresholded evaluation (matches above threshold counted)

Reference: https://oaei.ontologymatching.org/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class Alignment:
    """A single correspondence between source and target concepts."""

    source: str
    target: str
    confidence: float = 1.0

    def key(self) -> tuple[str, str]:
        return (self.source, self.target)


@dataclass
class EvaluationResult:
    """OAEI evaluation result for a single test case."""

    case_name: str
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
            f"{self.case_name}: P={self.precision:.4f} "
            f"R={self.recall:.4f} F1={self.f1:.4f} "
            f"(TP={self.tp} FP={self.fp} FN={self.fn})"
        )


@dataclass
class AggregateResult:
    """Micro-averaged results across all test cases (OAEI standard)."""

    results: list[EvaluationResult] = field(default_factory=list)

    @property
    def tp(self) -> int:
        return sum(r.tp for r in self.results)

    @property
    def fp(self) -> int:
        return sum(r.fp for r in self.results)

    @property
    def fn(self) -> int:
        return sum(r.fn for r in self.results)

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
            f"Micro-avg: P={self.precision:.4f} "
            f"R={self.recall:.4f} F1={self.f1:.4f} "
            f"(TP={self.tp} FP={self.fp} FN={self.fn})"
        )


def evaluate(
    case_name: str,
    system_alignments: Iterable[Alignment],
    reference_alignments: Iterable[Alignment],
    threshold: float = 0.0,
) -> EvaluationResult:
    """Evaluate system alignments against reference (gold standard).

    Args:
        case_name: Name of the test case.
        system_alignments: Alignments produced by the system.
        reference_alignments: Gold-standard reference alignments.
        threshold: Minimum confidence to count a system match.

    Returns:
        EvaluationResult with TP/FP/FN counts.
    """
    ref_set: set[tuple[str, str]] = {
        a.key() for a in reference_alignments
    }

    sys_pairs: set[tuple[str, str]] = set()
    for a in system_alignments:
        if a.confidence >= threshold:
            sys_pairs.add(a.key())

    tp = len(sys_pairs & ref_set)
    fp = len(sys_pairs - ref_set)
    fn = len(ref_set - sys_pairs)

    return EvaluationResult(case_name=case_name, tp=tp, fp=fp, fn=fn)


def evaluate_batch(
    system_per_case: dict[str, list[Alignment]],
    reference_per_case: dict[str, list[Alignment]],
    threshold: float = 0.0,
) -> AggregateResult:
    """Evaluate multiple test cases and return micro-averaged result.

    Args:
        system_per_case: {case_name: [Alignment, ...]} from system.
        reference_per_case: {case_name: [Alignment, ...]} gold standard.
        threshold: Minimum confidence for system matches.

    Returns:
        AggregateResult with per-case and overall metrics.
    """
    agg = AggregateResult()
    for case_name, ref_aligns in reference_per_case.items():
        sys_aligns = system_per_case.get(case_name, [])
        result = evaluate(case_name, sys_aligns, ref_aligns, threshold)
        agg.results.append(result)
    return agg
