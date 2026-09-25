# LEAKAGE_AUDIT — PETCLINIC_EXT_V1

Scope: prompts (`prompts/*.txt`), evidence JSON (`evidence/E*_*.json`), `DOMAIN_DESCRIPTION.txt`.

Classification key: **IDENTITY_ALIAS** | **LEGITIMATE_DOMAIN_SEMANTICS** | **STRUCTURAL_EVIDENCE** | **REFERENCE_LEAKAGE** | **SAFE**

## Target reference labels (CUSTOMERS / VETS / VISITS)

| Location | Finding |
|----------|---------|
| All prompts | **SAFE** — labels absent; schema requires free-text service names |
| All evidence JSON | **SAFE** — labels absent |
| `reference_mapping.csv` | **REFERENCE_LEAKAGE** if exposed to model — **not** in model inputs (scoring-only) |

## Identity aliases (ANONYMIZED condition)

| Term | SEMANTIC evidence | ANONYMIZED evidence | Prompts ANON |
|------|-------------------|---------------------|--------------|
| Owner, Pet, Vet, Visit, *Controller, *Repository | IDENTITY_ALIAS (expected) | Replaced by `Component_XX` | **SAFE** (no class names) |
| `org.springframework.samples.petclinic.*` paths | IDENTITY_ALIAS | `Module_XX` / `artifacts/Component_XX.java` | **SAFE** |

## Domain vocabulary

| Term | DOMAIN_DESCRIPTION / prompts | Classification |
|------|------------------------------|----------------|
| veterinary, clinic, pets, clients, visits (generic) | DOMAIN_DESCRIPTION.txt | **LEGITIMATE_DOMAIN_SEMANTICS** — allowed; does not name target microservices |
| “Customers”, “Vets”, “Visits” as services | absent | **SAFE** |

## Structural evidence (E1 only)

| Content | Classification |
|---------|----------------|
| `static_call_edges`, `data_relations` between components | **STRUCTURAL_EVIDENCE** — identical topology in SEMANTIC vs ANONYMIZED (renamed nodes only) |

## Package / endpoint / table names

- SEMANTIC JSON may include monolith `source_path` segments (`owner`, `vet`) in `file` field — **IDENTITY_ALIAS** (semantic arm only).
- ANONYMIZED JSON uses opaque `artifacts/Component_XX.java` — **SAFE** for path identity.
- SQL table names **not** embedded in E0/E1 evidence packages.

## Reverse map

`component_identifier_map.csv` is **not** referenced in prompts or evidence. **SAFE** for model input.

## Remaining semantic information under ANONYMIZED

- Generic domain narrative (veterinary clinic operations).
- Component `kind` (controller, repository, domain, validator).
- Graph structure in E1 (who calls whom) without domain-specific class names.

## Verdict

**ANONYMIZED** inputs do not encode target service membership via identity aliases. Automated check `scripts/verify_petclinic_freeze.py` (`checks.E_no_reference_in_prompts`) must pass before execution.
