# LLMStructBench Report: Engine vs Published LLM Systems

**Date**: 2026-06-13 22:39:23

**Tasks**: Extraction + Mapping

**Elapsed**: 1.1s

**Methodology**: LLMStructBench (arXiv 2602.14743) — α=0.25 (key weight), λ=0.5 (DOC/F1 balance)


## 1. Engine Performance (Auto-computed)

| Task | F1_keys | F1_values | F1_micro | DOC_micro | Composite |
|------|---------|-----------|----------|-----------|-----------|
| **Extraction** | 1.0000 | 0.9962 | **0.9972** | **0.0000** | **0.4986** |
| **Mapping** | 0.3426 | 0.9456 | **0.7949** | **0.1667** | **0.4808** |


## 2. Extraction — Detailed Analysis


## Error Profile — Extraction (Auto-computed)

> All values below are **computed from actual benchmark data**.

### Error Distribution


| Error Type | Count | % | Description |
|------------|-------|---|-------------|
| **MK** | 0 | 0.0% | Missing Key (column absent) |
| **MV** | 0 | 0.0% | Missing Value (key present, value null) |
| **WV** | 338 | 100.0% | Wrong Value (value mismatch) |
| **Total** | **338** | **100%** | |

### WV Subtype Breakdown


| Subtype | Count | Credit | Description |
|---------|-------|--------|-------------|
| value_error | 338 | 0.0 | Same type, different content |

### Sample Errors (Actual Data)

  VALUE_ERROR `재료비_값::LOSS율::R0013`: GT=`None` SYS=`0.022490458798408507`
  VALUE_ERROR `재료비_값::LOSS율::R0014`: GT=`None` SYS=`0`
  VALUE_ERROR `재료비_값::LOSS율::R0015`: GT=`None` SYS=`0`
  VALUE_ERROR `재료비_값::LOSS율::R0016`: GT=`None` SYS=`0`
  VALUE_ERROR `재료비_값::LOSS율::R0017`: GT=`None` SYS=`0`
  VALUE_ERROR `재료비_값::LOSS율::R0018`: GT=`None` SYS=`0`
  VALUE_ERROR `재료비_값::LOSS율::R0019`: GT=`None` SYS=`0`
  VALUE_ERROR `재료비_값::LOSS율::R0020`: GT=`None` SYS=`0`
  VALUE_ERROR `재료비_값::LOSS율::R0021`: GT=`None` SYS=`0`
  VALUE_ERROR `재료비_값::LOSS율::R0022`: GT=`None` SYS=`0`
  VALUE_ERROR `노무비_값::C/T::R0004`: GT=`None` SYS=`51.19`
  VALUE_ERROR `노무비_값::C/T::R0005`: GT=`None` SYS=`84`
  VALUE_ERROR `노무비_값::C/T::R0006`: GT=`None` SYS=`9.115222528`
  VALUE_ERROR `노무비_값::C/V::R0004`: GT=`None` SYS=`2`
  VALUE_ERROR `노무비_값::C/V::R0005`: GT=`None` SYS=`1`

### Per-Sheet Breakdown


| Sheet | F1_keys | F1_values | F1_micro | DOC | Correct? | Total | Matched |
|-------|---------|-----------|----------|-----|----------|-------|---------|
| 원가계산서_0310/재료비_값 | 1.0000 | 0.9897 | 0.9923 | 0.0 | ❌ | 10000 | 9796 |
| 원가계산서_0310/노무비_값 | 1.0000 | 0.9970 | 0.9978 | 0.0 | ❌ | 10500 | 10438 |
| 원가계산서_0310/경비_값 | 1.0000 | 0.9990 | 0.9992 | 0.0 | ❌ | 10500 | 10479 |
| 원가계산서_0310/집계_값 | 1.0000 | 0.9982 | 0.9986 | 0.0 | ❌ | 14000 | 13949 |

## Comparison with Latest LLMs


| System | F1_micro | JSON/Struct Validity | Composite | Engine Delta |
|--------|----------|---------------------|-----------|-------------|
| **Engine (extraction)** | **0.9972** | **1.0** | **0.4986** | — |
| GPT-5.4 | 0.9140 | 100.0% | — | +0.0832 |
| Gemini 3.1 Pro | 0.8980 | 99.8% | — | +0.0992 |
| Claude Opus 4.6 | 0.8850 | 99.5% | — | +0.1122 |
| Qwen3.5-122B | 0.8670 | 98.9% | — | +0.1302 |
| GPT-5-Mini | 0.8420 | 100.0% | — | +0.1552 |
| Gemini 3.1 Flash | 0.8390 | 98.5% | — | +0.1582 |
| Llama-3.3-70B | 0.7910 | 94.2% | — | +0.2062 |
| Mistral Large 3 | 0.7650 | 93.8% | — | +0.2322 |

## Domain Difference Analysis (Auto-computed)

| Dimension | LLMStructBench (Original) | Engine (This Benchmark) |
|-----------|--------------------------|------------------------|
| **Input** | Natural language text (email/message) | XLSX (structured spreadsheet) |
| **Output** | JSON conforming to schema | XLSX conforming to template |
| **Schema** | JSON Schema (types, nesting, constraints) | Template structure (sections, columns, merges) |
| **Conversion** | Unstructured → structured | Semi-structured → structured |
| **Eval pairs** | Key:value in JSON object | Cell (sheet::col::row → value) |
| **DOC unit** | Document (email instance) | Sheet (재료비_값, 노무비_값, etc.) |

## F1_micro vs Production Cell-EM Reconciliation


| Metric | Value | Source |
|--------|-------|--------|
| **F1_micro (this benchmark)** | 0.9972 | LLMStructBench methodology |
| **DOC_micro (this benchmark)** | 0.0000 | Sheet-level correctness |
| **Composite** | 0.4986 | (1-λ)·F1 + λ·DOC |
| **Cell-EM (production)** | 0.9999 | D1-D5 validator (44 codes) |
| **Mapping Score (production)** | 0.973 | M1-M5 validator (14 codes) |

The **+0.0027** gap between F1_micro (0.9972) and production Cell-EM (0.9999) is explained by:

1. **Different metric definition**: F1_micro includes key existence (MK) and partial credit, while Cell-EM is strict cell-value exact match with tolerance

2. **DOC_micro strictness**: A sheet with even one wrong cell counts as 'not correct' in DOC, while Cell-EM averages across all cells

3. **Template structure bonus**: The engine structurally prevents schema violations (merge/format/formula), which Cell-EM captures but F1_micro doesn't fully reflect


## 3. Mapping — Detailed Analysis


## Error Profile — Mapping (Auto-computed)

> All values below are **computed from actual benchmark data**.

### Per-Sheet Breakdown


| Sheet | F1_keys | F1_values | F1_micro | DOC | Correct? | Total | Matched |
|-------|---------|-----------|----------|-----|----------|-------|---------|
| _test_af/원가계산서_골든셋 (merges: 74/75) | 0.2753 | 0.9231 | 0.7612 | 0.0 | ❌ | 131 | 91 |
| 원가계산서_0101/원가계산서_골든셋 (merges: 75/75) | 0.2857 | 0.9231 | 0.7638 | 0.0 | ❌ | 131 | 91 |
| 원가계산서_0227/원가계산서_골든셋 (merges: 75/75) | 0.1706 | 0.9287 | 0.7392 | 0.0 | ❌ | 131 | 90 |
| 원가계산서_0310/원가계산서_골든셋 (merges: 75/75) | 0.4233 | 0.9232 | 0.7982 | 0.0 | ❌ | 131 | 91 |
| 원가계산서_0406/원가계산서_골든셋 (merges: 75/75) | 0.5014 | 0.9458 | 0.8347 | 0.0 | ❌ | 131 | 87 |
| 원가계산서_0406/원가계산서_골든셋 (merges: 75/75) | 1.0000 | 1.0000 | 1.0000 | 1.0 | ✅ | 131 | 131 |

## Comparison with Latest LLMs


| System | F1_micro | JSON/Struct Validity | Composite | Engine Delta |
|--------|----------|---------------------|-----------|-------------|
| **Engine (mapping)** | **0.7949** | **1.0** | **0.4808** | — |
| GPT-5.4 | 0.9140 | 100.0% | — | -0.1191 |
| Gemini 3.1 Pro | 0.8980 | 99.8% | — | -0.1031 |
| Claude Opus 4.6 | 0.8850 | 99.5% | — | -0.0901 |
| Qwen3.5-122B | 0.8670 | 98.9% | — | -0.0721 |
| GPT-5-Mini | 0.8420 | 100.0% | — | -0.0471 |
| Gemini 3.1 Flash | 0.8390 | 98.5% | — | -0.0441 |
| Llama-3.3-70B | 0.7910 | 94.2% | — | +0.0039 |
| Mistral Large 3 | 0.7650 | 93.8% | — | +0.0299 |

## Domain Difference Analysis (Auto-computed)

| Dimension | LLMStructBench (Original) | Engine (This Benchmark) |
|-----------|--------------------------|------------------------|
| **Input** | Natural language text (email/message) | XLSX (structured spreadsheet) |
| **Output** | JSON conforming to schema | XLSX conforming to template |
| **Schema** | JSON Schema (types, nesting, constraints) | Template structure (sections, columns, merges) |
| **Conversion** | Unstructured → structured | Semi-structured → structured |
| **Eval pairs** | Key:value in JSON object | Cell (sheet::col::row → value) |
| **DOC unit** | Document (email instance) | Sheet (재료비_값, 노무비_값, etc.) |

## F1_micro vs Production Cell-EM Reconciliation


| Metric | Value | Source |
|--------|-------|--------|
| **F1_micro (this benchmark)** | 0.7949 | LLMStructBench methodology |
| **DOC_micro (this benchmark)** | 0.1667 | Sheet-level correctness |
| **Composite** | 0.4808 | (1-λ)·F1 + λ·DOC |
| **Cell-EM (production)** | 0.9999 | D1-D5 validator (44 codes) |
| **Mapping Score (production)** | 0.973 | M1-M5 validator (14 codes) |

The **+0.2050** gap between F1_micro (0.7949) and production Cell-EM (0.9999) is explained by:

1. **Different metric definition**: F1_micro includes key existence (MK) and partial credit, while Cell-EM is strict cell-value exact match with tolerance

2. **DOC_micro strictness**: A sheet with even one wrong cell counts as 'not correct' in DOC, while Cell-EM averages across all cells

3. **Template structure bonus**: The engine structurally prevents schema violations (merge/format/formula), which Cell-EM captures but F1_micro doesn't fully reflect


## 4. Notes


- **Methodology**: LLMStructBench (arXiv 2602.14743, Tenckhoff et al.). F1_micro (α=0.25 key, 0.75 value), DOC_micro (document-level), Composite (λ=0.5).

- **Fuzzy credit**: Levenshtein-based partial credit for string deviations (L_good=0.1, L_bad=2.0, γ=0.5). Numeric fields use domain tolerances (단가=0.01, 소요량=0.001, etc.).

- **Domain difference**: LLMStructBench evaluates NL text → JSON. Engine evaluates XLSX → XLSX (extraction) and XLSX → template XLSX (mapping). Cross-domain comparison is indicative, not definitive.

- **LLM sources**: `docs/260610_LLM_vs_CostReady_성능비교표.md` Section 3-4 (GPT-5.4, Claude Opus 4.6, Gemini 3.1 Pro, etc.).

- **Gap analysis**: All error profiles, per-sheet breakdowns, and comparisons are **fully auto-computed** from actual benchmark data.
