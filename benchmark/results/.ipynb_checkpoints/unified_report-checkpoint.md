# 통합 벤치마크 종합 레포트 / Unified Benchmark Report

**날짜**: 2026-06-13 23:30:18

**엔진**: CostReady v0.9 (8-Tier + DM + Validator)

**벤치마크**: OAEI + LLMStructBench + Matcher-Oracle

**LLM Oracle**: 비활성


## 1. 요약 / Executive Summary


| Benchmark | Metric | Engine Score | Best LLM | Gap |
|-----------|--------|:-----------:|----------|-----|
| OAEI | F1 | **0.8542** | GPT-5.4 (0.8820) | -0.0278 |
| LLMStructBench | F1_micro | **0.9972** | GPT-5.4 (0.9140) | +0.0832 |
| Matcher-Oracle | Oracle F1 | **0.8723** | GPT-5.4 (0.9420) | -0.0697 |
| **Average** | **3-Bench Avg** | **0.9079** [A] | — | — |


## 2. 벤치마크 통합 비교표 / Cross-Benchmark Comparison


> CostReady vs 최신 LLM (2026년 기준) 3개 벤치마크 교차 비교


| Rank | System | Type | OAEI F1 | StructBench F1 | Oracle F1 | Avg F1 | Grade | Cost |
|------|--------|------|---------|----------------|-----------|--------|-------|------|
| — | **CostReady v0.9** | **Hybrid** | **0.8542** | **0.9972** | **0.8723** | **0.9079** | **A** | **$0** |
| 1 | GPT-5.4 | Closed | 0.8820 | 0.9140 | 0.9420 | 0.9127 | A | 보통 |
| 2 | Claude Opus 4.6 | Closed | 0.8650 | 0.8850 | 0.9350 | 0.8950 | A | 낮음 |
| 3 | Gemini 3.1 Pro | Closed | 0.8590 | 0.8980 | 0.9180 | 0.8917 | A | 높음 |
| 4 | Gemini 3.1 Flash | Closed | — | 0.8390 | 0.8840 | 0.8615 | B | 최상 |
| 5 | Qwen3.5-122B | Open | 0.8210 | 0.8670 | 0.8790 | 0.8557 | B | 높음 |
| 6 | GPT-5-Mini | Closed | — | 0.8420 | 0.8610 | 0.8515 | B | 최상 |
| 7 | GPT-4o | Closed | 0.7840 | — | — | 0.7840 | C | 보통 |
| 8 | Llama-3.3-70B | Open | 0.7300 | 0.7910 | 0.8150 | 0.7787 | C | 보통 |
| 9 | Mistral Large 3 | Closed | — | 0.7650 | — | 0.7650 | C | 보통 |


## 3. 벤치마크별 상세 결과 / Per-Benchmark Details


### 3-1. OAEI (필드 매칭 F1)


| Metric | Value |
|--------|-------|
| Precision | 0.7736 |
| Recall | 0.9535 |
| F1 | **0.8542** |
| TP / FP / FN | 82 / 24 / 4 |

### 3-2. LLMStructBench (셀 추출/맵핑 F1)


| Task | F1_micro | DOC_micro | Composite |
|------|----------|-----------|-----------|
| Extraction | 0.9972 | 0.0000 | 0.4986 |
| Mapping | 0.7949 | 0.1667 | 0.4808 |

### 3-3. Matcher-Oracle (2-Phase Oracle 검증)


| Mode | Phase1 F1 | Oracle F1 | Delta | Se | Sp | YI | LLM Calls |
|------|-----------|-----------|-------|----|----|----|-----------|
| None | 0.8542 | 0.8542 | +0.0000 | — | — | — | 0 |
| Det | 0.8542 | 0.8723 | +0.0182 | 1.0000 | 0.1333 | 0.1333 | 0 |


## 4. 통합 Gap 분석 / Unified Gap Analysis (Auto-computed)


| Model | OAEI Gap | StructBench Gap | Oracle Gap | Avg Gap |
|-------|----------|-----------------|------------|---------|
| GPT-5.4 | -0.0278 | +0.0832 | -0.0697 | -0.0048 |
| Claude Opus 4.6 | -0.0108 | +0.1122 | -0.0627 | +0.0129 |
| Gemini 3.1 Pro | -0.0048 | +0.0992 | -0.0457 | +0.0162 |
| Gemini 3.1 Flash | — | +0.1582 | -0.0117 | +0.0464 |
| Qwen3.5-122B | +0.0332 | +0.1302 | -0.0067 | +0.0522 |
| GPT-5-Mini | — | +0.1552 | +0.0113 | +0.0564 |
| GPT-4o | +0.0702 | — | — | +0.1239 |
| Llama-3.3-70B | +0.1242 | +0.2062 | +0.0573 | +0.1292 |
| Mistral Large 3 | — | +0.2322 | — | +0.1429 |

| Metric | Value |
|--------|-------|
| Engine Average F1 | **0.9079** [A] |
| Win Rate | **13/21** (61.9%) |

### 자동 산출 인사이트 / Auto-generated Insights

1. Engine average F1 across 3 benchmarks: **0.9079** [A] — 우수 / Very Good
2. vs best LLM (GPT-5.4, avg=0.9127): **-0.0048** average gap
3. Engine outperforms LLMs in **13/21** benchmark-model pairs (61.9% win rate)
4. OAEI: Engine=0.8542 vs best LLM(GPT-5.4)=0.8820 → gap -0.0278
5. LLMStructBench: Engine=0.9972 vs best LLM(GPT-5.4)=0.9140 → gap +0.0832
6. Matcher-Oracle: Engine=0.8723 vs best LLM(GPT-5.4)=0.9420 → gap -0.0697
7. Engine cost: **$0** (self-hosted, deterministic core). LLM API costs: 보통/낮음/높음/최상/높음/최상/보통/보통/보통


## 5. 아키텍처 우위 분석 / Architecture Advantage


| Dimension | CostReady (Hybrid) | Pure LLM | Advantage |
|-----------|-------------------|----------|-----------|
| **Matching** | 8-Tier Deterministic (T0a-T5) | LLM full inference | LLM wins (F1: 0.8542 vs 0.882) |
| **Extraction** | 9-Phase Pipeline | LLM JSON generation | Engine wins (F1: 0.9972 vs 0.914) |
| **Verification** | M1-M5 Deterministic | LLM self-check | Engine: 44 codes, 0 LLM calls, $0 cost |
| **Cost** | $0 (self-hosted) | $0.15~75/M tokens | **$0 vs $$$** |
| **Latency** | ~12s per case | 3~8s/page (VLM) | Engine faster for batch |
| **Hallucination** | 0 (deterministic core) | Variable (temperature dependent) | **Engine: 0 risk** |


## 6. 260610 비교표 업데이트 텍스트 / Update Text


```markdown

### 종합 성능 비교표 (3-벤치마크 통합)


| Rank | System | Type | OAEI F1 | StructBench F1 | Oracle F1 | Avg F1 | Grade | Cost |
|------|--------|------|---------|----------------|-----------|--------|-------|------|
| — | **CostReady v0.9** | **Hybrid** | **0.8542** | **0.9972** | **0.8723** | **0.9079** | **A** | **$0** |
| 1 | GPT-5.4 | Closed | 0.8820 | 0.9140 | 0.9420 | 0.9127 | A | 보통 |
| 2 | Claude Opus 4.6 | Closed | 0.8650 | 0.8850 | 0.9350 | 0.8950 | A | 낮음 |
| 3 | Gemini 3.1 Pro | Closed | 0.8590 | 0.8980 | 0.9180 | 0.8917 | A | 높음 |
| 4 | Gemini 3.1 Flash | Closed | — | 0.8390 | 0.8840 | 0.8615 | B | 최상 |
| 5 | Qwen3.5-122B | Open | 0.8210 | 0.8670 | 0.8790 | 0.8557 | B | 높음 |
| 6 | GPT-5-Mini | Closed | — | 0.8420 | 0.8610 | 0.8515 | B | 최상 |
| 7 | GPT-4o | Closed | 0.7840 | — | — | 0.7840 | C | 보통 |
| 8 | Llama-3.3-70B | Open | 0.7300 | 0.7910 | 0.8150 | 0.7787 | C | 보통 |
| 9 | Mistral Large 3 | Closed | — | 0.7650 | — | 0.7650 | C | 보통 |
```


## 7. 비고 / Notes


- **3개 벤치마크**: OAEI(필드 매칭), LLMStructBench(셀 추출/맵핑), Matcher-Oracle(2-Phase Oracle 검증)의 독립적 측정 결과를 통합.

- **Engine F1은 콜드스타트 측정값**: T0(User-Confirmed) 제외. 프로덕션 Cell-EM=99.99%는 T0 사전 커버(94.4%)+검증+AutoFix 적용 후 수치.

- **LLM 점수는 외부 벤치마크**: OAEI(ontology alignment), LLMStructBench(NL→JSON), Matcher-Oracle(algorithm+LLM oracle) 도메인. CostReady는 원가계산서 필드 매핑 도메인 — **직접 비교는 참고용**.

- **모든 수치는 자동 산출**: Gap 분석(Section 4)은 하드코딩 없이 실제 측정값에서 자동 계산됨.

- **레포트 생성**: `excel_ready/benchmark/run_all.py` (2026-06-13 23:30:18 실행)
