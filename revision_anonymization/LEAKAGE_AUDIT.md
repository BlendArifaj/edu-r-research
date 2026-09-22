# Leakage audit — revision v2 (strengthened identity blinding)

**Protocol:** `anonymization_exp_v2`  
**Control:** Opaque **component-identity aliases** in the ANONYMIZED arm only.

---

## A. Identity / name leakage vs B. Legitimate semantic evidence

| Category | Definition | ANONYMIZED arm handling |
|----------|------------|-------------------------|
| **A. Identity / name leakage** | Tokens whose primary role is to identify a **specific application component** or its **module/package/file path** | **Removed/replaced** |
| **B. Legitimate semantic evidence** | Domain purpose, business entities, operations, cross-domain narratives, call/data/runtime **structure**, migration rules R1–R9 | **Preserved** (content unchanged except component token substitution in structural fields) |

### A — replaced in ANONYMIZED inputs

| Leakage type | Semantic (revision SEMANTIC arm) | Anonymized arm |
|--------------|----------------------------------|----------------|
| Component class name | `FacultyService`, … | `Component_XX` |
| Module path | `app.repositories.faculty_repository` | `Module_XX` (paired 1:1 with component) |
| Source file path | `monolith/app/.../faculty_repository.py` | `artifacts/Component_XX.py` |
| Metrics `component` field | original name | `Component_XX` |
| Functional-area **listing id** (alias of reference service slug) | `faculty`, `student`, … | `Area_01`…`Area_06` |
| System paths | `monolith/app`, trace path | `artifacts/app`, `artifacts/runtime_traces.jsonl` |
| Call/data/runtime graph node labels | class names | `Component_XX` |

Maps: `component_identifier_map.csv`, `functional_area_identifier_map.csv`, `evidence/module_path_map.csv`, `evidence/file_path_map.csv`.

**Not sent to the model:** any reverse map or `original_identifier` columns.

### B — preserved (both arms)

| Evidence | Examples | Notes |
|----------|----------|-------|
| Global domain description | university education-management monolith | Wording unchanged |
| Functional **capabilities** | “course catalog administration”, “GPA calculation” | Under `Area_XX:` in ANON |
| Cross-domain narratives | “Grade workflows require student, teacher, course…” | Natural language semantics |
| Entity / table names | `Student`, `CourseEnrollment`, `Invoice` | Not component identities |
| HTTP endpoint paths | `/api/v1/students/...` | Operation routing, not class names |
| Runtime counts / SQL means | numeric summaries | Unchanged |
| R1–R9 rule **text** | migration constraints | Unchanged |
| Component **kind** | `service`, `repository`, `legacy` | Structural layer hint (disclosed) |

---

## Channel checklist (C0–C3)

| Channel | Class (ANON) |
|---------|----------------|
| `prompts.py` preamble (SEMS-R, education areas) | B |
| C0 capability bullets | B |
| C0 area list **keys** | **A → Area_XX** |
| C0 component catalog | **A → Component_XX + Module_XX** |
| C1 call edges | **A → nodes opaque; relation B** |
| C1 entity ownership accessors | **A on component tokens; B on entities** |
| C1 database_usage component column | **A** |
| C1 runtime endpoint strings | B |
| C2 rules | B |
| C3 instructions | B |
| JSON schema example | B (generic placeholders) |

---

## Output schema

See **`REFERENCE_LABEL_SCHEMA_VERDICT.md`**: **NO** required six reference labels in schema.

---

## SEMANTIC arm (revision experiment)

Uses **original** identifiers (same as submitted paper evidence). Identity leakage **intentionally present** for comparison.

---

## Validation

`scripts/verify_anonymization.py` → `validation_results.json`  
**Latest:** `all_pass: true` (checks A–M + schema template scan).

---

## Residual limitations (disclose in paper)

1. **Kind** field (`service` vs `repository`) remains.  
2. **Entity names** and **endpoint paths** retain domain language.  
3. **C0 capability text** still describes business areas (without using reference service labels as **ids** in ANON).  
4. Models may still **choose** domain-like `services[].name` strings voluntarily.

These are **not** treated as identity aliases for v2; optional future study if needed.
