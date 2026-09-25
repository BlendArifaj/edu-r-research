# PETCLINIC_EXT_V1 — Gemini model amendment

**Amendment ID:** `PETCLINIC_EXT_V1_AMENDMENT_GEMINI_38`  
**Date:** 2026-09-26  
**Status:** Approved (infrastructure substitution)

## Reason

Google Generative Language API returns HTTP **404** for `gemini-2.5-flash` on this account:

> This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.8-flash …

This is an **availability** constraint, not a prompt/evidence change. GPT-4o-mini and Llama 3.1 8B runs (PET-021–PET-060) are unchanged.

## Change (Gemini cells only, PET-001–PET-020)

| Field | Before | After |
|-------|--------|--------|
| `model` | `gemini-2.5-flash` | `gemini-3.8-flash` |
| `requested_model_id` | `gemini-2.5-flash` | `gemini-3.8-flash` |
| `pair_id` prefix | `gemini-2.5-flash\|…` | `gemini-3.8-flash\|…` |
| `expected_output_path` | `…/gemini-25-flash/…` | `…/gemini-38-flash/…` |

**Unchanged:** execution order, pair order, prompts, evidence, identifier map, reference mapping, temperature, repetitions, scoring, GPT/Llama rows.

## Reporting

- Label the Gemini family as **Gemini 3.8 Flash** (`gemini-3.8-flash`) in external-validation results.
- Do not claim bitwise comparability to EDU-R runs that used Gemini 2.5 Flash without stating the model-ID change.
- Prior `gemini-25-flash` output dirs are **failed infra attempts** only (empty raw); not used in scoring.

## Re-execution

```bash
export GEMINI_API_KEY="..."
python external_validation_petclinic/scripts/execute_petclinic.py --models gemini-3.8-flash
python external_validation_petclinic/scripts/score_petclinic.py
python external_validation_petclinic/scripts/analyze_petclinic.py
```

Results freeze tag remains `petclinic-ext-v1-results` with this amendment cited in `PETCLINIC_EXT_V1_RESULTS_FREEZE.md`.
