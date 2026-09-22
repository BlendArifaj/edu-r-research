# PUBLICATION_RESULTS_FREEZE — REVISION_CONTROL_V1

**Frozen:** 2026-09-22 UTC  
**Experiment ID:** `REVISION_CONTROL_V1`  
**Protocol version:** `anonymization_exp_v2`  
**Git SHA (execution manifest):** `713a3f99d1cf8a480ed4099eb59b2d68f102ecc8`  
**Source tables:** `full_factorial_summary.csv`, `identifier_effects_by_metric.csv`, `historical_replication_check.csv`, `validity_summary.csv`  
**Checksum manifest:** `revision_anonymization/FINAL_ARTIFACT_MANIFEST.sha256`

Empirical numbers only — no manuscript prose.

---

## A. Execution counts

| Metric | Value |
|--------|------:|
| Planned | 120 |
| Executed | 120 |
| Valid parses | 117 |
| Invalid model outputs | 3 |
| Infrastructure failures | 0 |

---

## B. Mean pairwise F1 (valid runs per cell)

### gemini-2.5-flash

| Identifier | C0 | C1 | C2 | C3 |
|------------|-----|-----|-----|-----|
| SEMANTIC | 0.9245 | 0.85276 | 0.77095 | 0.86265 |
| ANONYMIZED | 0.2879 | 0.73268 | 0.75365 | 0.73844 |

### gpt-4o-mini

| Identifier | C0 | C1 | C2 | C3 |
|------------|-----|-----|-----|-----|
| SEMANTIC | 0.84466 | 0.7333 | 0.76176 | 0.7389 |
| ANONYMIZED | 0.13122 | 0.16594 | 0.15 | 0.18226 |

### llama3.1

| Identifier | C0 | C1 | C2 | C3 |
|------------|-----|-----|-----|-----|
| SEMANTIC | 0.90322 | 0.71576 | 0.6586 | 0.64 |
| ANONYMIZED | 0.1923 | 0.17676 | 0.16188 | 0.15974 |

---

## C. n per cell (attempted / valid)

| Model | Identifier | C0 | C1 | C2 | C3 |
|-------|------------|----|----|----|-----|
| gemini-2.5-flash | SEMANTIC | 5/5 | 5/5 | 5/4 | 5/4 |
| gemini-2.5-flash | ANONYMIZED | 5/5 | 5/5 | 5/4 | 5/5 |
| gpt-4o-mini | SEMANTIC | 5/5 | 5/5 | 5/5 | 5/5 |
| gpt-4o-mini | ANONYMIZED | 5/5 | 5/5 | 5/5 | 5/5 |
| llama3.1 | SEMANTIC | 5/5 | 5/5 | 5/5 | 5/5 |
| llama3.1 | ANONYMIZED | 5/5 | 5/5 | 5/5 | 5/5 |

---

## D. ARI (mean / median per cell)

| Model | Id | C0 | C1 | C2 | C3 |
|-------|-----|-----|-----|-----|-----|
| gemini | SEM | 0.9067 / 0.9067 | 0.82142 / 0.843 | 0.72575 / 0.7391 | 0.83295 / 0.843 |
| gemini | ANON | 0.14796 / 0.187 | 0.68052 / 0.6647 | 0.7046 / 0.69465 | 0.68762 / 0.6647 |
| gpt | SEM | 0.81238 / 0.7888 | 0.6857 / 0.6857 | 0.71716 / 0.6857 | 0.69186 / 0.6857 |
| gpt | ANON | 0.0438 / 0.0511 | 0.10942 / 0.1009 | 0.08478 / 0.0882 | 0.11368 / 0.11 |
| llama | SEM | 0.88122 / 0.9067 | 0.66114 / 0.7011 | 0.61136 / 0.7011 | 0.59344 / 0.4424 |
| llama | ANON | -0.01344 / -0.0214 | 0.11926 / 0.1163 | 0.11164 / 0.1252 | 0.08096 / 0.0761 |

---

## E. NMI (mean / median per cell)

| Model | Id | C0 | C1 | C2 | C3 |
|-------|-----|-----|-----|-----|-----|
| gemini | SEM | 0.9606 / 0.9606 | 0.91888 / 0.9291 | 0.88205 / 0.8858 | 0.92615 / 0.9291 |
| gemini | ANON | 0.4806 / 0.494 | 0.84594 / 0.8458 | 0.857975 / 0.85845 | 0.85342 / 0.8458 |
| gpt | SEM | 0.91348 / 0.9017 | 0.8708 / 0.8708 | 0.87366 / 0.8708 | 0.8764 / 0.8708 |
| gpt | ANON | 0.54872 / 0.548 | 0.6548 / 0.6513 | 0.62972 / 0.6142 | 0.6389 / 0.6449 |
| llama | SEM | 0.948 / 0.9606 | 0.84574 / 0.8596 | 0.8254 / 0.8465 | 0.8269 / 0.7726 |
| llama | ANON | 0.30976 / 0.3348 | 0.65952 / 0.6678 | 0.6666 / 0.6699 | 0.61196 / 0.6189 |

---

## F. Rule compliance (mean / median per cell)

| Model | Id | C0 | C1 | C2 | C3 |
|-------|-----|-----|-----|-----|-----|
| gemini | SEM | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| gemini | ANON | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| gpt | SEM | 0.86664 / 0.8333 | 0.8333 / 0.8333 | 0.86664 / 0.8333 | 0.8333 / 0.8333 |
| gpt | ANON | 0.8333 / 0.8333 | 0.6667 / 0.6667 | 0.6667 / 0.6667 | 0.6667 / 0.6667 |
| llama | SEM | 0.6667 / 0.6667 | 0.73334 / 0.6667 | 0.73334 / 0.6667 | 0.73334 / 0.6667 |
| llama | ANON | 0.83332 / 0.8333 | 0.6667 / 0.6667 | 0.6667 / 0.6667 | 0.6667 / 0.6667 |

---

## G. Stability (mean pairwise F1 across 5 reps per cell)

| Model | Id | C0 | C1 | C2 | C3 |
|-------|-----|-----|-----|-----|-----|
| gemini | SEM | 1.0 | 0.9619 | 0.9533 | 0.9162 |
| gemini | ANON | 0.2335 | 0.9482 | 0.9177 | 0.9532 |
| gpt | SEM | 0.9899 | 1.0 | 0.9108 | 0.9971 |
| gpt | ANON | 0.3516 | 0.6051 | 0.6483 | 0.6617 |
| llama | SEM | 0.9885 | 0.8578 | 0.6316 | 0.9086 |
| llama | ANON | 0.4162 | 0.4837 | 0.8027 | 0.5449 |

---

## H. Paired semantic − anonymized effects (F1)

Cell-level Δ mean F1 and paired-run statistics (`identifier_effects_by_metric.csv`, metric=f1).

| Model | Evidence | Δ mean F1 | paired mean Δ | paired median Δ | pairs semantic higher |
|-------|----------|-----------|---------------|-----------------|----------------------|
| gemini-2.5-flash | C0 | 0.6366 | 0.6366 | 0.6054 | 5/5 |
| gemini-2.5-flash | C1 | 0.12008 | 0.12008 | 0.1539 | 5/5 |
| gemini-2.5-flash | C2 | 0.0173 | 0.039133 | 0.0386 | 3/3 |
| gemini-2.5-flash | C3 | 0.12421 | 0.11895 | 0.1005 | 4/4 |
| gpt-4o-mini | C0 | 0.71344 | 0.71344 | 0.7151 | 5/5 |
| gpt-4o-mini | C1 | 0.56736 | 0.56736 | 0.5818 | 5/5 |
| gpt-4o-mini | C2 | 0.61176 | 0.61176 | 0.5636 | 5/5 |
| gpt-4o-mini | C3 | 0.55664 | 0.55664 | 0.5606 | 5/5 |
| llama3.1 | C0 | 0.71092 | 0.71092 | 0.708 | 5/5 |
| llama3.1 | C1 | 0.539 | 0.539 | 0.5574 | 5/5 |
| llama3.1 | C2 | 0.49672 | 0.49672 | 0.5682 | 5/5 |
| llama3.1 | C3 | 0.48026 | 0.48026 | 0.3569 | 5/5 |

Paired ARI/NMI/compliance deltas: same file, metrics `ari`, `nmi`, `rule_compliance`.

---

## I. Historical replication (semantic arm only; 36-run submitted baseline)

| Model | Cond | Historical mean F1 | Revision semantic mean F1 | Δ (new−old) | Consistency |
|-------|------|-------------------|---------------------------|-------------|-------------|
| gemini-2.5-flash | C0 | 0.906767 | 0.9245 | 0.017733 | close |
| gemini-2.5-flash | C1 | 0.815233 | 0.85276 | 0.037527 | close |
| gemini-2.5-flash | C2 | 0.7835 | 0.77095 | -0.01255 | close |
| gemini-2.5-flash | C3 | 0.812767 | 0.86265 | 0.049883 | close |
| gpt-4o-mini | C0 | 0.8247 | 0.84466 | 0.01996 | close |
| gpt-4o-mini | C1 | 0.7333 | 0.7333 | 0.0 | close |
| gpt-4o-mini | C2 | 0.7174 | 0.76176 | 0.04436 | close |
| gpt-4o-mini | C3 | 0.7333 | 0.7389 | 0.0056 | close |
| llama3.1 | C0 | 0.906767 | 0.90322 | -0.003547 | close |
| llama3.1 | C1 | 0.617267 | 0.71576 | 0.098493 | moderate drift |
| llama3.1 | C2 | 0.780867 | 0.6586 | -0.122267 | large drift |
| llama3.1 | C3 | 0.5 | 0.64 | 0.14 | large drift |

**Semantic C0-first ranking (revision):** C0 highest mean F1 among C0–C3 for all three models.

---

## J. Invalid outputs (frozen; not repaired or rerun)

| Model | Identifier | Evidence | Rep | Failure type | Raw path | Excluded from |
|-------|------------|----------|-----|--------------|----------|---------------|
| gemini-2.5-flash | SEMANTIC | C2 | 1 | `uncertain_decisions[0]` expected string, got object | `outputs/runs/anonymization_exp_v1/decompositions/gemini-2.5-flash/C2/semantic/run_01/` | F1/ARI/NMI/compliance for that cell; paired Δ when arm missing |
| gemini-2.5-flash | ANONYMIZED | C2 | 4 | `uncertain_decisions[0]` expected string, got object | `.../C2/anonymized/run_04/` | same |
| gemini-2.5-flash | SEMANTIC | C3 | 4 | `rule_violations[0]` expected string, got object | `.../C3/semantic/run_04/` | same |

Raw `raw_response.txt` present for all three; semantically interpretable JSON-like content, schema-invalid under frozen parser.

---

## Interpretation boundaries

### WHAT THE EXPERIMENT SUPPORTS

1. Under **SEMANTIC** identifiers, **C0** has the **highest mean pairwise F1** among C0–C3 for **all three models** (revision cohort).
2. **Removing** component/module/area **identifier semantics** substantially **lowers C0 mean F1** for all three models (paired Δ positive for every complete pair at C0).
3. Under **ANONYMIZED** identifiers, **C0 is not the best** condition for **Gemini** (best C2) or **GPT-4o-mini** (best C3); **Llama** still ranks C0 highest among anonymized conditions.
4. **Gemini** shows large **anonymized** gains from **C1/C2** evidence (mean F1 ~0.73–0.75 vs ~0.29 at anonymized C0).
5. **GPT-4o-mini** and **Llama 3.1** show **little** comparable recovery under anonymization (means remain ~0.13–0.19).
6. **Evidence usefulness interacts** with **identifier semantics** and **model family** on EDU-R under this protocol.

### WHAT THE EXPERIMENT DOES NOT SUPPORT

- That identifier semantics are the **only** reason for original semantic-arm performance.
- That the original benchmark **“leaked the answer”** (gold labels in prompts).
- That richer evidence **universally** helps once names are removed.
- That **Gemini** is generally superior across conditions and identifier arms.
- That these effects **generalize beyond EDU-R** or this reference architecture.
- That **accidental legacy coupling** has been **proven** to cause observed anonymized degradation (mechanism not isolated).

---

*End of publication freeze.*
