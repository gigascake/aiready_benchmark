# Cost Ready vs AI Ready 모드 — 통합 벤치마크 결과

**날짜**: 2026-06-30 17:21 KST  
**브랜치**: 14_Generation  
**총 실행 시간**: ~9초 (6 AI Ready 케이스 + Cost Ready 3개 벤치마크)

---

## 1. 요약 / Executive Summary

```
  구분         검증항목              결과       비고
  ──────────   ──────────────────   ──────   ────────────────────────
  🏭 Cost Ready
               OAEI 필드 매칭 F1   1.0000   TP=86 FP=0 FN=0
               LLMStructBench        0.9972   셀 추출 F1_micro
               LLMStructBench        0.7949   셀 맵핑 F1_micro
               Matcher-Oracle F1     1.0000   Grade=S (Det)
  
  🤖 AI Ready
               V1-V5 추출품질 avg    99.9%    Grade=S (6케이스)
               C1-C5 정합성 avg      1.0000   pass_rate=100%
               ValueBench L3 avg     0.9982   의미적 타당성
               ValueBench L5 avg     0.9681   추적성
  
```

---

## 2. Cost Ready 모드 (원가계산서)

### 2-1. OAEI — 필드 매칭 F1 (T0a-T5)

```
  Precision:   1.0000
  Recall:      1.0000
  F1:          1.0000
  TP=86  FP=0  FN=0
```

- 원가계산서 6개 템플릿(원가계산서_0101~0406, samp_05, samp_test) 전체 86개 정렬 완벽 매칭
- FP=0, FN=0 → 매칭 오류 없음

### 2-2. LLMStructBench — 셀 추출/맵핑 F1

```
  추출 F1_micro:  0.9972  (99.72%)
  맵핑 F1_micro:  0.7949  (79.49%)
```

- 추출(Extraction) 단계는 거의 완벽(99.7%)
- 맵핑(Mapping) 단계는 헤더 매칭 불일치로 일부 손실 발생
- 원가계산서는 정형 테이블이므로 추출은 잘 되지만, 맵핑 컬럼명이 정답지와 다를 수 있음

### 2-3. Matcher-Oracle — 2-Phase 매칭 검증

```
  Phase1 F1:   1.0000
  Phase2 F1:   1.0000
  Grade:       S
  Mode:        Det (Deterministic)
```

- Phase1(구조 기반)과 Phase2(Oracle) 모두 F1=1.0
- Det 모드에서 완벽 → LLM 불필요한 케이스

### 2-4. TEDS — 표 편집 거리

- Cost Ready TEDS: 정답지(right_files)와 매핑 결과(custom_files_3_5) 비교
- 정렬이 복잡해 simple-row 기반 TEDS는 생략

---

## 3. AI Ready 모드 (다중 포맷)

### 3-1. V1-V5 추출품질검증 (6개 포맷)

```
  케이스              V1(완전성)  V2(무결성)  V3(구조)  V4(RoundTrip)  총점
  ────────────────   ─────────   ─────────   ───────   ───────────   ──────
  NextRise (PDF)      100.0       100.0        99.0       100.0    99.8%
  전략적기술 (DOCX)    100.0       100.0       100.0       100.0   100.0%
  공고 (PDF)           100.0       100.0       100.0       100.0   100.0%
  저작권 (HWP)         100.0       100.0        97.6       100.0    99.6%
  하람AI (HWPX)        100.0       100.0       100.0       100.0   100.0%
  신AI (XLSX)          100.0       100.0       100.0       100.0   100.0%
  ────────────────   ─────────   ─────────   ───────   ───────────   ──────
  평균                            99.9%         Grade=S
```

**세부 분석:**

- **V1 완전성**: 모든 케이스 100% — MD 섹션 수 = XLSX 시트 수, 빈 시트 없음
- **V2 무결성**: 모든 케이스 100% — null/인코딩깨짐/타입불일치 0건
- **V3 구조**: 
  - NextRise (PDF) 99.0% — 약간의 행 길이 편차 (INFO)
  - 저작권 (HWP) 97.6% — 행 길이 편차 존재
  - 나머지 100% — 시트명/헤더/행길이 모두 안정적
- **V4 RoundTrip**: 모든 케이스 100% — MD 원본과 맵핑.xlsx 셀 일치율 완벽

### 3-2. C1-C5 정합성검증 (toDB)

```
  케이스              점수    pass_gate   CRITICAL
  ────────────────   ──────   ─────────   ────────
  NextRise (PDF)      1.0000       O        0
  전략적기술 (DOCX)    1.0000       O        0
  공고 (PDF)           1.0000       O        0
  저작권 (HWP)         1.0000       O        0
  하람AI (HWPX)        1.0000       O        0
  신AI (XLSX)          1.0000       O        0
  ────────────────   ──────   ─────────   ────────
  평균: 1.0000   pass_rate: 100%   Grade=S
```

- 6개 케이스 전체 pass_gate=O, CRITICAL 0건
- toDB 정합성 완벽 — 스키마/구조/행대수/크로스로우/DB준비도 모두 만족

### 3-3. ValueBench — L3/L5 값검증

```
  L3: 의미적 타당성 (Semantic Plausibility)
  L5: MD 추적성 (Traceability from MD source)
  
  케이스              L3(의미)    L5(추적성)    traceable/total
  ────────────────   ────────   ────────    ───────────────
  NextRise (PDF)      1.0000       0.9095       3919/4309
  전략적기술 (DOCX)    1.0000       1.0000        107/107
  공고 (PDF)           0.9967       1.0000        301/301
  저작권 (HWP)         0.9926       0.8992       1820/2024
  하람AI (HWPX)        1.0000       1.0000         88/88
  신AI (XLSX)          1.0000       1.0000        209/209
  ────────────────   ────────   ────────    ───────────────
  평균               0.9982       0.9681
```

**세부 분석:**

- **L3 의미적 타당성**: 평균 99.82% — 모든 케이스에서 값의 의미적 일관성 검증 통과
- **L5 추적성**: 평균 96.81%
  - NextRise: 90.95% — 대규모 데이터(4309셀) 중 390셀이 MD에서 추적 불가
  - 저작권(HWP): 89.92% — HWP 문서 구조 특성상 일부 셀 위치 정보 손실
  - DOCX/HWPX/XLSX/PDF(소규모): 100% — 포맷 구조가 선명하여 완전 추적

---

## 4. 모드 간 비교 분석

```
  비교항목               Cost Ready     AI Ready    胜出方
  ────────────────────   ──────────     ────────     ──────
  필드매칭 F1            1.0000          —       Cost Ready
  셀추출 F1              0.9972          —       Cost Ready
  셀맵핑 F1              0.7949          —       Cost Ready
  Oracle 매칭 F1         1.0000          —       Cost Ready
  추출품질 (V1-V5)        —            99.9%     AI Ready
  정합성 (C1-C5)          —            100%      AI Ready
  의미적타당성 (L3)       —            99.82%    AI Ready
  추적성 (L5)             —            96.81%    AI Ready
```

### 핵심 인사이트

1. **Cost Ready(원가계산서)는 매칭 F1이 더 우수**
   - 정형 원가계산서는 템플릿 기반 매칭이 매우 효과적
   - OAEI 필드 매칭 F1=1.0, Matcher-Oracle F1=1.0
   - 단, 셀맵핑 F1=0.79로 컬럼명 불일치 문제 존재

2. **AI Ready(다중 포맷)는 품질 검증이 더 포괄적**
   - V1-V5 추출품질 99.9% — PDF/DOCX/HWP/HWPX/XLSX 모두 S등급
   - C1-C5 정합성 100% pass — toDB 준비도 완벽
   - ValueBench L3=99.8%, L5=96.8% — 값 검증도 견고

3. **포맷별 AI Ready 품질 차이**
   - DOCX/HWPX/XLSX: 모든 지표 100% — 구조가 명확
   - PDF: V3=99%, L5=90% — PDF 레이아웃 분석에서 미세 손실
   - HWP: V3=97.6%, L5=90% — HWP 형식 특성상 일부 열/행 위치 정보 손실

4. **실행 효율성**
   - 6개 AI Ready 케이스 전체 V1-V5+C1-C5+ValueBench: ~9초
   - Cost Ready 3개 벤치마크: OAEI ~15초
   - 전체: 분 단위 이내 — 대용량 벤치마크에도 실용적

---

## 5. 결론

```
  Cost Ready 모드:  필드/셀 매칭에 특화. 원가계산서 정형 데이터에 최적.
                    F1=1.0(매칭) / 0.997(추출) / 0.795(맵핑)
  
  AI Ready 모드:    다중 포맷 품질 검증에 특화. PDF/DOCX/HWP/HWPX/XLSX 모두 S등급.
                    V1-V5=99.9% / C1-C5=100% / L3=99.8% / L5=96.8%
  
  요약: 두 모드 서로 보완적.
       Cost Ready = 정형 원가계산서 매칭 정확도
       AI Ready   = 불규칙 다중 포맷 품질/정합성/추적성
```

---

*결과 JSON: ai_ready/benchmark/results/separate_combined_benchmark.json*
