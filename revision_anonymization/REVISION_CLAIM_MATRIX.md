# REVISION_CLAIM_MATRIX — submitted claims vs REVISION_CONTROL_V1

**Purpose:** Classify major manuscript claims before prose edits.  
**Evidence:** Original snapshot `outputs/runs/2026-08-27_005`; revision `REVISION_CONTROL_V1` (`PUBLICATION_RESULTS_FREEZE.md`, forensic audit).

| Action | Meaning |
|--------|---------|
| **KEEP** | Claim remains as stated for semantic/original evidence design |
| **KEEP WITH QUALIFICATION** | Claim holds with narrower scope or explicit caveat |
| **REPLACE** | Wording or emphasis must change to match evidence |
| **REMOVE** | Claim not defensible as stated |

---

## 1. “C0 is strongest for all three models”

| Field | Content |
|-------|---------|
| **Manuscript location** | Results / LLM evidence ladder (Tables II, narrative around C0–C3); central empirical motif |
| **Original evidence** | 36-run study: highest mean F1 at C0 for Gemini, GPT-4o-mini, Llama (`2026-08-27_005`) |
| **New evidence** | **Semantic arm:** C0 still highest mean F1 for all three (revision 120-run). **Anonymized arm:** C0 **not** best for Gemini (C2) or GPT (C3); Llama C0 still best among anonymized |
| **Recommended interpretation** | **KEEP WITH QUALIFICATION** — State C0-first **under semantic identifiers** (replicated). Add that **identifier-semantics control** reverses or weakens C0 dominance for cloud models when names are opaque |
| **Action** | **KEEP WITH QUALIFICATION** |

---

## 2. “More evidence is not necessarily better”

| Field | Content |
|-------|---------|
| **Manuscript location** | Discussion of evidence richness; C1–C3 vs C0 under semantic prompts |
| **Original evidence** | Semantic runs: diminishing returns / non-monotonic ladder for some models |
| **New evidence** | Semantic: still non-monotonic (e.g. Gemini C3 > C1). **Anonymized Gemini:** C1–C3 **much higher** than C0 — evidence **is** better when names removed for that model |
| **Recommended interpretation** | **REPLACE** scope — “Not necessarily better” applies **conditional on identifier semantics**; for anonymized Gemini, more evidence **is** materially better |
| **Action** | **REPLACE** |

---

## 3. “Semantic context enables LLMs to approximate experts”

| Field | Content |
|-------|---------|
| **Manuscript location** | Introduction / contributions; qualitative comparison to expert decomposition |
| **Original evidence** | High semantic C0 F1 (~0.82–0.92) vs graph baselines in Table I |
| **New evidence** | Semantic C0 remains high; **anonymized** C0 collapses (~0.13–0.29) while **domain/capability text retained** — expert-like agreement depends strongly on **component identity cues**, not capability text alone |
| **Recommended interpretation** | **KEEP WITH QUALIFICATION** — Approximation holds with **full semantic identifiers**; **not** with identifier control at C0 |
| **Action** | **KEEP WITH QUALIFICATION** |

---

## 4. “Low-level dependency evidence can introduce noise”

| Field | Content |
|-------|---------|
| **Manuscript location** | Evidence design rationale (C1 vs C0) |
| **Original evidence** | Semantic C1 often below C0 |
| **New evidence** | Under **anonymized Gemini**, C1 **increases** F1 vs C0; under GPT/Llama anonymized, small or negative C0→C1 deltas |
| **Recommended interpretation** | **KEEP WITH QUALIFICATION** — Noise narrative fits **semantic** ladder; **not universal** when identifiers anonymized (model-specific) |
| **Action** | **KEEP WITH QUALIFICATION** |

---

## 5. “Dependency evidence can preserve accidental coupling”

| Field | Content |
|-------|---------|
| **Manuscript location** | Discussion / threats (coupling, migration) |
| **Original evidence** | Conceptual + graph/LLM comparisons |
| **New evidence** | Identifier experiment does **not** isolate accidental coupling mechanism; anonymized degradation is consistent with **lost alias semantics**, not proven coupling preservation |
| **Recommended interpretation** | **KEEP WITH QUALIFICATION** — Retain as **hypothesis/limitation**, not as outcome of REVISION_CONTROL_V1 |
| **Action** | **KEEP WITH QUALIFICATION** |

---

## 6. “LLMs outperform graph methods”

| Field | Content |
|-------|---------|
| **Manuscript location** | Table I / baseline comparison |
| **Original evidence** | LLM semantic C0 F1 > Louvain baselines on EDU-R |
| **New evidence** | Not re-run baselines in revision; semantic C0 replication supports **same ordering** if baselines unchanged. Anonymized LLM at C0 **far below** typical LLM semantic performance — comparison to graphs **not re-tested** under anonymization |
| **Recommended interpretation** | **KEEP WITH QUALIFICATION** — For **semantic** conditions on EDU-R; do not extend to anonymized arm without new baselines |
| **Action** | **KEEP WITH QUALIFICATION** |

---

## 7. “Runtime clustered deployment improves performance”

| Field | Content |
|-------|---------|
| **Manuscript location** | Phase 10 / Table V; performance evaluation section |
| **Original evidence** | Manuscript claims vs `revision_audit` Locust logs — **conflict** (100-user local stamp; clustered 300-user narrative) |
| **New evidence** | **No new runtime experiment** in REVISION_CONTROL_V1 |
| **Recommended interpretation** | **REMOVE or REPLACE** performance superiority claims unless reconciled with archived logs or new study (`REVISION_FORENSIC_AUDIT.md` **BLOCKER**) |
| **Action** | **REMOVE** (performance claims) / **REPLACE** (with verified numbers or limitation) |

---

## Summary table

| Claim | Action |
|-------|--------|
| C0 strongest (all models) | KEEP WITH QUALIFICATION |
| More evidence not necessarily better | REPLACE (conditional) |
| LLMs approximate experts | KEEP WITH QUALIFICATION |
| Low-level dependency noise | KEEP WITH QUALIFICATION |
| Accidental coupling preserved | KEEP WITH QUALIFICATION |
| LLMs outperform graphs | KEEP WITH QUALIFICATION |
| Runtime clustered improves RPS | REMOVE / REPLACE (forensic) |

---

*No manuscript prose changed in this artifact.*
