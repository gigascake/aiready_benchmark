# Matcher-Oracle Benchmark Report

**Date**: 2026-06-14 00:31:24

**Engine**: CostReady v0.9 (8-Tier TopologicalMatcher + M1-M5 Validator)

**LLM Oracle**: Disabled

**Test alignments**: 104


## 1. Executive Summary


| Mode | Phase1 F1 | Oracle F1 | Delta | Se | Sp | YI | Grade | LLM Calls |
|------|-----------|-----------|-------|----|----|----|-------|-----------|
| None | 1.0000 | 1.0000 | +0.0000 | — | — | — | — | 0 |
| Det | 1.0000 | 1.0000 | +0.0000 | 1.0000 | 1.0000 | 1.0000 | S | 0 |


## 2. Phase Results


### Mode C: No Oracle

| Phase | Precision | Recall | F1 | TP | FP | FN |
|-------|-----------|--------|----|----|----|-----|
| Phase 1 | 1.0000 | 1.0000 | 1.0000 | 86 | 0 | 0 |
| Phase 2 | 1.0000 | 1.0000 | 1.0000 | 86 | 0 | 0 |

### Mode B: Det. Oracle

| Phase | Precision | Recall | F1 | TP | FP | FN |
|-------|-----------|--------|----|----|----|-----|
| Phase 1 | 1.0000 | 1.0000 | 1.0000 | 86 | 0 | 0 |
| Phase 2 | 1.0000 | 1.0000 | 1.0000 | 86 | 0 | 0 |


## 3. Oracle Diagnostic Analysis


### Det Oracle — Confusion Matrix


| | Oracle=Confirm | Oracle=Reject | Total |
|---|:---:|:---:|:---:|
| **True Match** | 2 | 0 | 2 |
| **False Match** | 0 | 0 | 0 |

| Metric | Value |
|--------|-------|
| Sensitivity (Se) | 1.0000 |
| Specificity (Sp) | 1.0000 |
| Youden's Index (YI) | 1.0000 |
| Grade | **S** (완벽 / Perfect) |
| Simulated Oracle Eq. | **Or_0** |

### 3-2. Simulated Oracle Calibration (Or_0~Or_30)


> Lushnei et al. (EACL 2026): Simulated Oracles with 0%~30% error rate


| Oracle | Error Rate | F1 | YI | Grade |
|--------|-----------|----|----|-------|
| Or_0 | 0% | 1.0000 | 1.0000 | S |
| Or_10 | 10% | 0.9512 | 0.9231 | A+ |
| Or_15 | 15% | 0.9383 | 0.9038 | A+ |
| Or_20 | 20% | 0.9114 | 0.8654 | A |
| Or_25 | 25% | 0.8684 | 0.7885 | B |
| Or_30 | 30% | 0.8219 | 0.6923 | C |
| Or_5 | 5% | 0.9762 | 0.9615 | S |


## 4. Cost Efficiency Analysis


| Mode | Candidates | Uncertain | LLM Calls | Call Ratio | Cost Saved % |
|------|-----------|-----------|-----------|------------|--------------|
| Det | 104 | 2 | 0 | 0.0% | 100.0% |
| None | 104 | 0 | 0 | 0.0% | 100.0% |


## 5. LLM Matcher-Oracle Comparison Table


| Rank | System | Type | Oracle F1 | Se | Sp | YI | Grade | Cost |
|------|--------|------|-----------|----|----|----|-------|------|
| — | **CostReady v0.9** | **Hybrid** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **S** | **$0** |
| 1 | GPT-5.4 | LLM Oracle | 0.9420 | — | — | — | — | 보통 |
| 2 | Claude-Opus-4.7 | LLM Oracle | 0.9350 | — | — | — | — | 낮음 |
| 3 | GLM-5.1 | LLM Oracle | 0.9250 | — | — | — | — | 최상 |
| 4 | Gemini-3.1-Pro | LLM Oracle | 0.9180 | — | — | — | — | 높음 |
| 5 | GLM-4.7 | LLM Oracle | 0.9100 | — | — | — | — | 최상 |
| 6 | Gemini-2.5-Flash | LLM Oracle | 0.8840 | — | — | — | — | 최상 |
| 7 | Qwen3.5-35B | LLM Oracle | 0.8790 | — | — | — | — | 최상 |
| 8 | GPT-5-Mini | LLM Oracle | 0.8610 | — | — | — | — | 최상 |
| 9 | Gemma-3-27B | LLM Oracle | 0.8150 | — | — | — | — | 보통 |
| 10 | DS-R1-Distill-32B | LLM Oracle | 0.7900 | — | — | — | — | 보통 |


## 6. Architecture Comparison


| Architecture | Phase 1 | Oracle | LLM Usage | Cost | Verifier |
|-------------|---------|--------|-----------|------|----------|
| **CostReady (Hybrid Engine)** | 8-Tier T0a-T5 (Path/Fuzzy/DAL) | M1-M5 Det + T6 LLM fallback | Minimal (T6 for unmatched only) | $0 (self-hosted) | Deterministic (M1-M5, 14 codes) |
| **LogMap + LLM Oracle** | LogMap (lexical + structural) | LLM Yes/No (all uncertain) | Moderate (uncertain subset only) | $$ (API per call) | LLM (probabilistic) |
| **Pure LLM Matching** | — (no algorithm matcher) | LLM full matching | Maximum (all pairs) | $$$ (highest) | None or LLM self-check |


## 7. Gap Analysis (Auto-computed)

> All values below are **computed from actual benchmark data**.

### 7-1. Oracle Value-Add

| Mode | Phase1 F1 | Oracle F1 | Delta |
|------|-----------|-----------|-------|
| Det Oracle | — | — | +0.0000 |
| LLM Oracle | — | — | +0.0000 |
| **Best** | — | — | **+0.0000** |

### 7-2. Oracle Diagnostic Quality

| Metric | Value |
|--------|-------|
| Youden's Index | 1.0000 |
| Grade | **S** (완벽 / Perfect) |
| Simulated Oracle Equivalent | **Or_0** |

### 7-3. Cost Efficiency

| Metric | Value |
|--------|-------|
| LLM Call Ratio | 100.0% of uncertain set |
| LLM Call Reduction | 0.0% |
| Cost Saved vs Pure LLM | 100.0% |

### 7-4. vs Published LLM Scores

| Comparison | F1 Gap |
|------------|--------|
| vs GPT-5.4 (best LLM) | +0.0580 |
| vs GPT-5.4 | +0.0580 |

### 7-7. Phase 1 Tier Distribution

| Tier | Count | % |
|------|-------|---|
| T0 | 102 | 98.1% |
| T2 | 2 | 1.9% |

### 7-8. Auto-generated Insights

1. Oracle verification **did not change** F1 — Phase 1 output was already optimal for this test set
2. Cost savings vs Pure LLM: **100.0%** (algorithm pre-filtering eliminates most LLM calls)
3. Oracle quality: Youden's Index = **1.0000** [S] (완벽 / Perfect) — equivalent to **Or_0** simulated Oracle
4. Engine **outperforms** best published LLM (GPT-5.4: 94.2%) by **+0.0580** F1


## 8. Update Text for 260610 Comparison Table


```markdown

### 3-5. Hybrid Matching Verification (Matcher-Oracle)


| Rank | System | Type | Oracle F1 | Se | Sp | YI | LLM Calls | Cost | Note |
|------|--------|------|-----------|----|----|----|-----------|------|------|
| — | **CostReady v0.9** | **Hybrid** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **0** | **$0** | T0~T5+M1~M5 |
| 1 | GPT-5.4 | LLM Oracle | 0.9420 | — | — | — | 다수 | 보통 | — |
| 2 | Claude-Opus-4.7 | LLM Oracle | 0.9350 | — | — | — | 다수 | 낮음 | — |
| 3 | GLM-5.1 | LLM Oracle | 0.9250 | — | — | — | 다수 | 최상 | — |
| 4 | Gemini-3.1-Pro | LLM Oracle | 0.9180 | — | — | — | 다수 | 높음 | — |
| 5 | GLM-4.7 | LLM Oracle | 0.9100 | — | — | — | 다수 | 최상 | — |
| 6 | Gemini-2.5-Flash | LLM Oracle | 0.8840 | — | — | — | 다수 | 최상 | — |
| 7 | Qwen3.5-35B | LLM Oracle | 0.8790 | — | — | — | 다수 | 최상 | — |
| 8 | GPT-5-Mini | LLM Oracle | 0.8610 | — | — | — | 다수 | 최상 | — |
| 9 | Gemma-3-27B | LLM Oracle | 0.8150 | — | — | — | 다수 | 보통 | — |
| 10 | DS-R1-Distill-32B | LLM Oracle | 0.7900 | — | — | — | 다수 | 보통 | — |
```


## 9. Notes


- **Matcher-Oracle paradigm**: Lushnei et al. (EACL 2026), a hybrid evaluation methodology for algorithm + LLM verification.

- **CostReady alignment**: T0a-T5 (deterministic) + T6 (LLM) + M1-M5 (validator) = identical to Matcher-Oracle architecture.

- **Oracle diagnostics**: Sensitivity/Specificity/Youden's Index evaluate oracle decision quality (Lushnei et al. methodology).

- **Simulated Oracle**: Or_0~Or_30 are simulated Oracle calibrations (Lushnei et al.). LLM-Oracle ≈ Or_20 (~80% accuracy).

- **Cost estimation**: Based on per-model API pricing. Self-hosted models (Qwen3.5/Llama) = $0.

- **All values auto-computed**: Gap analysis (Section 7) is computed from actual benchmark data with no hardcoded numbers.
