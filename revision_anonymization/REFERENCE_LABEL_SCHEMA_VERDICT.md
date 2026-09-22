# Reference service label leakage — schema verdict

**Question:** Does any LLM prompt or output schema **require** the six reference service labels  
(Faculty, Student, Grade, Finance, Attendance, Library) as target categories?

## Answer: **NO**

### Evidence

1. **Output JSON schema** (`decomposition/llm/prompts.py` `SCHEMA_INSTRUCTIONS`):
   - `services[].name` is free text (`"candidate-service"` example only).
   - No enum, no closed list of six domains.
   - Components listed by whatever identifiers appear in the prompt catalog.

2. **Pydantic model** (`decomposition/llm/schema.py`):
   - `ServiceProposal.name: str` — unconstrained string.
   - No validator tying names to reference partition.

3. **Prompt template** (`decomposition/llm/prompts.py`):
   - Grep for `Faculty`, `Student`, `Grade`, `Finance`, `Attendance`, `Library` as **required labels**: **no matches**.
   - C0 lists **functional areas** with capability text; in SEMANTIC arm ids are `faculty`, `student`, …; in ANON arm ids are `Area_01`…`Area_06`.
   - These are **input context**, not mandated **output** service names.

4. **Scoring** (`decomposition/evaluation/gold.py`):
   - Gold partition uses lowercase service keys (`faculty`, `student`, …) **only inside evaluation code**, not in LLM prompts.

### Classification

**Not a BLOCKER** for execution on schema grounds.

### Residual risk (disclosed, not schema leakage)

Models may **voluntarily** echo domain words in `services[].name` because of semantic evidence (capabilities, entities, narratives). That is **behavioral**, not schema-enforced reference labels.
