# SENSITIVITY_ANALYSIS_SPEC — PETCLINIC_EXT_V1 (frozen pre-execution)

**Protocol amendment:** approved in principle (small-cluster criterion).  
**Status:** FROZEN before any LLM execution. Results must not choose which analysis to emphasize post hoc.

## PRIMARY analysis (mandatory)

- **Reference universe:** all **15** deterministically mapped monolith components.
- **Reference services:** CUSTOMERS (8), VETS (5), VISITS (2).
- **Metrics:** global partition agreement only — pairwise precision, pairwise recall, pairwise F1, ARI, NMI, validity rate, run-to-run stability.
- **Claim scope:** whole-partition **identifier sensitivity** on independent PetClinic (not per-service headline claims).

**Do not** report or emphasize per-service precision/recall/F1 for CUSTOMERS, VETS, or VISITS as primary evidence.

## SECONDARY sensitivity (mandatory reporting companion)

- **Reference universe:** CUSTOMERS + VETS components only (**13** components, **2** reference services).
- **Exclusion:** all VISITS-mapped components (`Visit`, `VisitController`).
- **Same metrics** as primary, on the reduced 13-component gold partition.
- **Purpose:** assess whether semantic vs anonymized direction depends on the two-component VISITS cluster.

### Pre-specified interpretation (do not reverse after results)

| Primary vs sensitivity | Interpretation |
|------------------------|----------------|
| Identifier-effect **direction similar** (e.g. semantic > anonymized at E0 for same models) | Effect is **not driven solely** by the small VISITS cluster. |
| **Direction changes** materially | Reference **imbalance** (especially VISITS n=2) may **materially affect** the external result; discuss SMALL_REFERENCE_CLUSTER limitation prominently. |

The sensitivity analysis **does not replace** the three-service primary analysis.

## Implementation note (post-execution, not now)

Scoring script should accept `reference_scope=PRIMARY_15` vs `SENSITIVITY_CV_13` filtering `reference_mapping.csv` by service.
