# REVIEWER_RESOLUTION_MATRIX — IEEE Access revision

Maps reviewer themes to **evidence now available**, **remaining manuscript work**, and **response-letter hooks**.  
Sources: `REVISION_FORENSIC_AUDIT.md`, `REVISION_CONTROL_V1` results, `revision_audit/`.

---

## R1 — Semantic names / domain leakage / high C0

| Item | Detail |
|------|--------|
| **Concern** | Component names and domain list may inflate C0; unfair to baselines |
| **Evidence now** | 120-run identifier control; `LEAKAGE_AUDIT.md`; `PUBLICATION_RESULTS_FREEZE.md` §B,H; paired Δ F1 at C0: Gemini 0.64, GPT 0.71, Llama 0.71 |
| **Experiment** | `REVISION_CONTROL_V1` (semantic vs anonymized × C0–C3 × 3 models × 5 reps) |
| **Manuscript change required** | Yes — disclose identifier-semantics control; qualify C0 claims; cite Δ tables |
| **Response letter** | “We ran a pre-registered identifier control (120 new runs). Semantic C0 replicates; anonymized C0 drops sharply; extra evidence partially recovers Gemini only.” |

---

## R2 — (Editor / general rigor)

| Item | Detail |
|------|--------|
| **Concern** | Clarity, structure, completeness (inferred) |
| **Evidence now** | Freeze manifest, provenance JSON, 5-rep design, validity rates |
| **Manuscript change required** | Yes — integrate revision experiment section; restore missing threats |
| **Response letter** | Point to reproducibility package and frozen SHA manifest |

---

## R3 — Fair baselines / graph comparisons

| Item | Detail |
|------|--------|
| **Concern** | LLM vs graph fairness, evidence parity |
| **Evidence now** | Baselines not re-executed; scoring universe unchanged (`REFERENCE_LABEL_SCHEMA_VERDICT.md`); Table I recomputed in `revision_audit/table_i_recomputed.csv` |
| **Manuscript change required** | Yes — clarify Table III `static_plus_runtime` = `combined_graph` (audit); baseline evidence parity text |
| **Response letter** | Forensic Table I/III reconciliation + unchanged evaluator |

---

## R4 — Evidence richness / C0–C3 ladder

| Item | Detail |
|------|--------|
| **Concern** | Does more evidence help? |
| **Evidence now** | `evidence_effects_anonymized.csv`; semantic ladder replicated; anonymized ladder **model-dependent** |
| **Manuscript change required** | Yes — conditional narrative (semantic vs anonymized) |
| **Response letter** | “Evidence benefit interacts with identifier semantics; Gemini recovers under anonymization with C1/C2.” |

---

## R5 — Few repetitions / stability

| Item | Detail |
|------|--------|
| **Concern** | n=3 original; stability |
| **Evidence now** | n=5 revision; `stability` in `full_factorial_summary.csv`; validity 117/120 |
| **Manuscript change required** | Yes — report revision n=5; cite stability column; note 3 invalid Gemini parses |
| **Response letter** | Expanded repetitions + invalid-output policy (no repair) |

---

## R6 — Domain vs identifier semantics

| Item | Detail |
|------|--------|
| **Concern** | What is “semantic” in prompts? |
| **Evidence now** | `LEAKAGE_AUDIT.md` distinction A (preserved domain) vs B (anonymized aliases); protocol §5 |
| **Manuscript change required** | Yes — explicit “identifier-semantics control” wording |
| **Response letter** | Capability/entity text preserved; only names/paths/area ids anonymized |

---

## Cross-cutting: Table I metrics (F1 = ARI = NMI in Word)

| Item | Detail |
|------|--------|
| **Evidence** | `revision_audit/table_i_recomputed.csv` — artifact math correct; Word transcription error |
| **Manuscript change** | Fix Table I columns in manuscript |
| **Response letter** | Attach recomputation; classify as transcription |

---

## Cross-cutting: Runtime / Phase 10 / Table V

| Item | Detail |
|------|--------|
| **Evidence** | `REVISION_FORENSIC_AUDIT.md` §Phase 10 — local Locust vs manuscript 300-user clustered |
| **Manuscript change** | **BLOCKER** — remove, correct, or reproduce runtime claims |
| **Response letter** | Honest limitation or new verified run (outside REVISION_CONTROL_V1) |

---

## Cross-cutting: Reproducibility

| Item | Detail |
|------|--------|
| **Evidence** | `FINAL_ARTIFACT_MANIFEST.sha256`, `FREEZE_REVISION_CONTROL_V1/PROVENANCE.json`, frozen Llama digest, git SHA in manifest |
| **Manuscript change** | Cite experiment ID, protocol version, tag (once committed) |
| **Response letter** | Checksum manifest + 120 run paths |
| **Caveat** | Freeze bundle was **uncommitted** at `713a3f9` — commit + tag before submission |

---

## Cross-cutting: Reference architecture / gold

| Item | Detail |
|------|--------|
| **Evidence** | Unchanged gold; reverse-map for anonymized scoring; six service names not required in output schema |
| **Manuscript change** | Clarify scoring universe (24 components); gold role |
| **Response letter** | `REFERENCE_LABEL_SCHEMA_VERDICT.md` |

---

## Cross-cutting: Claim scope / Threats to Validity

| Item | Detail |
|------|--------|
| **Evidence** | `REVISION_CLAIM_MATRIX.md`; interpretation boundaries in publication freeze |
| **Manuscript change** | Restore Section VII / threats; bound generalization to EDU-R |
| **Response letter** | List supported vs unsupported claims |

---

## Quick reference

| Reviewer theme | Primary artifact | Ms change? |
|----------------|------------------|------------|
| Name leakage | paired_identifier_effects.csv | Yes |
| Table I | table_i_recomputed.csv | Yes |
| Runtime | forensic audit Phase 10 | Yes (blocker) |
| Reproducibility | FINAL_ARTIFACT_MANIFEST.sha256 | Yes |
| Reps / validity | validity_summary.csv | Yes |
| Reference arch | component map + gold | Clarify |
| Claim scope | REVISION_CLAIM_MATRIX.md | Yes |
| Threats | publication freeze boundaries | Yes |

---

*No manuscript prose changed in this artifact.*
