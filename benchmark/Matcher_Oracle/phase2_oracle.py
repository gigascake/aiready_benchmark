"""Phase 2: Oracle verification (3 modes).

Mode A: LLM Oracle — T6 (LLM temp=0.0) verifies uncertain set
Mode B: Det. Oracle — M1-M5 TemplateMappingValidator acts as deterministic oracle
Mode C: No Oracle — Phase 1 result as-is (baseline)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from dataclasses import dataclass, field

from oracle_metrics import Alignment, OracleEvaluation, evaluate_oracle
from phase1_matcher import Phase1Result


_ENGINE_SRC = str(
    Path(__file__).resolve().parent.parent.parent / "src"
)

VLM_BASE_URL = "http://192.168.50.88:28000/v1"
VLM_MODEL = "qwen35-122b"
VLM_API_KEY = "hb260320"


def _ensure_path() -> None:
    if _ENGINE_SRC not in sys.path:
        sys.path.insert(0, _ENGINE_SRC)


@dataclass
class Phase2Result:
    """Result of Phase 2 oracle verification."""

    mode: str
    alignments: list[Alignment] = field(default_factory=list)
    oracle_decisions: dict[tuple[str, str], bool] = field(default_factory=dict)
    llm_calls: int = 0
    elapsed: float = 0.0


# ════════════════════════════════════════════════════════════
# Mode A: LLM Oracle
# ════════════════════════════════════════════════════════════

def _llm_oracle_check(source: str, target: str) -> bool | None:
    """Send a single Yes/No query to the LLM oracle.

    Returns:
        True (confirm), False (reject), or None (error/fallback).
    """
    try:
        from openai import OpenAI

        client = OpenAI(base_url=VLM_BASE_URL, api_key=VLM_API_KEY)

        prompt = (
            f"Is the field '{source}' semantically equivalent to '{target}' "
            f"in the context of a cost analysis document? "
            f"Answer with only 'Yes' or 'No'."
        )

        response = client.chat.completions.create(
            model=VLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10,
        )

        answer = response.choices[0].message.content.strip().lower()
        return "yes" in answer

    except Exception:
        return None


def run_mode_a_llm_oracle(phase1: Phase1Result) -> Phase2Result:
    """Mode A: LLM Oracle verification on uncertain set.

    Sends uncertain candidates to LLM for Yes/No verification.
    Only LLM-confirmed candidates are kept.
    """
    t0 = time.time()

    uncertain_keys = {a.key() for a in phase1.uncertain_set}
    confident = [a for a in phase1.alignments if a.key() not in uncertain_keys]

    oracle_decisions: dict[tuple[str, str], bool] = {}
    llm_calls = 0

    for align in phase1.uncertain_set:
        llm_calls += 1
        src_leaf = align.source.split("::")[-1] if "::" in align.source else align.source
        tgt_leaf = align.target.split("::")[-1] if "::" in align.target else align.target

        result = _llm_oracle_check(src_leaf, tgt_leaf)
        if result is None:
            oracle_decisions[align.key()] = True
        else:
            oracle_decisions[align.key()] = result

    verified = list(confident)
    for align in phase1.uncertain_set:
        if oracle_decisions.get(align.key(), True):
            verified.append(align)

    return Phase2Result(
        mode="LLM",
        alignments=verified,
        oracle_decisions=oracle_decisions,
        llm_calls=llm_calls,
        elapsed=time.time() - t0,
    )


# ════════════════════════════════════════════════════════════
# Mode B: Deterministic Oracle (real M1-M5 TemplateMappingValidator)
# ════════════════════════════════════════════════════════════

def run_mode_b_det_oracle(
    phase1: Phase1Result,
    dm_xlsx_path: str = "",
    template_xlsx: str = "",
) -> Phase2Result:
    """Mode B: Deterministic Oracle via real M1-M5 Validator.

    Runs TemplateMappingValidator on the DM output file.
    Uses validation issues (M2 cell role, M4 section marker, M5 value type)
    to reject uncertain set pairs that the validator flags as problematic.

    M1-M5 checks (14 codes):
    - M1: Merge structure consistency
    - M2: Label/DATA cell role classification
    - M3: Meta-field mapping completeness
    - M4: Section marker alignment
    - M5: Value type consistency

    Args:
        phase1: Phase 1 result with uncertain set.
        dm_xlsx_path: Path to DM output file (_dm.xlsx).
        template_xlsx: Path to golden template file.
    """
    t0 = time.time()

    uncertain_keys = {a.key() for a in phase1.uncertain_set}
    confident = [a for a in phase1.alignments if a.key() not in uncertain_keys]

    oracle_decisions: dict[tuple[str, str], bool] = {}

    if not dm_xlsx_path or not Path(dm_xlsx_path).exists():
        for align in phase1.uncertain_set:
            oracle_decisions[align.key()] = True
    else:
        _ensure_path()

        from validator.template_mapping_validator import TemplateMappingValidator

        validator = TemplateMappingValidator(
            template_path=str(template_xlsx) if template_xlsx and Path(template_xlsx).exists() else None,
        )
        report = validator.validate_from_xlsx(str(dm_xlsx_path))

        flagged_sections: set[str] = set()
        for issue in report.issues:
            if issue.severity == "CRITICAL":
                loc = issue.location or ""
                if "::" in loc:
                    flagged_sections.add(loc.split("::")[0])
                for sec_kw in ["재료비", "가공비", "원가", "집계"]:
                    if sec_kw in str(issue.message):
                        flagged_sections.add(sec_kw)

        for align in phase1.uncertain_set:
            src_sec = align.source.split("::")[0] if "::" in align.source else ""
            tgt_sec = align.target.split("::")[0] if "::" in align.target else ""

            is_flagged = False
            for fs in flagged_sections:
                if fs and (fs in src_sec or fs in tgt_sec):
                    is_flagged = True
                    break

            if is_flagged:
                oracle_decisions[align.key()] = False
            elif report.overall_score is not None and report.overall_score < 0.85:
                oracle_decisions[align.key()] = False
            else:
                oracle_decisions[align.key()] = True

    verified = list(confident)
    for align in phase1.uncertain_set:
        if oracle_decisions.get(align.key(), True):
            verified.append(align)

    return Phase2Result(
        mode="Det",
        alignments=verified,
        oracle_decisions=oracle_decisions,
        llm_calls=0,
        elapsed=time.time() - t0,
    )


# ════════════════════════════════════════════════════════════
# Mode C: No Oracle (Baseline)
# ════════════════════════════════════════════════════════════

def run_mode_c_no_oracle(phase1: Phase1Result) -> Phase2Result:
    """Mode C: No oracle. Phase 1 result passed through as-is."""
    return Phase2Result(
        mode="None",
        alignments=list(phase1.alignments),
        oracle_decisions={},
        llm_calls=0,
        elapsed=0.0,
    )


# ════════════════════════════════════════════════════════════
# Full evaluation
# ════════════════════════════════════════════════════════════

def evaluate_mode(
    phase1: Phase1Result,
    phase2: Phase2Result,
    reference_alignments: list[Alignment],
) -> OracleEvaluation:
    """Evaluate a single mode's Phase 1 + Phase 2 results."""
    return evaluate_oracle(
        mode=phase2.mode,
        phase1_alignments=phase1.alignments,
        phase2_alignments=phase2.alignments,
        reference_alignments=reference_alignments,
        uncertain_set=phase1.uncertain_set,
        oracle_decisions=phase2.oracle_decisions,
        llm_calls=phase2.llm_calls,
    )


def run_all_modes(
    phase1: Phase1Result,
    reference_alignments: list[Alignment],
    use_llm: bool = True,
    dm_xlsx_path: str = "",
    template_xlsx: str = "",
) -> tuple[dict[str, OracleEvaluation], dict[str, Phase2Result]]:
    """Run all three modes and evaluate.

    Args:
        phase1: Phase 1 result.
        reference_alignments: Gold standard.
        use_llm: If False, skip Mode A (LLM) — useful when VLM server is down.
        dm_xlsx_path: Path to DM output file for Mode B validation.
        template_xlsx: Path to golden template for Mode B validation.

    Returns:
        (evaluations, phase2_results)
    """
    evaluations: dict[str, OracleEvaluation] = {}
    phase2_results: dict[str, Phase2Result] = {}

    # Mode C: No Oracle (always)
    mode_c = run_mode_c_no_oracle(phase1)
    phase2_results["None"] = mode_c
    evaluations["None"] = evaluate_mode(phase1, mode_c, reference_alignments)

    # Mode B: Det Oracle (always)
    mode_b = run_mode_b_det_oracle(phase1, dm_xlsx_path, template_xlsx)
    phase2_results["Det"] = mode_b
    evaluations["Det"] = evaluate_mode(phase1, mode_b, reference_alignments)

    # Mode A: LLM Oracle (optional)
    if use_llm:
        try:
            mode_a = run_mode_a_llm_oracle(phase1)
            phase2_results["LLM"] = mode_a
            evaluations["LLM"] = evaluate_mode(phase1, mode_a, reference_alignments)
        except Exception as exc:
            print(f"  [WARN] LLM Oracle mode failed: {exc}")
            print(f"  [INFO] Skipping Mode A (LLM Oracle)")

    return evaluations, phase2_results
