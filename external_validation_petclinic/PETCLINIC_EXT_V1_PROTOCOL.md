# PETCLINIC_EXT_V1 — External validation protocol (design freeze)

**Status:** DESIGN FREEZE — **no LLM execution**  
**Amendment:** small-cluster criterion + sensitivity analysis (approved in principle)  
**Parent study:** EDU-R / SEMS-R IEEE Access revision  
**Question:** Does the identifier-semantics effect observed in EDU-R replicate on independent Spring PetClinic?

## Evidence conditions (not EDU-R C0–C3)

| ID | Content |
|----|---------|
| **E0_MINIMAL** | Neutral domain description + component catalog |
| **E1_STRUCTURAL** | E0 + static-call edges + data-access relations (monolith extraction only) |

## Identifier conditions

- **SEMANTIC** — original monolith names/paths  
- **ANONYMIZED** — `Component_XX`, `Module_XX`, opaque artifact paths  

## Reference partition (frozen)

| Service | Components |
|---------|----------:|
| CUSTOMERS | 8 |
| VETS | 5 |
| VISITS | 2 |
| **Total** | **15** |

See `REFERENCE_MAPPING_AUDIT.md` for why VISITS has exactly two components.

### Amended inclusion criteria (replaces “≥3 per service”)

- ≥ **12** deterministically mapped components overall ✓ (15)  
- ≥ **3** externally defined business reference services ✓  
- ≥ **2** deterministically mapped components in **every** service ✓  
- Any service with **&lt;3** components → **SMALL_REFERENCE_CLUSTER** limitation (VISITS)

`reference_mapping.csv` is **unchanged** by this amendment.

### Reference pair arithmetic (gold)

- Unordered pairs: **C(15,2) = 105**  
- Same-service positive pairs: **28 + 10 + 1 = 39** (CUSTOMERS / VETS / VISITS)  
- Global partition metrics are appropriate; **not** strong VISITS-specific claims.

## Design matrix (not executed)

3 models × 2 evidence × 2 identifier × 5 reps = **60** runs (`run_manifest.csv`).

## Pairing

Counterbalanced adjacent pairs per `model × evidence × repetition` (odd pair index → SEMANTIC first).

## Scoring (planned) — global only

**Primary metrics (global partition):**

- pairwise precision, recall, F1  
- ARI, NMI  
- validity rate  
- run-to-run stability  

**Excluded:** rule compliance (no PetClinic migration-rule set).  
**Excluded from primary emphasis:** per-service precision/recall/F1 headlines.

Reverse-map anonymized component IDs after generation, before scoring. Reference mapping never shown to the model.

## Pre-specified analyses (frozen before execution)

| Analysis | Universe | Detail |
|----------|----------|--------|
| **PRIMARY** | 15 components, 3 services | Full reference; drives external-validity claim |
| **SECONDARY SENSITIVITY** | 13 components (CUSTOMERS+VETS only) | Excludes VISITS-mapped components; robustness to small VISITS cluster |

Full specification: `SENSITIVITY_ANALYSIS_SPEC.md`. Sensitivity **does not replace** primary.

## Research questions (frozen)

- **EXT-RQ1:** SEMANTIC vs ANONYMIZED at **E0** (per model).  
- **EXT-RQ2:** ANONYMIZED **E0** vs **E1** (per model).  
- **EXT-RQ3:** Qualitative consistency across model families (no pooled headline).

## Outcomes A–D (+ MIXED)

As specified in revision brief; no outcome is a failed experiment.

## Invalid output policy

Same as `revision_anonymization/RETRY_FAILURE_POLICY.md` (infra retries only; schema failures are outcomes).

## Pre-execution validation

```bash
python external_validation_petclinic/scripts/verify_petclinic_freeze.py
```

→ `validation_results.json`

### Stop/go criteria (amended)

| ID | Criterion |
|----|-----------|
| A | Independent source repository frozen |
| B | Pre-existing microservice reference frozen |
| C | Deterministic reference mapping |
| D | ≥12 total mapped components |
| E | ≥3 reference business services |
| F | ≥2 components per service |
| G | No direct reference-label leakage in anonymized model inputs |
| H | SMALL_REFERENCE_CLUSTER recorded when any cluster &lt;3 |
| I | Primary + sensitivity analysis frozen pre-execution |

**Expected:** **GO** (VISITS n=2 documented under H).
