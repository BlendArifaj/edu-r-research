# REFERENCE_MAPPING_AUDIT — PETCLINIC_EXT_V1

**Protocol:** `PETCLINIC_EXT_V1` (amended small-cluster criterion, freeze before execution)

## Summary

| Metric | Value |
|--------|------:|
| Included monolith components | **15** |
| CUSTOMERS | **8** |
| VETS | **5** |
| VISITS | **2** |
| Excluded candidates | **15** |

**Amended stop/go:** ≥12 total components, ≥3 business reference services, ≥2 components per service — **satisfied**. VISITS is a **SMALL_REFERENCE_CLUSTER** (n=2).

## Why VISITS has only two components

This is a property of **monolith ↔ microservices correspondence**, not missing extraction.

1. The canonical monolith includes **`Visit`** (domain) and **`VisitController`** (web entry for visit creation). Both have unique counterparts in **visits-service** (RULE_1 / RULE_2) → **VISITS**.
2. **`VisitController`** persists visit-related state through **`OwnerRepository`** (constructor injection in monolith source), not through a monolith `VisitRepository`.
3. The distributed **visits-service** defines **`VisitRepository`**, but that type **does not exist** in the monolith codebase. RULE_1 cannot map a non-existent monolith artifact.
4. **`OwnerRepository`** cannot be assigned wholesale to VISITS without **architectural judgment**: it is the persistence boundary for **Owner** (customer) aggregates and is correctly mapped to **CUSTOMERS** via RULE_1.
5. No additional frozen rule assigns partial repository responsibility without judgment. Therefore **only two** VISITS components are retained.

We **do not** invent a third VISITS component to satisfy an arbitrary minimum.

## Reference imbalance (pair counts for gold partition)

For **n** components in one reference service, unordered within-service positive pairs = **C(n,2)**.

| Service | n | C(n,2) same-service positive pairs |
|---------|--:|-----------------------------------:|
| CUSTOMERS | 8 | **28** |
| VETS | 5 | **10** |
| VISITS | 2 | **1** |
| **Total same-service positives** | 15 | **39** |

All unordered component pairs (evaluation universe): **C(15,2) = 105**.

VISITS contributes **1 / 39** same-service positive pairs (~2.6% of within-service positive mass).

**Implication:** PETCLINIC_EXT_V1 supports **global** partition-agreement / identifier-sensitivity analysis on the full 15-component reference. It does **not** support strong **service-specific** conclusions about VISITS alone.

## Mapping rules (frozen)

1. **RULE_1_UNIQUE_SIMPLE_NAME**
2. **RULE_2_CONTROLLER_TO_RESOURCE**
3. **RULE_2_REPOSITORY_ENTITY_TYPE**
4. **RULE_2_VALIDATOR_FOR_ENTITY_PET**
5. **RULE_2_VET_PACKAGE_AGGREGATE**

**RULE 3:** unmapped → exclude (no judgment).

## Manual architectural judgment

**None** for included rows.

## Mapping file integrity

- `reference_mapping.csv` — **15 rows, unchanged** under this amendment.
- SHA-256: see `reference_mapping.sha256` (must match at validation).

## BLOCKER status (amended protocol)

No BLOCKER for design freeze. **MAJOR limitation (documented):** SMALL_REFERENCE_CLUSTER for VISITS (n=2). Mitigation: pre-specified **CUSTOMERS+VETS** sensitivity analysis (`SENSITIVITY_ANALYSIS_SPEC.md`).
