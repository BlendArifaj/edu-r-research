# Frozen retry and failure policy — REVISION_CONTROL_V1

**Protocol:** `anonymization_exp_v2` + execution amendments  
**Frozen before execution:** 2026-09-22  

## A. Infrastructure / transport failure (`INFRA_FAILURE`)

**Examples:** HTTP timeout before body received, connection error, provider 5xx, rate-limit 429, Ollama unreachable, digest mismatch abort.

**Policy:**

- Maximum **2 infrastructure retries** per run (`max_infra_retries = 2` → up to **3** transport attempts).
- Exponential backoff: 5s, 15s (fixed schedule).
- Log every attempt in `attempt_log.jsonl` under the run directory.
- Last error stored in metadata `invalid_reason` / `infra_error`.
- If still failing: `execution_status = INFRA_FAILURE`, `parse_status = not_applicable`.
- **Do not** add replacement experimental runs beyond the 120 manifest slots.

## B. Model output failure (experimental outcome)

**Examples:** invalid JSON, schema validation error, incomplete response, duplicate/missing components after parse.

**Policy:**

- **No retries** for output quality (no “fix your JSON” follow-up prompts).
- Single provider response per successful transport.
- Store `raw_response.txt` as received.
- `execution_status = COMPLETED`, `parse_status = invalid` (or `valid`).
- `parsed.json` = `null` when invalid.
- Counts toward **invalid model outputs**, not infra failures.

## Metadata fields (per run)

| Field | Description |
|-------|-------------|
| `attempt_count` | Total transport attempts |
| `infra_retry_count` | `attempt_count - 1` |
| `execution_status` | `COMPLETED`, `INFRA_FAILURE`, `SKIPPED` |
| `parse_status` | `valid`, `invalid`, `not_applicable` |
| `invalid_reason` | Parse/validation message or infra error |
| `resolved_model_version` | Provider metadata when available |

## Llama-specific

Before **each** Llama run (and each Llama pair batch), executor verifies digest matches `llama_digest_frozen.txt`. On mismatch: **ABORT entire experiment** (no silent continuation).
