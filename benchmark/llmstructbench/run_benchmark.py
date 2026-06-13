"""Main LLMStructBench benchmark runner.

Evaluates the excel_ready engine's extraction and/or mapping pipeline
using LLMStructBench methodology (F1_micro, DOC_micro, Composite Score),
then generates a comparison report with published LLM results.

Usage:
    cd excel_ready/benchmark/llmstructbench
    PYTHONPATH=. python run_benchmark.py [--evaluate extraction|mapping|both] [--output results/]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from struct_metrics import BatchResult, LAMBDA
from error_classifier import classify_pairs, analysis_to_f1_result


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent.parent.parent
CUSTOM_FILES = PROJECT_DIR / "custom_files_3_5"
RIGHT_FILES = PROJECT_DIR / "right_files"
TEMPLATES_DIR = PROJECT_DIR / "templates"


def _normalize_stem(name: str) -> str:
    """Extract the 원가계산서_XXXX stem from a filename."""
    for prefix in ("원가계산서_",):
        if name.startswith(prefix):
            rest = name[len(prefix):]
            return prefix + rest.split("_")[0]
    return name.split(".")[0]


def discover_extraction_cases() -> list[dict]:
    """Find all cases with both GT and extraction output."""
    cases: list[dict] = []

    gt_files = {}
    for f in RIGHT_FILES.glob("*.xlsx"):
        gt_files[_normalize_stem(f.name)] = f

    sys_files = {}
    for f in CUSTOM_FILES.glob("*_맵핑.xlsx"):
        if "_allobject" in f.name or "_pattern" in f.name:
            continue
        stem = _normalize_stem(f.name.replace("_맵핑.xlsx", ""))
        sys_files[stem] = f

    for stem in sorted(set(gt_files.keys()) & set(sys_files.keys())):
        cases.append({
            "stem": stem,
            "gt_xlsx": str(gt_files[stem]),
            "sys_xlsx": str(sys_files[stem]),
        })

    return cases


def discover_mapping_cases() -> list[dict]:
    """Find all cases with template and DM output."""
    cases: list[dict] = []

    template = TEMPLATES_DIR / "원가계산서_골든셋.xlsx"
    if not template.exists():
        return cases

    for f in sorted(CUSTOM_FILES.glob("*_dm.xlsx")):
        stem = _normalize_stem(f.name.replace("_dm.xlsx", ""))
        cases.append({
            "stem": stem,
            "template_xlsx": str(template),
            "mapped_xlsx": str(f),
        })

    return cases


def run_extraction_benchmark() -> tuple[BatchResult, list]:
    """Run extraction evaluation on all discovered cases."""
    from extraction_evaluator import evaluate_extraction, _load_xlsx_sheet_pairs
    from struct_metrics import CellPair
    from error_classifier import ErrorAnalysis

    cases = discover_extraction_cases()
    print(f"  Found {len(cases)} extraction cases")

    batch = BatchResult()
    all_analyses: list[ErrorAnalysis] = []

    for case in cases:
        print(f"\n  Processing: {case['stem']}")
        print(f"    GT:   {Path(case['gt_xlsx']).name}")
        print(f"    SYS:  {Path(case['sys_xlsx']).name}")

        sub_batch = evaluate_extraction(case["gt_xlsx"], case["sys_xlsx"])

        for sr in sub_batch.sheet_results:
            sr.sheet_name = f"{case['stem']}/{sr.sheet_name}"
            batch.sheet_results.append(sr)
            print(f"    {sr.sheet_name}: F1={sr.f1_result.f1_micro:.4f} "
                  f"{'✅' if sr.is_correct else '❌'} "
                  f"({sr.matched_cells}/{sr.total_cells} cells)")

        from extraction_evaluator import _load_xlsx_sheet_pairs, _match_headers
        from openpyxl import load_workbook
        gt_path = Path(case["gt_xlsx"])
        sys_path = Path(case["sys_xlsx"])
        gt_wb = load_workbook(gt_path, read_only=True, data_only=True)
        for ws_name in [ws.title for ws in gt_wb.worksheets]:
            gt_h, gt_r = _load_xlsx_sheet_pairs(gt_path, ws_name)
            sys_h, sys_r = _load_xlsx_sheet_pairs(sys_path, ws_name)
            if not gt_h or not sys_h:
                continue
            hmap = _match_headers(gt_h, sys_h)
            gt_p: list[CellPair] = []
            sys_p: list[CellPair] = []
            for gc, sc in hmap.items():
                gh = gt_h[gc]
                for ri in range(max(len(gt_r), len(sys_r))):
                    gv = gt_r[ri][gc] if ri < len(gt_r) and gc < len(gt_r[ri]) else None
                    sv = sys_r[ri][sc] if ri < len(sys_r) and sc < len(sys_r[ri]) else None
                    k = f"{ws_name}::{gh}::R{ri+1:04d}"
                    gt_p.append(CellPair(key=k, value=gv, field_name=gh))
                    sys_p.append(CellPair(key=k, value=sv, field_name=gh))
            for gc in range(len(gt_h)):
                if gc not in hmap and gt_h[gc]:
                    for ri in range(len(gt_r)):
                        gv = gt_r[ri][gc] if gc < len(gt_r[ri]) else None
                        k = f"{ws_name}::{gt_h[gc]}::R{ri+1:04d}"
                        gt_p.append(CellPair(key=k, value=gv, field_name=gt_h[gc]))
            for sc in range(len(sys_h)):
                if sc not in set(hmap.values()) and sys_h[sc]:
                    for ri in range(len(sys_r)):
                        sv = sys_r[ri][sc] if sc < len(sys_r[ri]) else None
                        k = f"{ws_name}::{sys_h[sc]}::R{ri+1:04d}"
                        sys_p.append(CellPair(key=k, value=sv, field_name=sys_h[sc]))
            analysis = classify_pairs(gt_p, sys_p)
            all_analyses.append(analysis)
        gt_wb.close()

    return batch, all_analyses


def run_mapping_benchmark() -> tuple[BatchResult, list]:
    """Run mapping evaluation on all discovered cases."""
    from mapping_evaluator import evaluate_mapping
    from struct_metrics import CellPair
    from error_classifier import ErrorAnalysis, classify_pairs

    cases = discover_mapping_cases()
    print(f"  Found {len(cases)} mapping cases")

    batch = BatchResult()
    all_analyses: list[ErrorAnalysis] = []

    for case in cases:
        print(f"\n  Processing: {case['stem']}")
        print(f"    TPL:  {Path(case['template_xlsx']).name}")
        print(f"    DM:   {Path(case['mapped_xlsx']).name}")

        sub_batch = evaluate_mapping(case["template_xlsx"], case["mapped_xlsx"])

        for sr in sub_batch.sheet_results:
            sr.sheet_name = f"{case['stem']}/{sr.sheet_name}"
            batch.sheet_results.append(sr)
            print(f"    {sr.sheet_name}: F1={sr.f1_result.f1_micro:.4f} "
                  f"{'✅' if sr.is_correct else '❌'} "
                  f"({sr.matched_cells}/{sr.total_cells} cells)")
            if sr.f1_result.detail:
                print(f"      merges: {sr.f1_result.detail.get('map_merges', '?')}/"
                      f"{sr.f1_result.detail.get('tpl_merges', '?')}, "
                      f"fill: {sr.f1_result.detail.get('fill_ratio', 0):.1%}")

    return batch, all_analyses


def generate_report(
    ext_batch: BatchResult | None,
    ext_analyses: list | None,
    map_batch: BatchResult | None,
    map_analyses: list | None,
    elapsed: float,
    output_dir: Path,
) -> str:
    """Generate markdown comparison report."""
    from comparison_data import LLM_STRUCT_BENCH
    from gap_analysis import run_gap_analysis, generate_gap_analysis_markdown

    lines: list[str] = []
    lines.append("# LLMStructBench Report: Engine vs Published LLM Systems\n")
    lines.append(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    tasks = []
    if ext_batch:
        tasks.append("Extraction")
    if map_batch:
        tasks.append("Mapping")
    lines.append(f"**Tasks**: {' + '.join(tasks)}\n")
    lines.append(f"**Elapsed**: {elapsed:.1f}s\n")
    lines.append(f"**Methodology**: LLMStructBench (arXiv 2602.14743) — "
                 f"α=0.25 (key weight), λ={LAMBDA} (DOC/F1 balance)\n")
    lines.append("\n> ⚠️ **Caveat — Measurement Scope**: This benchmark evaluates "
                 "**pre-generated output files** (extraction XLSX, DM XLSX) against "
                 "ground truth / template. It does **not** invoke the live extraction "
                 "or mapping engine. Extraction F1 measures cell-level accuracy of "
                 "existing XLSX files. Mapping F1 measures structural fidelity (fill "
                 "ratio, merge preservation) — **not** semantic mapping correctness, "
                 "as no reference mapping exists. For live engine evaluation, see "
                 "OAEI and Matcher-Oracle benchmarks.\n\n")

    section_num = 1

    # ── Engine Performance ──
    lines.append(f"## {section_num}. Engine Performance (Auto-computed)\n")
    section_num += 1

    lines.append("| Task | F1_keys | F1_values | F1_micro | DOC_micro | Composite |")
    lines.append("|------|---------|-----------|----------|-----------|-----------|")

    if ext_batch:
        total_tp_k = sum(r.f1_result.tp_keys for r in ext_batch.sheet_results)
        total_fp_k = sum(r.f1_result.fp_keys for r in ext_batch.sheet_results)
        total_fn_k = sum(r.f1_result.fn_keys for r in ext_batch.sheet_results)
        total_tp_v = sum(r.f1_result.tp_values for r in ext_batch.sheet_results)
        total_fn_v = sum(r.f1_result.fn_values for r in ext_batch.sheet_results)
        total_err = sum(r.f1_result.error_count for r in ext_batch.sheet_results)

        p_k = total_tp_k / (total_tp_k + total_fp_k) if (total_tp_k + total_fp_k) > 0 else 0
        r_k = total_tp_k / (total_tp_k + total_fn_k) if (total_tp_k + total_fn_k) > 0 else 0
        f1_k = 2*p_k*r_k/(p_k+r_k) if (p_k+r_k) > 0 else 0

        p_v = total_tp_v / (total_tp_v + total_err) if (total_tp_v + total_err) > 0 else 0
        r_v = total_tp_v / (total_tp_v + total_fn_v) if (total_tp_v + total_fn_v) > 0 else 0
        f1_v = 2*p_v*r_v/(p_v+r_v) if (p_v+r_v) > 0 else 0

        lines.append(
            f"| **Extraction** | {f1_k:.4f} | {f1_v:.4f} | "
            f"**{ext_batch.f1_micro:.4f}** | **{ext_batch.doc_micro:.4f}** | "
            f"**{ext_batch.composite:.4f}** |"
        )

    if map_batch:
        total_tp_k = sum(r.f1_result.tp_keys for r in map_batch.sheet_results)
        total_fp_k = sum(r.f1_result.fp_keys for r in map_batch.sheet_results)
        total_fn_k = sum(r.f1_result.fn_keys for r in map_batch.sheet_results)
        total_tp_v = sum(r.f1_result.tp_values for r in map_batch.sheet_results)
        total_fn_v = sum(r.f1_result.fn_values for r in map_batch.sheet_results)
        total_err = sum(r.f1_result.error_count for r in map_batch.sheet_results)

        p_k = total_tp_k / (total_tp_k + total_fp_k) if (total_tp_k + total_fp_k) > 0 else 0
        r_k = total_tp_k / (total_tp_k + total_fn_k) if (total_tp_k + total_fn_k) > 0 else 0
        f1_k = 2*p_k*r_k/(p_k+r_k) if (p_k+r_k) > 0 else 0

        p_v = total_tp_v / (total_tp_v + total_err) if (total_tp_v + total_err) > 0 else 0
        r_v = total_tp_v / (total_tp_v + total_fn_v) if (total_tp_v + total_fn_v) > 0 else 0
        f1_v = 2*p_v*r_v/(p_v+r_v) if (p_v+r_v) > 0 else 0

        lines.append(
            f"| **Mapping** | {f1_k:.4f} | {f1_v:.4f} | "
            f"**{map_batch.f1_micro:.4f}** | **{map_batch.doc_micro:.4f}** | "
            f"**{map_batch.composite:.4f}** |"
        )
    lines.append("")

    # ── Gap Analysis sections ──
    if ext_batch and ext_analyses:
        gap = run_gap_analysis(ext_batch, "extraction", ext_analyses)
        lines.append(f"\n## {section_num}. Extraction — Detailed Analysis\n")
        section_num += 1
        gap_lines = generate_gap_analysis_markdown(
            gap, ext_batch.f1_micro, ext_batch.doc_micro, ext_batch.composite,
        )
        lines.extend(gap_lines)

    if map_batch and map_analyses is not None:
        gap = run_gap_analysis(map_batch, "mapping", map_analyses)
        lines.append(f"\n## {section_num}. Mapping — Detailed Analysis\n")
        section_num += 1
        gap_lines = generate_gap_analysis_markdown(
            gap, map_batch.f1_micro, map_batch.doc_micro, map_batch.composite,
        )
        lines.extend(gap_lines)

    # ── Notes ──
    lines.append(f"\n## {section_num}. Notes\n\n")
    lines.append("- **Methodology**: LLMStructBench (arXiv 2602.14743, Tenckhoff et al.). "
                 "F1_micro (α=0.25 key, 0.75 value), DOC_micro (document-level), "
                 f"Composite (λ={LAMBDA}).\n")
    lines.append("- **Fuzzy credit**: Levenshtein-based partial credit for string deviations "
                 "(L_good=0.1, L_bad=2.0, γ=0.5). Numeric fields use domain tolerances "
                 "(단가=0.01, 소요량=0.001, etc.).\n")
    lines.append("- **Domain difference**: LLMStructBench evaluates NL text → JSON. "
                 "Engine evaluates XLSX → XLSX (extraction) and XLSX → template XLSX (mapping). "
                 "Cross-domain comparison is indicative, not definitive.\n")
    lines.append("- **Measurement scope (caveat)**: This benchmark compares **pre-generated "
                 "output files**, not live engine output. Mapping evaluation lacks reference "
                 "answers, so mapping F1 = structural fidelity (fill/merge), not semantic "
                 "correctness. For live engine semantic evaluation, see OAEI/Matcher-Oracle.\n")
    lines.append("- **LLM sources**: `docs/260610_LLM_vs_CostReady_성능비교표.md` Section 3-4 "
                 "(GPT-5.4, Claude Opus 4.6, Gemini 3.1 Pro, etc.).\n")
    lines.append("- **Gap analysis**: All error profiles, per-sheet breakdowns, and "
                 "comparisons are **fully auto-computed** from actual benchmark data.\n")

    report_path = output_dir / "benchmark_report.md"
    report_path.write_text("\n".join(lines), "utf-8")
    print(f"\n  Report saved to: {report_path}")
    return str(report_path)


def main():
    parser = argparse.ArgumentParser(
        description="LLMStructBench Benchmark for excel_ready Engine",
    )
    parser.add_argument(
        "--evaluate", default="both",
        choices=["extraction", "mapping", "both"],
        help="Evaluation task (default: both)",
    )
    parser.add_argument(
        "--output", default="results",
        help="Output directory (default: results/)",
    )
    args = parser.parse_args()

    output_dir = BASE_DIR / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("LLMStructBench Benchmark: excel_ready Engine")
    print(f"Tasks: {args.evaluate}")
    print("=" * 60)

    ext_batch = None
    ext_analyses = None
    map_batch = None
    map_analyses = None

    t0 = time.time()

    if args.evaluate in ("extraction", "both"):
        print("\n[1] Extraction Evaluation")
        ext_batch, ext_analyses = run_extraction_benchmark()
        if ext_batch.sheet_results:
            print(f"\n  F1_micro={ext_batch.f1_micro:.4f}  "
                  f"DOC_micro={ext_batch.doc_micro:.4f}  "
                  f"Composite={ext_batch.composite:.4f}")

    if args.evaluate in ("mapping", "both"):
        print("\n[2] Mapping Evaluation")
        map_batch, map_analyses = run_mapping_benchmark()
        if map_batch.sheet_results:
            print(f"\n  F1_micro={map_batch.f1_micro:.4f}  "
                  f"DOC_micro={map_batch.doc_micro:.4f}  "
                  f"Composite={map_batch.composite:.4f}")

    elapsed = time.time() - t0

    # ── Save raw results ──
    raw_data: dict = {
        "elapsed_seconds": elapsed,
        "tasks": args.evaluate,
    }
    if ext_batch:
        raw_data["extraction"] = {
            "f1_micro": ext_batch.f1_micro,
            "doc_micro": ext_batch.doc_micro,
            "composite": ext_batch.composite,
            "sheets": [
                {
                    "sheet": sr.sheet_name,
                    "f1_micro": sr.f1_result.f1_micro,
                    "f1_keys": sr.f1_result.f1_keys,
                    "f1_values": sr.f1_result.f1_values,
                    "is_correct": sr.is_correct,
                    "total_cells": sr.total_cells,
                    "matched_cells": sr.matched_cells,
                }
                for sr in ext_batch.sheet_results
            ],
        }
    if map_batch:
        raw_data["mapping"] = {
            "f1_micro": map_batch.f1_micro,
            "doc_micro": map_batch.doc_micro,
            "composite": map_batch.composite,
            "sheets": [
                {
                    "sheet": sr.sheet_name,
                    "f1_micro": sr.f1_result.f1_micro,
                    "is_correct": sr.is_correct,
                    "total_cells": sr.total_cells,
                    "matched_cells": sr.matched_cells,
                    "detail": sr.f1_result.detail,
                }
                for sr in map_batch.sheet_results
            ],
        }

    raw_path = output_dir / "raw_results.json"
    raw_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), "utf-8")
    print(f"  Raw results saved to: {raw_path}")

    # ── Generate report ──
    print("\n[3] Generating report...")
    report_path = generate_report(
        ext_batch, ext_analyses,
        map_batch, map_analyses,
        elapsed, output_dir,
    )

    print("\n" + "=" * 60)
    print("Benchmark complete!")
    print(f"  Report: {report_path}")
    print(f"  Raw:    {raw_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
