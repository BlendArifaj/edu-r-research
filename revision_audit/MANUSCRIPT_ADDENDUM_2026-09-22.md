# Manuscript addendum — submitted IEEE Access docx (2026-09-22)

**Source file (read-only):**  
`/Users/bezepsolution/Desktop/FIEK/PhD/Punime shkencore/11 - Sems-r research - SUBMITTED/EDU_R_IEEE_Access_2026_Manuscript.docx`

**Extracted text (audit only):** `revision_audit/manuscript_extracted.txt`  
**Extracted tables:** `revision_audit/manuscript_tables.md`  
**Row-level diff:** `revision_audit/manuscript_vs_artifacts.csv`

**User note:** Additional experiments may have been run on other platforms; the submitted manuscript is the **authoritative intended last state**. The `sems-research` git tree may not contain all runs cited in the paper (especially Table V at 300 users).

---

## 1. Table I — reviewer concern **resolved (transcription)**

In the **manuscript Word table**, F1, ARI, and NMI are **identical per row** (e.g. Rule Heuristic: 0.925 / 0.925 / 0.925).

In **repository artifacts** (`outputs/runs/2026-08-27_005/metrics/table_a.csv` and independent recomputation in `table_i_recomputed.csv`), the three metrics **differ** as expected.

| Method | MS F1 | MS ARI | MS NMI | Artifact F1 | Artifact ARI | Artifact NMI |
|--------|-------|--------|--------|-------------|--------------|--------------|
| Rule Heuristic | 0.925 | **0.925** | **0.925** | 0.9245 | **0.9067** | **0.9606** |
| Combined Graph | 0.387 | **0.387** | **0.387** | 0.3866 | **0.2183** | **0.4883** |

**Diagnosis: (C) transcription / table formatting error** — ARI and NMI columns were filled with the **same rounded F1 value** (3 decimal places), not computed ARI/NMI.

Body text still cites correct F1 to 4 decimals (e.g. 0.9245, 0.3866). **Rankings and narrative do not change** if ARI/NMI are corrected; only Table I columns and any prose that relied on identical triples need updating.

---

## 2. Tables II–IV vs `sems-research` snapshot

| Table | Match to `2026-08-27_005` metrics |
|-------|-----------------------------------|
| **II** | **Yes** (3 d.p. rounding of Table B) |
| **III** | **Yes**; `Static + runtime` = internal `combined_graph` |
| **IV** | **Yes** (expert medians present in snapshot follow-up) |

LLM design in manuscript (3 models × 4 conditions × 3 reps) matches scientific snapshot **005**.

---

## 3. Table V — platform / artifact gap

| Field | Manuscript | `sems-research` Locust stamp `2026-08-27_225302` |
|-------|------------|--------------------------------------------------|
| Users | **300** | **100** (`workload/config/high.yaml`, `comparison.csv`) |
| Monolith requests | **180,144** | **60,048** (exactly **×3**) |
| Monolith failures | **198** | **66** (exactly **×3**) |
| Clustered requests | **220,512** | **23,000** (not ×3; “corrected” trajectory in `paper.md`) |
| Clustered median | **120 ms** | **1200 ms** in Locust Aggregated row |
| Clustered RPS | **245.88** | **76.94** |

**Interpretation:**

- Monolith columns in the manuscript are **consistent with scaling the local 100-user run by 3** (users 100→300), but **latency percentiles for clustered were not taken from that same Locust file** (local clustered median is 1200 ms, not 120 ms).
- The manuscript matches the **hand-edited** `outputs/reports/2026-08-27_005/paper.md` Phase 10 block, **not** the immutable `comparison.csv` in the repo.

**For revision:** Either (a) **import and archive** the 300-user / other-platform Locust logs that support Table V, or (b) **revert Table V** to the stamped artifact under version control.

Manuscript line 56: *“actual run time is omitted until further verification”* — **(B)+(C)**: placeholder note while publishing derived throughput; duration is **defined** in repo config (**300s**) but user count differs between ms and local default config.

---

## 4. Structural / placeholder issues (manuscript)

| Item | Finding |
|------|---------|
| **Section VII** | **Missing** — numbering goes **VI. DISCUSSION** → **VIII. CONCLUSION** |
| **Threats to validity** | **No dedicated section**; III-B promises naming leakage *“discussed later”* — **never appears** as a full section (only scattered mentions) |
| **Placeholders** | `Date of publication xxxx 00, 0000`; `10.1109/ACCESS.2024.Doi Number` |
| **Keywords** | Includes **EDU-R**; **not** “engineering education” as a keyword |
| **“Significantly lower”** | Abstract: latency “significantly lower” — **no statistical test** cited |

---

## 5. Updated BLOCKER list (with manuscript)

| Issue | Status |
|-------|--------|
| Table I ARI/NMI columns | **MAJOR manuscript fix** (not a recomputation bug) |
| Table V vs local Locust | **BLOCKER until** other-platform artifacts are archived or table corrected |
| Missing Section VII / promised threats section | **MAJOR** structural |
| IEEE placeholders | **MINOR** pre-publication |

---

## 6. Recommended next step (no execution)

1. Fix Table I in Word: paste **ARI and NMI from `table_a.csv`** (or `table_i_recomputed.csv`).  
2. Locate and add to repo (or supplementary ZIP) the **300-user Mode E** raw Locust outputs for Table V.  
3. Add **Section VII — Threats to Validity** (naming leak, C0 domain list, architect anchoring, single runtime run, EDU-R ≠ production).  
4. Renumber **VIII → VII** or insert missing section.

See main report: `REVISION_FORENSIC_AUDIT.md`.
