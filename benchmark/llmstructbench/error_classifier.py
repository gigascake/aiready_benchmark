"""Error classifier: MK/MV/WV classification with fuzzy credit.

Classifies each key-value pair into:
  - MK (Missing Key): key present in GT but absent in system output
  - MV (Missing Value): key present but value is null/empty
  - WV (Wrong Value): value differs, sub-classified into:
    - deviation: string deviation (Levenshtein-based partial credit)
    - error: same type, different content (zero credit)
    - coerce: type-coercible mismatch (partial credit β=0.2)
    - type: type mismatch, not coercible (zero credit)

Domain-specific numeric tolerances are applied before classification:
  values within tolerance → full credit (C=1.0)
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from struct_metrics import (
    BETA, GAMMA, L_GOOD, L_BAD, P_BAD,
    CellPair, F1Result, fuzzy_credit, levenshtein_norm,
    _compute_f1_micro,
)


# ════════════════════════════════════════════════════════════
# Domain-specific numeric tolerances
# ════════════════════════════════════════════════════════════

FIELD_TOLERANCES: dict[str, float] = {
    "단가": 0.01,
    "소요량": 0.001,
    "사용량": 0.001,
    "C/T": 0.01,
    "C/Time": 0.01,
    "CYCLE TIME": 0.01,
    "NET C/T": 0.01,
    "임율": 0.01,
    "금액": 1.0,
    "계": 1.0,
    "재료비": 1.0,
    "노무비": 1.0,
    "경비": 1.0,
    "가공비": 1.0,
    "제조원가": 1.0,
}

DEFAULT_TOLERANCE = 0.0  # exact match by default


class WVSubtype(Enum):
    """Wrong Value subtypes."""
    NONE = "none"                  # no error (match)
    DEVIATION = "deviation"        # string deviation (fuzzy credit)
    VALUE_ERROR = "value_error"    # same type, different content
    COERCIBLE = "coercible"        # type-coercible ("42" vs 42)
    TYPE_ERROR = "type_error"      # type mismatch, not coercible


@dataclass
class ValueComparison:
    """Result of comparing a single GT value vs system value."""
    subtype: WVSubtype
    credit: float          # fuzzy credit in [P_BAD, 1.0]
    gt_value: Any
    sys_value: Any


@dataclass
class ErrorAnalysis:
    """Full error analysis for a set of pairs."""

    tp_keys: int
    fp_keys: int
    fn_keys: int           # MK count
    missing_values: int    # MV count
    wv_by_subtype: Counter = field(default_factory=Counter)
    wv_credits: list[float] = field(default_factory=list)
    tp_values: float = 0.0
    total_compared: int = 0
    fuzzy_credits_sum: float = 0.0
    sample_errors: list[str] = field(default_factory=list)

    @property
    def wv_total(self) -> int:
        return sum(self.wv_by_subtype.values())

    @property
    def error_count(self) -> int:
        """Total WV count (excluding MV)."""
        return self.wv_total


# ════════════════════════════════════════════════════════════
# Value comparison logic
# ════════════════════════════════════════════════════════════

def _is_null(val: Any) -> bool:
    """Check if a value is null/empty."""
    if val is None:
        return True
    s = str(val).strip()
    return s == "" or s.lower() in ("none", "nan", "null", "-")


def _to_float(val: Any) -> float | None:
    """Try to parse value as float."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if isinstance(val, float) and math.isnan(val):
            return None
        return float(val)
    try:
        return float(str(val).strip().replace(",", ""))
    except (ValueError, TypeError):
        return None


def _get_tolerance(field_name: str) -> float:
    """Look up numeric tolerance for a field."""
    return FIELD_TOLERANCES.get(field_name, DEFAULT_TOLERANCE)


def compare_values(
    gt_val: Any,
    sys_val: Any,
    field_name: str = "",
) -> ValueComparison:
    """Compare a GT value with system value, return subtype + credit.

    Classification order:
    1. Both null → match (NONE)
    2. Numeric comparison with tolerance → match or value_error
    3. Type-coercible (string "42" vs int 42) → coercible (β=0.2)
    4. Both strings → deviation (fuzzy credit) or value_error
    5. Type mismatch → type_error
    """
    gt_null = _is_null(gt_val)
    sys_null = _is_null(sys_val)

    if gt_null and sys_null:
        return ValueComparison(WVSubtype.NONE, 1.0, gt_val, sys_val)

    if gt_null or sys_null:
        return ValueComparison(WVSubtype.VALUE_ERROR, 0.0, gt_val, sys_val)

    gt_float = _to_float(gt_val)
    sys_float = _to_float(sys_val)

    if gt_float is not None and sys_float is not None:
        tol = _get_tolerance(field_name)
        diff = abs(gt_float - sys_float)
        if diff <= tol:
            return ValueComparison(WVSubtype.NONE, 1.0, gt_val, sys_val)
        return ValueComparison(WVSubtype.VALUE_ERROR, 0.0, gt_val, sys_val)

    gt_str = str(gt_val).strip()
    sys_str = str(sys_val).strip()

    if gt_float is not None and sys_float is None:
        if _is_coercible(gt_str, sys_str):
            return ValueComparison(WVSubtype.COERCIBLE, BETA, gt_val, sys_val)
        l_norm = levenshtein_norm(gt_str, sys_str)
        if l_norm <= L_GOOD:
            return ValueComparison(WVSubtype.NONE, 1.0, gt_val, sys_val)
        if l_norm < L_BAD:
            return ValueComparison(WVSubtype.DEVIATION, fuzzy_credit(l_norm), gt_val, sys_val)
        return ValueComparison(WVSubtype.TYPE_ERROR, 0.0, gt_val, sys_val)

    if gt_float is None and sys_float is not None:
        if _is_coercible(sys_str, gt_str):
            return ValueComparison(WVSubtype.COERCIBLE, BETA, gt_val, sys_val)
        l_norm = levenshtein_norm(gt_str, sys_str)
        if l_norm <= L_GOOD:
            return ValueComparison(WVSubtype.NONE, 1.0, gt_val, sys_val)
        if l_norm < L_BAD:
            return ValueComparison(WVSubtype.DEVIATION, fuzzy_credit(l_norm), gt_val, sys_val)
        return ValueComparison(WVSubtype.TYPE_ERROR, 0.0, gt_val, sys_val)

    if gt_str == sys_str:
        return ValueComparison(WVSubtype.NONE, 1.0, gt_val, sys_val)

    l_norm = levenshtein_norm(gt_str, sys_str)
    if l_norm <= L_GOOD:
        return ValueComparison(WVSubtype.NONE, 1.0, gt_val, sys_val)
    if l_norm < L_BAD:
        return ValueComparison(WVSubtype.DEVIATION, fuzzy_credit(l_norm), gt_val, sys_val)
    return ValueComparison(WVSubtype.VALUE_ERROR, 0.0, gt_val, sys_val)


def _is_coercible(s1: str, s2: str) -> bool:
    """Check if two values are type-coercible (e.g., '42' vs 42)."""
    f1 = _to_float(s1)
    f2 = _to_float(s2)
    if f1 is not None and f2 is not None:
        return abs(f1 - f2) < 0.001
    return False


# ════════════════════════════════════════════════════════════
# Pair classification
# ════════════════════════════════════════════════════════════

def classify_pairs(
    gt_pairs: list[CellPair],
    sys_pairs: list[CellPair],
) -> ErrorAnalysis:
    """Classify all pairs into MK/MV/WV and compute credits.

    Args:
        gt_pairs: Ground-truth cell pairs.
        sys_pairs: System output cell pairs.

    Returns:
        ErrorAnalysis with all counts and credits.
    """
    gt_map: dict[str, CellPair] = {p.key: p for p in gt_pairs}
    sys_map: dict[str, CellPair] = {p.key: p for p in sys_pairs}

    gt_keys = set(gt_map.keys())
    sys_keys = set(sys_map.keys())

    tp_k = len(gt_keys & sys_keys)
    fp_k = len(sys_keys - gt_keys)
    fn_k = len(gt_keys - sys_keys)

    common_keys = gt_keys & sys_keys
    mv_count = 0
    wv_by_subtype: Counter = Counter()
    wv_credits: list[float] = []
    tp_v = 0.0
    fuzzy_sum = 0.0
    total_compared = 0
    sample_errors: list[str] = []

    for key in sorted(common_keys):
        gt_pair = gt_map[key]
        sys_pair = sys_map[key]
        total_compared += 1

        if _is_null(gt_pair.value) and _is_null(sys_pair.value):
            tp_v += 1.0
            continue

        if _is_null(sys_pair.value) and not _is_null(gt_pair.value):
            mv_count += 1
            continue

        comp = compare_values(gt_pair.value, sys_pair.value, gt_pair.field_name)

        if comp.subtype == WVSubtype.NONE:
            tp_v += comp.credit
        elif comp.subtype == WVSubtype.COERCIBLE:
            tp_v += comp.credit
            wv_by_subtype[WVSubtype.COERCIBLE] += 1
            wv_credits.append(comp.credit)
            fuzzy_sum += comp.credit
            if len(sample_errors) < 20:
                sample_errors.append(
                    f"  COERCIBLE `{key}`: GT=`{gt_pair.value}` SYS=`{sys_pair.value}` credit={comp.credit:.2f}"
                )
        elif comp.subtype == WVSubtype.DEVIATION:
            wv_by_subtype[WVSubtype.DEVIATION] += 1
            wv_credits.append(comp.credit)
            fuzzy_sum += comp.credit
            tp_v += max(0.0, comp.credit)
            if len(sample_errors) < 20:
                sample_errors.append(
                    f"  DEVIATION `{key}`: GT=`{gt_pair.value}` SYS=`{sys_pair.value}` credit={comp.credit:.2f}"
                )
        elif comp.subtype == WVSubtype.VALUE_ERROR:
            wv_by_subtype[WVSubtype.VALUE_ERROR] += 1
            wv_credits.append(comp.credit)
            if len(sample_errors) < 20:
                sample_errors.append(
                    f"  VALUE_ERROR `{key}`: GT=`{gt_pair.value}` SYS=`{sys_pair.value}`"
                )
        elif comp.subtype == WVSubtype.TYPE_ERROR:
            wv_by_subtype[WVSubtype.TYPE_ERROR] += 1
            wv_credits.append(comp.credit)
            if len(sample_errors) < 20:
                sample_errors.append(
                    f"  TYPE_ERROR `{key}`: GT=`{gt_pair.value}` ({type(gt_pair.value).__name__}) "
                    f"SYS=`{sys_pair.value}` ({type(sys_pair.value).__name__})"
                )

    return ErrorAnalysis(
        tp_keys=tp_k,
        fp_keys=fp_k,
        fn_keys=fn_k,
        missing_values=mv_count,
        wv_by_subtype=wv_by_subtype,
        wv_credits=wv_credits,
        tp_values=tp_v,
        total_compared=total_compared,
        fuzzy_credits_sum=fuzzy_sum,
        sample_errors=sample_errors,
    )


def analysis_to_f1_result(analysis: ErrorAnalysis) -> F1Result:
    """Convert ErrorAnalysis counts to F1Result."""
    f1_micro = _compute_f1_micro(
        analysis.tp_keys, analysis.fp_keys, analysis.fn_keys,
        analysis.tp_values, analysis.missing_values, analysis.error_count,
    )

    p_k = analysis.tp_keys / (analysis.tp_keys + analysis.fp_keys) if (analysis.tp_keys + analysis.fp_keys) > 0 else 0.0
    r_k = analysis.tp_keys / (analysis.tp_keys + analysis.fn_keys) if (analysis.tp_keys + analysis.fn_keys) > 0 else 0.0
    f1_k = 2 * p_k * r_k / (p_k + r_k) if (p_k + r_k) > 0 else 0.0

    predicted_v = analysis.tp_values + analysis.error_count
    gold_v = analysis.tp_values + analysis.missing_values
    p_v = analysis.tp_values / predicted_v if predicted_v > 0 else 0.0
    r_v = analysis.tp_values / gold_v if gold_v > 0 else 0.0
    f1_v = 2 * p_v * r_v / (p_v + r_v) if (p_v + r_v) > 0 else 0.0

    return F1Result(
        f1_keys=f1_k,
        f1_values=f1_v,
        f1_micro=f1_micro,
        tp_keys=analysis.tp_keys,
        fp_keys=analysis.fp_keys,
        fn_keys=analysis.fn_keys,
        tp_values=analysis.tp_values,
        fn_values=analysis.missing_values,
        error_count=analysis.error_count,
    )
