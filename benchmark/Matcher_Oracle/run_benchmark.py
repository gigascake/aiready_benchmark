"""Main Matcher-Oracle benchmark runner.

Evaluates the engine's 2-Phase hybrid matching architecture:
  Phase 1: Algorithm matching (T0a-T5 deterministic)
  Phase 2: Oracle verification (3 modes: LLM / Det / None)

Generates bilingual (Korean + English) comparison reports with:
  - Oracle P/R/F1 + Sensitivity/Specificity/Youden's Index
  - Simulated Oracle calibration (Or_0~Or_30)
  - Cost efficiency analysis
  - Gap analysis (auto-computed)
  - LLM comparison table

Usage:
    cd benchmark/Matcher_Oracle
    PYTHONPATH=. python run_benchmark.py [--with-llm] [--output results/]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from oracle_metrics import (
    Alignment,
    OracleEvaluation,
    PhaseResult,
    evaluate_phase,
    run_simulated_oracle_calibration,
)
from phase1_matcher import run_phase1_for_case, Phase1Result
from phase2_oracle import run_all_modes
from cost_analyzer import analyze_costs, get_cost_summary_table
from gap_analysis import run_gap_analysis, generate_gap_markdown
from comparison_data import (
    LLM_MATCHER_ORACLE,
    SIMULATED_ORACLE,
    ARCHITECTURE_COMPARISON,
    grade_youden,
)


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent.parent.parent
CUSTOM_FILES = PROJECT_DIR / "custom_files_3_5"
TEMPLATES_DIR = PROJECT_DIR / "templates"
STORE_PATH = PROJECT_DIR / "data" / "shared" / "mapping_rules_store.json"


# ════════════════════════════════════════════════════════════
# Case discovery
# ════════════════════════════════════════════════════════════

def discover_cases() -> list[dict]:
    """Discover test cases with extraction output and reference alignments."""
    cases: list[dict] = []

    template = TEMPLATES_DIR / "원가계산서_골든셋.xlsx"
    if not template.exists():
        print(f"[ERROR] Template not found: {template}")
        return cases

    if not STORE_PATH.exists():
        print(f"[ERROR] mapping_rules_store not found: {STORE_PATH}")
        return cases

    raw = json.loads(STORE_PATH.read_text("utf-8"))
    store_data = raw.get("rules", raw) if isinstance(raw, dict) else raw
    case_stems = sorted({r.get("case_stem", "") for r in store_data if isinstance(r, dict) and r.get("case_stem")})

    for stem in case_stems:
        extraction = CUSTOM_FILES / f"{stem}_맵핑.xlsx"
        if not extraction.exists():
            extraction = CUSTOM_FILES / f"{stem}_맵핑_allobject.xlsx"
        if not extraction.exists():
            continue

        dm_xlsx = CUSTOM_FILES / f"{stem}_dm.xlsx"

        cases.append({
            "stem": stem,
            "extraction_xlsx": str(extraction),
            "template_xlsx": str(template),
            "dm_xlsx_path": str(dm_xlsx) if dm_xlsx.exists() else "",
        })

    return cases


def load_reference_alignments() -> dict[str, list[Alignment]]:
    """Load user-confirmed mappings as reference alignments."""
    raw = json.loads(STORE_PATH.read_text("utf-8"))
    store_data = raw.get("rules", raw) if isinstance(raw, dict) else raw

    per_case: dict[str, list[Alignment]] = {}
    for rule in store_data:
        if not isinstance(rule, dict):
            continue
        case_stem = rule.get("case_stem", "unknown")
        source = rule.get("source_pattern", "") or rule.get("source_field", "")
        target = rule.get("target_field", "")
        section = rule.get("section", "")
        confidence = rule.get("confidence", 1.0)

        if source and target:
            key = f"{section}::{source}" if section else source
            val = f"{section}::{target}" if section else target
            per_case.setdefault(case_stem, []).append(
                Alignment(source=key, target=val, confidence=confidence)
            )

    return per_case


# ════════════════════════════════════════════════════════════
# Benchmark runner
# ════════════════════════════════════════════════════════════

def run_benchmark(
    cases: list[dict],
    reference_per_case: dict[str, list[Alignment]],
    use_llm: bool = True,
) -> dict:
    """Run full Matcher-Oracle benchmark.

    Returns:
        Dict with all results for report generation.
    """
    all_phase1_alignments: list[Alignment] = []
    all_reference: list[Alignment] = []
    total_uncertain = 0
    tier_distribution: dict[str, int] = {}

    # Accumulate per-case OracleEvaluation counts for each mode
    agg: dict[str, dict] = {}

    for case in cases:
        stem = case["stem"]
        print(f"\n{'='*60}")
        print(f"Processing: {stem}")

        ref_aligns = reference_per_case.get(stem, [])
        if not ref_aligns:
            print(f"  [SKIP] No reference alignments for {stem}")
            continue

        # Phase 1
        print(f"  [Phase 1] Running T0a-T5 matching...")
        phase1 = run_phase1_for_case(
            extraction_xlsx=case["extraction_xlsx"],
            template_xlsx=case["template_xlsx"],
        )
        print(f"    → {phase1.total_candidates} candidates, {phase1.uncertain_count} uncertain")

        for tier, count in phase1.tier_distribution.items():
            tier_distribution[tier] = tier_distribution.get(tier, 0) + count

        # Phase 2 (all modes)
        print(f"  [Phase 2] Running oracle verification...")
        mode_evals, mode_p2 = run_all_modes(
            phase1, ref_aligns,
            use_llm=use_llm,
            dm_xlsx_path=case.get("dm_xlsx_path", ""),
            template_xlsx=case.get("template_xlsx", ""),
        )

        # Accumulate
        all_phase1_alignments.extend(phase1.alignments)
        all_reference.extend(ref_aligns)
        total_uncertain += phase1.uncertain_count

        for mode_name, ev in mode_evals.items():
            if mode_name not in agg:
                agg[mode_name] = {
                    "p1_tp": 0, "p1_fp": 0, "p1_fn": 0,
                    "p2_tp": 0, "p2_fp": 0, "p2_fn": 0,
                    "tp_confirmed": 0, "fn_oracle": 0,
                    "fp_confirmed": 0, "tn_rejected": 0,
                    "oracle_confirm": 0, "oracle_reject": 0,
                    "total_uncertain": 0, "llm_calls": 0,
                }
            d = agg[mode_name]
            d["p1_tp"] += ev.phase1.tp
            d["p1_fp"] += ev.phase1.fp
            d["p1_fn"] += ev.phase1.fn
            d["p2_tp"] += ev.phase2.tp
            d["p2_fp"] += ev.phase2.fp
            d["p2_fn"] += ev.phase2.fn
            d["tp_confirmed"] += ev.tp_confirmed
            d["fn_oracle"] += ev.fn_oracle
            d["fp_confirmed"] += ev.fp_confirmed
            d["tn_rejected"] += ev.tn_rejected
            d["oracle_confirm"] += ev.oracle_confirm
            d["oracle_reject"] += ev.oracle_reject
            d["total_uncertain"] += ev.total_uncertain
            d["llm_calls"] += ev.llm_calls

        print(f"    Results:")
        for mode_name, ev in mode_evals.items():
            print(f"      [{mode_name}] {ev}")

    # Build aggregate evaluations from accumulated counts
    print(f"\n{'='*60}")
    print("Aggregating results...")

    evaluations: dict[str, OracleEvaluation] = {}

    for mode_name in ["None", "Det", "LLM"]:
        if mode_name not in agg:
            continue
        d = agg[mode_name]
        p1 = PhaseResult(label="Phase1", tp=d["p1_tp"], fp=d["p1_fp"], fn=d["p1_fn"])
        p2 = PhaseResult(label="Phase2", tp=d["p2_tp"], fp=d["p2_fp"], fn=d["p2_fn"])
        ev = OracleEvaluation(
            mode=mode_name,
            phase1=p1,
            phase2=p2,
            tp_confirmed=d["tp_confirmed"],
            fn_oracle=d["fn_oracle"],
            fp_confirmed=d["fp_confirmed"],
            tn_rejected=d["tn_rejected"],
            oracle_confirm=d["oracle_confirm"],
            oracle_reject=d["oracle_reject"],
            total_uncertain=d["total_uncertain"],
            llm_calls=d["llm_calls"],
        )
        evaluations[mode_name] = ev
        print(f"  [{mode_name}] {ev}")

    # Simulated Oracle calibration
    print(f"\n  [Simulated Oracle] Running Or_0~Or_30 calibration...")
    sim_results = run_simulated_oracle_calibration(
        phase1_alignments=all_phase1_alignments,
        reference_alignments=all_reference,
    )

    return {
        "evaluations": evaluations,
        "simulated_oracle": sim_results,
        "phase1_alignments": all_phase1_alignments,
        "reference_alignments": all_reference,
        "tier_distribution": tier_distribution,
        "total_candidates": len(all_phase1_alignments),
        "total_uncertain": total_uncertain,
    }


# ════════════════════════════════════════════════════════════
# Report generation (bilingual)
# ════════════════════════════════════════════════════════════

def generate_report(
    results: dict,
    use_llm: bool,
    output_dir: Path,
) -> list[str]:
    """Generate bilingual (KOR + ENG) reports.

    Returns:
        List of generated file paths.
    """
    reports = []

    for lang in ["kor", "eng"]:
        report_path = _generate_single_report(results, use_llm, output_dir, lang)
        reports.append(report_path)

    return reports


def _generate_single_report(
    results: dict,
    use_llm: bool,
    output_dir: Path,
    lang: str,
) -> str:
    """Generate a single-language report."""
    evals = results["evaluations"]
    sim = results["simulated_oracle"]
    tier_dist = results["tier_distribution"]

    is_kor = lang == "kor"
    lines: list[str] = []

    # ── Title ──
    if is_kor:
        lines.append("# Matcher-Oracle 벤치마크 레포트\n")
        lines.append(f"**날짜**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**엔진**: CostReady v0.9 (8-Tier TopologicalMatcher + M1-M5 Validator)\n")
        lines.append(f"**LLM Oracle**: {'활성 (T6)' if use_llm else '비활성'}\n")
        lines.append(f"**테스트 케이스**: {len(results.get('phase1_alignments', []))} 정렬\n\n")
    else:
        lines.append("# Matcher-Oracle Benchmark Report\n")
        lines.append(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**Engine**: CostReady v0.9 (8-Tier TopologicalMatcher + M1-M5 Validator)\n")
        lines.append(f"**LLM Oracle**: {'Enabled (T6)' if use_llm else 'Disabled'}\n")
        lines.append(f"**Test alignments**: {len(results.get('phase1_alignments', []))}\n\n")

    # ── 1. Executive Summary ──
    if is_kor:
        lines.append("## 1. 요약 / Executive Summary\n\n")
        lines.append("| Mode | Phase1 F1 | Oracle F1 | Delta | Se | Sp | YI | Grade | LLM Calls |")
        lines.append("|------|-----------|-----------|-------|----|----|----|-------|-----------|")
    else:
        lines.append("## 1. Executive Summary\n\n")
        lines.append("| Mode | Phase1 F1 | Oracle F1 | Delta | Se | Sp | YI | Grade | LLM Calls |")
        lines.append("|------|-----------|-----------|-------|----|----|----|-------|-----------|")

    for mode_name in ["None", "Det", "LLM"]:
        if mode_name not in evals:
            continue
        ev = evals[mode_name]
        grade, _ = ev.grade
        se_str = f"{ev.sensitivity:.4f}" if mode_name != "None" else "—"
        sp_str = f"{ev.specificity:.4f}" if mode_name != "None" else "—"
        yi_str = f"{ev.youden_index:.4f}" if mode_name != "None" else "—"
        lines.append(
            f"| {mode_name} | {ev.phase1_f1:.4f} | {ev.oracle_f1:.4f} | "
            f"{ev.oracle_delta:+.4f} | {se_str} | {sp_str} | {yi_str} | "
            f"{grade if mode_name != 'None' else '—'} | {ev.llm_calls} |"
        )
    lines.append("")

    # ── 2. Phase Results ──
    if is_kor:
        lines.append("\n## 2. Phase 결과 / Phase Results\n\n")
    else:
        lines.append("\n## 2. Phase Results\n\n")

    for mode_name in ["None", "Det", "LLM"]:
        if mode_name not in evals:
            continue
        ev = evals[mode_name]
        mode_label = {"None": "C: No Oracle", "Det": "B: Det. Oracle", "LLM": "A: LLM Oracle"}[mode_name]

        if is_kor:
            lines.append(f"### Mode {mode_label}\n")
        else:
            lines.append(f"### Mode {mode_label}\n")

        lines.append("| Phase | Precision | Recall | F1 | TP | FP | FN |")
        lines.append("|-------|-----------|--------|----|----|----|-----|")
        lines.append(
            f"| Phase 1 | {ev.phase1.precision:.4f} | {ev.phase1.recall:.4f} | "
            f"{ev.phase1.f1:.4f} | {ev.phase1.tp} | {ev.phase1.fp} | {ev.phase1.fn} |"
        )
        lines.append(
            f"| Phase 2 | {ev.phase2.precision:.4f} | {ev.phase2.recall:.4f} | "
            f"{ev.phase2.f1:.4f} | {ev.phase2.tp} | {ev.phase2.fp} | {ev.phase2.fn} |"
        )
        lines.append("")

    # ── 3. Oracle Diagnostic Analysis ──
    if is_kor:
        lines.append("\n## 3. Oracle 진단 분석 / Oracle Diagnostic Analysis\n\n")
    else:
        lines.append("\n## 3. Oracle Diagnostic Analysis\n\n")

    for mode_name in ["Det", "LLM"]:
        if mode_name not in evals:
            continue
        ev = evals[mode_name]

        if is_kor:
            lines.append(f"### {mode_name} Oracle — 혼동 행렬 / Confusion Matrix\n\n")
        else:
            lines.append(f"### {mode_name} Oracle — Confusion Matrix\n\n")

        lines.append("| | Oracle=Confirm | Oracle=Reject | Total |")
        lines.append("|---|:---:|:---:|:---:|")
        lines.append(
            f"| **True Match** | {ev.tp_confirmed} | {ev.fn_oracle} | "
            f"{ev.tp_confirmed + ev.fn_oracle} |"
        )
        lines.append(
            f"| **False Match** | {ev.fp_confirmed} | {ev.tn_rejected} | "
            f"{ev.fp_confirmed + ev.tn_rejected} |"
        )
        lines.append("")

        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Sensitivity (Se) | {ev.sensitivity:.4f} |")
        lines.append(f"| Specificity (Sp) | {ev.specificity:.4f} |")
        lines.append(f"| Youden's Index (YI) | {ev.youden_index:.4f} |")
        grade, grade_desc = ev.grade
        lines.append(f"| Grade | **{grade}** ({grade_desc}) |")
        lines.append(f"| Simulated Oracle Eq. | **{ev.simulated_oracle_equivalent}** |")
        lines.append("")

    # Simulated Oracle Calibration
    if is_kor:
        lines.append("### 3-2. Simulated Oracle 캘리브레이션 (Or_0~Or_30)\n\n")
        lines.append("> Lushnei et al. (EACL 2026): 오류율 0%~30% 시뮬레이션 Oracle\n\n")
    else:
        lines.append("### 3-2. Simulated Oracle Calibration (Or_0~Or_30)\n\n")
        lines.append("> Lushnei et al. (EACL 2026): Simulated Oracles with 0%~30% error rate\n\n")

    lines.append("| Oracle | Error Rate | F1 | YI | Grade |")
    lines.append("|--------|-----------|----|----|-------|")
    for name in sorted(SIMULATED_ORACLE.keys()):
        if name not in sim:
            continue
        ev = sim[name]
        grade, _ = ev.grade
        lines.append(
            f"| {name} | {SIMULATED_ORACLE[name]['error_rate']:.0%} | "
            f"{ev.oracle_f1:.4f} | {ev.youden_index:.4f} | {grade} |"
        )
    lines.append("")

    # ── 4. Cost Efficiency Analysis ──
    if is_kor:
        lines.append("\n## 4. 비용 효율 분석 / Cost Efficiency Analysis\n\n")
    else:
        lines.append("\n## 4. Cost Efficiency Analysis\n\n")

    costs = analyze_costs(evals, results["total_candidates"])
    lines.extend(get_cost_summary_table(costs))

    # ── 5. LLM Matcher-Oracle Comparison Table ──
    if is_kor:
        lines.append("\n## 5. LLM Matcher-Oracle 비교표 / LLM Comparison Table\n\n")
    else:
        lines.append("\n## 5. LLM Matcher-Oracle Comparison Table\n\n")

    lines.append("| Rank | System | Type | Oracle F1 | Se | Sp | YI | Grade | Cost |")
    lines.append("|------|--------|------|-----------|----|----|----|-------|------|")

    # Engine row
    best_ev = None
    best_f1 = 0
    for mode_name in ["Det", "LLM"]:
        if mode_name in evals and evals[mode_name].oracle_f1 > best_f1:
            best_f1 = evals[mode_name].oracle_f1
            best_ev = evals[mode_name]

    if best_ev:
        grade, _ = best_ev.grade
        lines.append(
            f"| — | **CostReady v0.9** | **Hybrid** | **{best_ev.oracle_f1:.4f}** | "
            f"**{best_ev.sensitivity:.4f}** | **{best_ev.specificity:.4f}** | "
            f"**{best_ev.youden_index:.4f}** | **{grade}** | **$0** |"
        )

    for rank, (name, info) in enumerate(
        sorted(LLM_MATCHER_ORACLE.items(), key=lambda x: -x[1]["f1"]), 1
    ):
        lines.append(
            f"| {rank} | {name} | LLM Oracle | {info['f1']:.4f} | "
            f"— | — | — | — | {info['cost_efficiency']} |"
        )
    lines.append("")

    # ── 6. Architecture Comparison ──
    if is_kor:
        lines.append("\n## 6. 아키텍처 비교 / Architecture Comparison\n\n")
    else:
        lines.append("\n## 6. Architecture Comparison\n\n")

    lines.append("| Architecture | Phase 1 | Oracle | LLM Usage | Cost | Verifier |")
    lines.append("|-------------|---------|--------|-----------|------|----------|")
    for name, info in ARCHITECTURE_COMPARISON.items():
        lines.append(
            f"| **{name}** | {info['phase1']} | {info['oracle']} | "
            f"{info['llm_usage']} | {info['cost']} | {info['verifier']} |"
        )
    lines.append("")

    # ── 7. Gap Analysis ──
    cost_saved_pct = costs.get("Det", costs.get("LLM", costs.get("None"))).cost_saved_pct if costs else 0.0

    gap = run_gap_analysis(
        evaluations=evals,
        phase1_alignments=results["phase1_alignments"],
        reference_alignments=results["reference_alignments"],
        tier_distribution=tier_dist,
        cost_saved_pct=cost_saved_pct,
    )
    lines.extend(generate_gap_markdown(gap))

    # ── 8. Update text for 260610 비교표 ──
    if is_kor:
        lines.append("\n## 8. 260610 비교표 Section 3-5 업데이트 텍스트\n\n")
        lines.append("```markdown\n")
        lines.append("### 3-5. 하이브리드 매칭 검증 (Matcher-Oracle)\n\n")
        lines.append("| 순위 | 시스템 | 유형 | Oracle F1 | Se | Sp | YI | LLM Calls | 비용 | 비고 |")
        lines.append("|------|--------|------|-----------|----|----|----|-----------|------|------|")
    else:
        lines.append("\n## 8. Update Text for 260610 Comparison Table\n\n")
        lines.append("```markdown\n")
        lines.append("### 3-5. Hybrid Matching Verification (Matcher-Oracle)\n\n")
        lines.append("| Rank | System | Type | Oracle F1 | Se | Sp | YI | LLM Calls | Cost | Note |")
        lines.append("|------|--------|------|-----------|----|----|----|-----------|------|------|")

    if best_ev:
        grade, _ = best_ev.grade
        note_kor = "T0~T5+M1~M5" if best_ev.mode == "Det" else "T0~T6 (LLM)"
        lines.append(
            f"| — | **CostReady v0.9** | **Hybrid** | **{best_ev.oracle_f1:.4f}** | "
            f"**{best_ev.sensitivity:.4f}** | **{best_ev.specificity:.4f}** | "
            f"**{best_ev.youden_index:.4f}** | **{best_ev.llm_calls}** | **$0** | {note_kor} |"
        )

    for rank, (name, info) in enumerate(
        sorted(LLM_MATCHER_ORACLE.items(), key=lambda x: -x[1]["f1"]), 1
    ):
        lines.append(
            f"| {rank} | {name} | LLM Oracle | {info['f1']:.4f} | "
            f"— | — | — | 다수 | {info['cost_efficiency']} | — |"
        )
    lines.append("```\n")

    # ── 9. Notes ──
    if is_kor:
        lines.append("\n## 9. 비고 / Notes\n\n")
        lines.append(
            "- **Matcher-Oracle 패러다임**: Lushnei et al. (EACL 2026), "
            "알고리즘 매칭 + LLM 검증 하이브리드 평가 방법론.\n"
        )
        lines.append(
            "- **CostReady 정합성**: T0a-T5(결정론) + T6(LLM) + M1-M5(검증) = "
            "Matcher-Oracle 아키텍처와 동일.\n"
        )
        lines.append(
            "- **Oracle 진단 지표**: Sensitivity/Specificity/Youden's Index는 "
            "Oracle의 판정 품질을 평가 (Lushnei et al. 방법론).\n"
        )
        lines.append(
            "- **Simulated Oracle**: Or_0~Or_30은 Lushnei et al.의 시뮬레이션 Oracle 캘리브레이션. "
            "LLM-Oracle ≈ Or_20 (~80% 정확도).\n"
        )
        lines.append(
            "- **비용 추정**: 모델별 API 단가 기반 추정치. 자체 호스팅 모델(Qwen3.5/Llama)은 $0.\n"
        )
        lines.append(
            "- **모든 수치는 자동 산출**: Gap 분석(Section 7)은 하드코딩 없이 "
            "실제 측정값에서 자동 계산됨.\n"
        )
    else:
        lines.append("\n## 9. Notes\n\n")
        lines.append(
            "- **Matcher-Oracle paradigm**: Lushnei et al. (EACL 2026), "
            "a hybrid evaluation methodology for algorithm + LLM verification.\n"
        )
        lines.append(
            "- **CostReady alignment**: T0a-T5 (deterministic) + T6 (LLM) + M1-M5 (validator) "
            "= identical to Matcher-Oracle architecture.\n"
        )
        lines.append(
            "- **Oracle diagnostics**: Sensitivity/Specificity/Youden's Index evaluate "
            "oracle decision quality (Lushnei et al. methodology).\n"
        )
        lines.append(
            "- **Simulated Oracle**: Or_0~Or_30 are simulated Oracle calibrations "
            "(Lushnei et al.). LLM-Oracle ≈ Or_20 (~80% accuracy).\n"
        )
        lines.append(
            "- **Cost estimation**: Based on per-model API pricing. "
            "Self-hosted models (Qwen3.5/Llama) = $0.\n"
        )
        lines.append(
            "- **All values auto-computed**: Gap analysis (Section 7) is computed from "
            "actual benchmark data with no hardcoded numbers.\n"
        )

    # Write file
    suffix = f"_{lang}" if lang != "kor" else ""
    report_path = output_dir / f"benchmark_report{suffix}.md"
    report_path.write_text("\n".join(lines), "utf-8")
    print(f"\n  Report [{lang}] saved to: {report_path}")
    return str(report_path)


# ════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Matcher-Oracle Benchmark for CostReady Engine"
    )
    parser.add_argument(
        "--with-llm", action="store_true",
        help="Enable LLM Oracle mode (Mode A, requires VLM server at :28000)",
    )
    parser.add_argument(
        "--output", default="results",
        help="Output directory (default: results/)",
    )
    args = parser.parse_args()

    output_dir = BASE_DIR / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Matcher-Oracle Benchmark: CostReady Engine")
    print(f"LLM Oracle: {'Enabled' if args.with_llm else 'Disabled'}")
    print("=" * 60)

    # ── Discover cases ──
    print("\n[1/4] Discovering test cases...")
    cases = discover_cases()
    print(f"  Found {len(cases)} test cases")
    for c in cases:
        print(f"    - {c['stem']}")

    if not cases:
        print("[ERROR] No test cases found.")
        sys.exit(1)

    # ── Load references ──
    print("\n[2/4] Loading reference alignments...")
    reference_per_case = load_reference_alignments()
    total_refs = sum(len(v) for v in reference_per_case.values())
    print(f"  Loaded {total_refs} reference alignments across {len(reference_per_case)} cases")

    if not reference_per_case:
        print("[ERROR] No reference alignments found.")
        sys.exit(1)

    # ── Run benchmark ──
    print(f"\n[3/4] Running benchmark...")
    t0 = time.time()
    results = run_benchmark(cases, reference_per_case, use_llm=args.with_llm)
    elapsed = time.time() - t0
    print(f"\n  Completed in {elapsed:.1f}s")

    # ── Save raw results ──
    raw_data: dict = {
        "elapsed_seconds": elapsed,
        "use_llm": args.with_llm,
        "total_candidates": results["total_candidates"],
        "total_uncertain": results["total_uncertain"],
        "tier_distribution": results["tier_distribution"],
        "evaluations": {},
        "simulated_oracle": {},
    }
    for mode_name, ev in results["evaluations"].items():
        raw_data["evaluations"][mode_name] = {
            "mode": ev.mode,
            "phase1_f1": ev.phase1_f1,
            "phase2_f1": ev.oracle_f1,
            "oracle_delta": ev.oracle_delta,
            "sensitivity": ev.sensitivity,
            "specificity": ev.specificity,
            "youden_index": ev.youden_index,
            "tp_confirmed": ev.tp_confirmed,
            "fn_oracle": ev.fn_oracle,
            "fp_confirmed": ev.fp_confirmed,
            "tn_rejected": ev.tn_rejected,
            "llm_calls": ev.llm_calls,
            "grade": ev.grade[0],
            "oracle_equivalent": ev.simulated_oracle_equivalent,
        }
    for name, ev in results["simulated_oracle"].items():
        raw_data["simulated_oracle"][name] = {
            "oracle_f1": ev.oracle_f1,
            "youden_index": ev.youden_index,
        }

    raw_path = output_dir / "raw_results.json"
    raw_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), "utf-8")
    print(f"  Raw results saved to: {raw_path}")

    # ── Generate reports ──
    print(f"\n[4/4] Generating reports (KOR + ENG)...")
    report_paths = generate_report(results, args.with_llm, output_dir)

    print("\n" + "=" * 60)
    print("Benchmark complete!")
    for p in report_paths:
        print(f"  Report: {p}")
    print(f"  Raw:    {raw_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
