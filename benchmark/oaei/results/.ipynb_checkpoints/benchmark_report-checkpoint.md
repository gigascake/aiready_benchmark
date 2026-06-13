# OAEI Benchmark Report: Engine vs Published Systems

**Date**: 2026-06-13 21:58:27

**Mode**: Deterministic only (T0a-T5)

**Test cases**: 2


## 1. Engine Performance


| Case | Precision | Recall | F1 | TP | FP | FN |
|------|-----------|--------|----|----|----|----|
| 원가계산서_0101 | 0.7736 | 0.9535 | 0.8542 | 41 | 12 | 2 |
| 원가계산서_0227 | 0.7736 | 0.9535 | 0.8542 | 41 | 12 | 2 |
| **Micro-Average** | **0.7736** | **0.9535** | **0.8542** | **82** | **24** | **4** |


## 2. Comparison with OAEI 2024 Systems


### Conference Track (rar2-M3)

| System | Precision | Recall | F1 |
|--------|-----------|--------|----|
| **Engine (Deterministic)** | **0.7736** | **0.9535** | **0.8542** |
| LogMap | 0.7600 | 0.5600 | 0.6400 |
| Matcha | 0.6600 | 0.6300 | 0.6400 |
| MDMapper | 0.6600 | 0.5300 | 0.5900 |
| ALIN | 0.8200 | 0.4400 | 0.5700 |
| LogMapLt | 0.6800 | 0.4700 | 0.5600 |
| OntoMatch | 0.8200 | 0.4300 | 0.5600 |
| edna (baseline) | 0.7400 | 0.4500 | 0.5600 |
| StringEquiv (baseline) | 0.7600 | 0.4100 | 0.5300 |
| TOMATO | 0.5700 | 0.4200 | 0.4800 |


### Anatomy Track

| System | Precision | Recall | F1 |
|--------|-----------|--------|----|
| **Engine (Deterministic)** | **0.7736** | **0.9535** | **0.8542** |
| Matcha | 0.951 | 0.931 | 0.941 |
| MDMapper | 0.926 | 0.881 | 0.903 |
| LogMapBio | 0.888 | 0.908 | 0.898 |
| LogMap | 0.917 | 0.848 | 0.881 |
| ALIN | 0.984 | 0.750 | 0.851 |
| LogMapLt | 0.962 | 0.728 | 0.828 |
| TOMATO | 0.955 | 0.360 | 0.523 |


## 3. Comparison with LLM-Based Systems


| System | Track | Precision | Recall | F1 |
|--------|-------|-----------|--------|----|
| **Engine (Deterministic)** | **Cost Doc** | **0.7736** | **0.9535** | **0.8542** |
| LLaMA-2 (MI-EMMO) | MSE | 0.9666 | 0.9206 | 0.9430 |
| GPT-3.5 (Nell-DBpedia) | CommonKG | 1.0000 | 0.8914 | 0.9426 |
| LLaMA-2 (YAGO-Wikidata) | CommonKG | 1.0000 | 0.8552 | 0.9219 |
| Mistral (DOID-ORDO) | Phenotype | 0.8579 | 0.9426 | 0.8983 |
| GPT-3.5 (Anatomy) | Anatomy | 0.9082 | 0.8746 | 0.8911 |
| Mistral (HP-MP) | Phenotype | 0.7667 | 0.9540 | 0.8501 |
| GPT-3.5 (NCIT-DOID) | Bio-ML | 0.8619 | 0.8006 | 0.8301 |
| Agent-OM (GPT-4o) | Conference (subset) | 0.8900 | 0.8500 | 0.8700 |
| OLaLa (LLaMA-2) | Biodiversity (Fungi) | — | — | 0.8000 |
| CANARD 2024 (Stella-base) | Complex Matching (Conference) | 0.3890 | — | 0.6230 |
| CANARD 2024 (GritLM-7B) | Complex Matching (Conference) | 0.3590 | — | 0.6790 |
| LLMap (Flan-T5) | Conference | — | — | — |


## 4. Summary


| Category | Best F1 | Engine F1 | Delta |
|----------|---------|-----------|-------|
| OAEI 2024 Conference | 0.6400 | 0.8542 | +0.2142 |
| OAEI 2024 Anatomy | 0.9410 | 0.8542 | -0.0868 |
| LLMs4OM (best) | 0.9430 | 0.8542 | -0.0888 |


## 5. Notes


- **Domain difference**: Engine evaluates on cost document field mapping (Korean cost analysis reports), while OAEI benchmarks use ontology alignment (conference, anatomy, biomedical, etc.). Direct comparison is indicative, not definitive.

- **Reference alignment**: User-confirmed mappings from `mapping_rules_store.json` serve as gold standard (human-validated source→target field correspondences).

- **Matching tiers**: T0a (Path-Exact) → T5 (Leaf Fuzzy) are deterministic; T6 (LLM Semantic) is optional.

- **OAEI sources**: Conference/Anatomy/KG from OAEI 2024 Results Paper (ceur-ws.org/Vol-3897/oaei2024_paper0.pdf).

- **LLM sources**: LLMs4OM (ESWC 2024), Agent-OM (VLDB 2024), CANARD 2024 (OAEI Complex Matching).
