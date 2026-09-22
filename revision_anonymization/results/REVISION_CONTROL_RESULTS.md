# REVISION_CONTROL_V1 — analysis report

Generated from `run_level_results.csv` and related artifacts (no LLM calls).

## 1. Execution summary

| Metric | Count |
|--------|------:|
| Planned | 120 |
| Executed | 120 |
| Valid parses | 117 |
| Invalid model outputs | 3 |
| Infrastructure failures | 0 |

## 2. Provenance

- Git SHA (manifest): `713a3f99d1cf8a480ed4099eb59b2d68f102ecc8`
- Cohort: `REVISION_CONTROL_V1` (120 contemporaneous runs; historical 36 excluded from primary analysis)
- Outputs: `outputs/runs/anonymization_exp_v1/`
- Llama digest: `46e0c10c039e` (`llama_digest_frozen.txt`)

## 3. Full C0–C3 matrix (mean F1)

Compact view; full metrics in `full_factorial_summary.csv`.

| Model | Identifier | C0 | C1 | C2 | C3 |
|-------|------------|-----|-----|-----|-----|
| gemini-2.5-flash | SEMANTIC | 0.9245 | 0.85276 | 0.77095* (4/5) | 0.86265* (4/5) |
| gemini-2.5-flash | ANONYMIZED | 0.2879 | 0.73268 | 0.75365* (4/5) | 0.73844 |
| gpt-4o-mini | SEMANTIC | 0.84466 | 0.7333 | 0.76176 | 0.7389 |
| gpt-4o-mini | ANONYMIZED | 0.13122 | 0.16594 | 0.15 | 0.18226 |
| llama3.1 | SEMANTIC | 0.90322 | 0.71576 | 0.6586 | 0.64 |
| llama3.1 | ANONYMIZED | 0.1923 | 0.17676 | 0.16188 | 0.15974 |

*Cell mean computed over valid parses only; fraction shows valid/attempted when <5.

## 4. Factorial detail tables

Per-cell: attempted/valid, individual F1, mean/median/SD/IQR, ARI, NMI, compliance, stability — see **`full_factorial_summary.csv`**.

## 5. Identifier effect (semantic − anonymized)

### Cell-level Δ mean F1

| Model | Evidence | Δ mean F1 | paired mean Δ | paired median Δ | pairs S>A |
|-------|----------|-----------|---------------|-----------------|-----------|
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

ARI, NMI, compliance (paired run-level) and stability (cell-level only): `paired_identifier_effects.csv`, `identifier_effects_by_metric.csv`.

## 6. Evidence richness under ANONYMIZED identifiers

See **`evidence_effects_anonymized.csv`**.

### gemini-2.5-flash
- Best anonymized condition by mean F1: **C2** (C0 mean F1 = 0.2879)
- C0_vs_C1: Δ(right−left) = 0.44478 (0.2879 → 0.73268)
- C0_vs_C2: Δ(right−left) = 0.46575 (0.2879 → 0.75365)
- C0_vs_C3: Δ(right−left) = 0.45054 (0.2879 → 0.73844)
- C1_vs_C2: Δ(right−left) = 0.02097 (0.73268 → 0.75365)
- C1_vs_C3: Δ(right−left) = 0.00576 (0.73268 → 0.73844)
- C2_vs_C3: Δ(right−left) = -0.01521 (0.75365 → 0.73844)

### gpt-4o-mini
- Best anonymized condition by mean F1: **C3** (C0 mean F1 = 0.13122)
- C0_vs_C1: Δ(right−left) = 0.03472 (0.13122 → 0.16594)
- C0_vs_C2: Δ(right−left) = 0.01878 (0.13122 → 0.15)
- C0_vs_C3: Δ(right−left) = 0.05104 (0.13122 → 0.18226)
- C1_vs_C2: Δ(right−left) = -0.01594 (0.16594 → 0.15)
- C1_vs_C3: Δ(right−left) = 0.01632 (0.16594 → 0.18226)
- C2_vs_C3: Δ(right−left) = 0.03226 (0.15 → 0.18226)

### llama3.1
- Best anonymized condition by mean F1: **C0** (C0 mean F1 = 0.1923)
- C0_vs_C1: Δ(right−left) = -0.01554 (0.1923 → 0.17676)
- C0_vs_C2: Δ(right−left) = -0.03042 (0.1923 → 0.16188)
- C0_vs_C3: Δ(right−left) = -0.03256 (0.1923 → 0.15974)
- C1_vs_C2: Δ(right−left) = -0.01488 (0.17676 → 0.16188)
- C1_vs_C3: Δ(right−left) = -0.01702 (0.17676 → 0.15974)
- C2_vs_C3: Δ(right−left) = -0.00214 (0.16188 → 0.15974)

### Answers (descriptive)

**A. Is anonymized C0 still best?** gemini-2.5-flash: no (C2); gpt-4o-mini: no (C3); llama3.1: yes

**B. Does C1 improve over anonymized C0?** gemini-2.5-flash: Δ=0.44478; gpt-4o-mini: Δ=0.03472; llama3.1: Δ=-0.01554

**C. C2 vs C1/C0:** see deltas C0_vs_C2 and C1_vs_C2 in CSV.

**D. C3 (self-critique):** compare C2_vs_C3 and C0_vs_C3 per model in CSV.

**E. Cross-model consistency:** Gemini shows large anonymized gains from C1+; GPT/Llama anonymized means stay low with smaller spreads.

## 7. Effect of identifier semantics on the original C0 finding

### Semantic identifiers (revision cohort)

- **gemini-2.5-flash:** ranking by mean F1 = C0 (0.9245), C3 (0.86265), C1 (0.85276), C2 (0.77095)
- **gpt-4o-mini:** ranking by mean F1 = C0 (0.84466), C2 (0.76176), C3 (0.7389), C1 (0.7333)
- **llama3.1:** ranking by mean F1 = C0 (0.90322), C1 (0.71576), C2 (0.6586), C3 (0.64)

### Anonymized identifiers

- **gemini-2.5-flash:** ranking = C2 (0.75365), C3 (0.73844), C1 (0.73268), C0 (0.2879)
- **gpt-4o-mini:** ranking = C3 (0.18226), C1 (0.16594), C2 (0.15), C0 (0.13122)
- **llama3.1:** ranking = C0 (0.1923), C1 (0.17676), C2 (0.16188), C3 (0.15974)

Under **semantic** names, **C0 remains the top mean F1** for all three models (same qualitative story as the submitted paper). Under **anonymized** names, **only Llama** keeps C0 on top; **Gemini** peaks at **C2**, **GPT-4o-mini** at **C3**, with large C1–C2 lifts over anonymized C0 for Gemini.

## 8. Invalid outputs

- **REV-021** — gemini-2.5-flash C2 SEMANTIC rep 1: raw present=True (12627 B); interpretable=yes; reason excerpt: `[{'type': 'string_type', 'loc': ('uncertain_decisions', 0), 'msg': 'Input should be a valid string', 'input': {'decision': "Ownership of 'User' entity", 'reason': "The 'User' entity's candidate_owner …`
- **REV-027** — gemini-2.5-flash C2 ANONYMIZED rep 4: raw present=True (13191 B); interpretable=yes; reason excerpt: `[{'type': 'string_type', 'loc': ('uncertain_decisions', 0), 'msg': 'Input should be a valid string', 'input': {'decision': 'Placement of Component_08', 'reason': 'Component_08 is a service called by C…`
- **REV-037** — gemini-2.5-flash C3 SEMANTIC rep 4: raw present=True (14563 B); interpretable=yes; reason excerpt: `[{'type': 'string_type', 'loc': ('rule_violations', 0), 'msg': 'Input should be a valid string', 'input': {'rule': 'R4: Minimize unnecessary cross-service coupling', 'violation': 'A cyclic dependency …`

**Validity rates**

By model:
| Group | attempted | valid | invalid | rate |
|-------|----------:|------:|--------:|-----:|
| gemini-2.5-flash | 40 | 37 | 3 | 0.925 |
| gpt-4o-mini | 40 | 40 | 0 | 1.0 |
| llama3.1 | 40 | 40 | 0 | 1.0 |

By evidence_condition:
| Group | attempted | valid | invalid | rate |
|-------|----------:|------:|--------:|-----:|
| C0 | 30 | 30 | 0 | 1.0 |
| C1 | 30 | 30 | 0 | 1.0 |
| C2 | 30 | 28 | 2 | 0.9333 |
| C3 | 30 | 29 | 1 | 0.9667 |

By identifier_condition:
| Group | attempted | valid | invalid | rate |
|-------|----------:|------:|--------:|-----:|
| ANONYMIZED | 60 | 59 | 1 | 0.9833 |
| SEMANTIC | 60 | 58 | 2 | 0.9667 |

All three invalid runs are **Gemini** at **C2/C3** (schema: list fields expected strings, got objects). Cell means for Gemini C2/C3 use **n=4** valid runs; paired deltas omit invalid arms.

## 9. Historical replication (semantic only)

| Model | Cond | Historical | Revision semantic | Δ | Direction | Consistency |
|-------|------|------------|-------------------|---|-----------|-------------|
| gemini-2.5-flash | C0 | 0.906767 | 0.9245 | 0.017733 | higher | close |
| gemini-2.5-flash | C1 | 0.815233 | 0.85276 | 0.037527 | higher | close |
| gemini-2.5-flash | C2 | 0.7835 | 0.77095 | -0.01255 | lower | close |
| gemini-2.5-flash | C3 | 0.812767 | 0.86265 | 0.049883 | higher | close |
| gpt-4o-mini | C0 | 0.8247 | 0.84466 | 0.01996 | higher | close |
| gpt-4o-mini | C1 | 0.7333 | 0.7333 | 0.0 | — | close |
| gpt-4o-mini | C2 | 0.7174 | 0.76176 | 0.04436 | higher | close |
| gpt-4o-mini | C3 | 0.7333 | 0.7389 | 0.0056 | higher | close |
| llama3.1 | C0 | 0.906767 | 0.90322 | -0.003547 | lower | close |
| llama3.1 | C1 | 0.617267 | 0.71576 | 0.098493 | higher | moderate drift |
| llama3.1 | C2 | 0.780867 | 0.6586 | -0.122267 | lower | large drift |
| llama3.1 | C3 | 0.5 | 0.64 | 0.14 | higher | large drift |

**C0 semantic reproduced?** For all three models, C0 has the highest mean F1 among C0–C3 in the **new semantic** cohort (see §7). Cloud models track submitted means closely at C0; **Llama C2/C3** drift more from historical semantic means.

## 10. Outcome classification

**MIXED OUTCOME (B + D)**

C0 is not strongest after anonymization for most cloud models; richer evidence raises anonymized F1 substantially (gemini-2.5-flash, gpt-4o-mini). gemini-2.5-flash: anonymized best=C2 (mean F1 0.75365); C0 mean=0.2879; gpt-4o-mini: anonymized best=C3 (mean F1 0.18226); C0 mean=0.13122; llama3.1: anonymized best=C0 (mean F1 0.1923); C0 mean=0.1923

## 11. Artifacts

- `full_factorial_summary.csv`
- `evidence_effects_anonymized.csv`
- `paired_identifier_effects.csv`
- `historical_replication_check.csv`
- `cell_summary.csv`, `validity_summary.csv`, `run_level_results.csv`

---

## Final scientific summary

### Finding 1 — Identifier-semantic effect

Semantic identifiers yield much higher gold agreement than anonymized aliases for every model×evidence cell with valid runs. Paired semantic−anonymized F1 deltas are positive in nearly all complete pairs; magnitude is largest at C0 for GPT/Llama and remains large for Gemini even when anonymized evidence helps.

### Finding 2 — Evidence richness under semantic identifiers

C0 remains the strongest semantic condition for all three models (mean F1 ranks C0 first). C1–C3 lower mean F1 vs C0 for Gemini/GPT; Llama shows the same C0-first ordering with a steeper drop after C0.

### Finding 3 — Evidence richness under anonymized identifiers

Pattern is **not** uniform: Gemini anonymized F1 rises from ~0.29 (C0) to ~0.73–0.75 (C1–C3). GPT and Llama anonymized means stay ~0.13–0.19 with only modest variation; C0 is still best for Llama, not for Gemini/GPT.

### Finding 4 — Model-specific behavior

Gemini combines high semantic performance with the largest **relative** benefit from extra evidence when names are anonymized. GPT semantic C0 is strong but anonymized arms stay flat. Llama shows the largest semantic/anonymized gap and limited anonymized response to richer evidence.

### Finding 5 — Stability and validity

Overall validity 117/120. Invalidity is confined to three Gemini schema failures (C2/C3). Semantic arms often show higher assignment stability than anonymized at C0; see `stability` column in factorial summary.

### Finding 6 — Historical replication

Revision **semantic** means align with submitted study for Gemini/GPT at most conditions; Llama C2/C3 differ more. Replication supports the **semantic** C0-first narrative more than it constrains anonymized behavior.

### Implication for the submitted central claim

**SUPPORTED WITH IMPORTANT QUALIFICATION** — New semantic cohort still ranks C0 first for all three models, but under anonymization best conditions are {'gemini-2.5-flash': 'C2', 'gpt-4o-mini': 'C3', 'llama3.1': 'C0'} — identifier removal changes the evidence ladder.

### Caveats before manuscript revision

- Three Gemini invalid parses reduce n to 4 in affected cells; do not impute.
- Anonymized evidence ladder conclusions are model-dependent; do not collapse across models.
- Historical comparison uses semantic arm only; provider/version drift may explain Llama C2/C3 gaps.
- Identifier control preserves domain/capability text; large semantic advantage does not by itself prove naming leakage in the original study—it quantifies alias information under fixed evidence.
