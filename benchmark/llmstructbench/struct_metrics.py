"""LLMStructBench standard metrics: F1_micro, DOC_micro, Composite Score.

Implements the evaluation methodology from:
  LLMStructBench (arXiv 2602.14743, Tenckhoff et al.)

Key formulas:
  F1_micro  = α · F1_keys + (1-α) · F1_values       (α = 0.25)
  DOC_micro = (#Correct / #Total) × (1 - #Failed / #Total)
  Composite = (1-λ) · F1_micro + λ · DOC_micro        (λ = 0.5)

Fuzzy credit C(l) for string deviations:
  C(l) = 1.0                 if l ≤ L_good (0.1)
  C(l) = γ · max(0, 1-l)     if L_good < l < L_bad
  C(l) = p_bad (-1)          if l ≥ L_bad (2.0)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

# ════════════════════════════════════════════════════════════
# Parameters (paper defaults)
# ════════════════════════════════════════════════════════════

ALPHA = 0.25       # key weight (value correctness weighted higher)
LAMBDA = 0.5       # DOC/F1 balance
BETA = 0.2         # coercible gain (partial credit for type-coercible)
GAMMA = 0.5        # fuzzy weight for approximate string matches
L_GOOD = 0.1       # Levenshtein threshold for full credit
L_BAD = 2.0        # Levenshtein threshold for penalty
P_BAD = -1.0       # penalty for hopelessly wrong strings


# ════════════════════════════════════════════════════════════
# Data structures
# ════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CellPair:
    """A single key-value pair extracted from a spreadsheet cell."""

    key: str            # e.g. "재료비_값::단가::R0001"
    value: Any          # cell value (str, int, float, None)
    field_name: str = ""  # leaf column name for tolerance lookup


@dataclass
class F1Result:
    """F1_micro breakdown for a single sheet/section."""

    f1_keys: float
    f1_values: float
    f1_micro: float
    tp_keys: int
    fp_keys: int
    fn_keys: int
    tp_values: float       # can be fractional due to fuzzy credit
    fn_values: int         # MV count
    error_count: int       # total WV count
    detail: dict = field(default_factory=dict)


@dataclass
class SheetResult:
    """Evaluation result for a single sheet."""

    sheet_name: str
    f1_result: F1Result
    is_correct: bool       # all cells match → DOC numerator
    is_failed: bool        # parse failure / empty → DOC penalty
    total_cells: int
    matched_cells: int


@dataclass
class BatchResult:
    """Aggregated results across multiple sheets/cases."""

    sheet_results: list[SheetResult] = field(default_factory=list)

    @property
    def f1_micro(self) -> float:
        """Micro-averaged F1 across all sheets."""
        total_tp_v = sum(r.f1_result.tp_values for r in self.sheet_results)
        total_fn_v = sum(r.f1_result.fn_values for r in self.sheet_results)
        total_err = sum(r.f1_result.error_count for r in self.sheet_results)
        total_tp_k = sum(r.f1_result.tp_keys for r in self.sheet_results)
        total_fp_k = sum(r.f1_result.fp_keys for r in self.sheet_results)
        total_fn_k = sum(r.f1_result.fn_keys for r in self.sheet_results)

        return _compute_f1_micro(
            total_tp_k, total_fp_k, total_fn_k,
            total_tp_v, total_fn_v, total_err,
        )

    @property
    def doc_micro(self) -> float:
        """DOC_micro = (#Correct / #Total) × (1 - #Failed / #Total)."""
        total = len(self.sheet_results)
        if total == 0:
            return 0.0
        correct = sum(1 for r in self.sheet_results if r.is_correct)
        failed = sum(1 for r in self.sheet_results if r.is_failed)
        return (correct / total) * (1 - failed / total)

    @property
    def composite(self) -> float:
        """Composite = (1-λ)·F1 + λ·DOC."""
        return (1 - LAMBDA) * self.f1_micro + LAMBDA * self.doc_micro


# ════════════════════════════════════════════════════════════
# Core computations
# ════════════════════════════════════════════════════════════

def _compute_f1_micro(
    tp_k: int, fp_k: int, fn_k: int,
    tp_v: float, fn_v: int, err_v: int,
) -> float:
    """Compute F1_micro from counts.

    F1_micro = α · F1_keys + (1-α) · F1_values
    """
    # F1_keys
    p_k = tp_k / (tp_k + fp_k) if (tp_k + fp_k) > 0 else 0.0
    r_k = tp_k / (tp_k + fn_k) if (tp_k + fn_k) > 0 else 0.0
    f1_k = 2 * p_k * r_k / (p_k + r_k) if (p_k + r_k) > 0 else 0.0

    # F1_values
    predicted_v = tp_v + err_v
    gold_v = tp_v + fn_v
    p_v = tp_v / predicted_v if predicted_v > 0 else 0.0
    r_v = tp_v / gold_v if gold_v > 0 else 0.0
    f1_v = 2 * p_v * r_v / (p_v + r_v) if (p_v + r_v) > 0 else 0.0

    return ALPHA * f1_k + (1 - ALPHA) * f1_v


def levenshtein_norm(s1: str, s2: str) -> float:
    """Normalized Levenshtein distance (0.0 = identical, higher = more different).

    Uses SequenceMatcher ratio as an efficient approximation.
    """
    if not s1 and not s2:
        return 0.0
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 0.0
    # SequenceMatcher gives ratio in [0, 1]; distance = 1 - ratio
    ratio = SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
    return 1.0 - ratio


def fuzzy_credit(l_norm: float) -> float:
    """Fuzzy credit function C(l).

    C(l) = 1.0             if l ≤ L_good (0.1)
    C(l) = γ·max(0, 1-l)  if L_good < l < L_bad
    C(l) = p_bad (-1)      if l ≥ L_bad (2.0)
    """
    if l_norm <= L_GOOD:
        return 1.0
    if l_norm >= L_BAD:
        return P_BAD
    return GAMMA * max(0.0, 1.0 - l_norm)


def compute_composite(f1_micro: float, doc_micro: float) -> float:
    """Composite = (1-λ)·F1 + λ·DOC."""
    return (1 - LAMBDA) * f1_micro + LAMBDA * doc_micro
