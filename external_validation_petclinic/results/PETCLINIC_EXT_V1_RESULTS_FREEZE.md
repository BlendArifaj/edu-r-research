# PETCLINIC_EXT_V1_RESULTS_FREEZE

- **Gemini model amendment:** `PETCLINIC_EXT_V1_AMENDMENT_GEMINI_MODEL.md` (`gemini-2.5-flash` unavailable on API account → `gemini-3.8-flash` for PET-001–PET-020 only).
- Experiment fingerprint: `4d12dd3bc414d1c7`
- Attempted: 60 | VALID: 60 | MODEL_INVALID: 0 | INFRA: 0
- Monolith SHA: `818c4136ea971c21674525f9053de0d9c7ad8cfe`
- Microservices SHA: `aefaf7fa9eb0ab911a24c346ca0e4dc5837251c7`
- reference_mapping.csv SHA-256: `57071674554b53207fb7f5112768f189c41600cfd119b1883474dae4707d94c7`
- run_manifest.csv SHA-256: `b01d87768e57d16177214d59f122e1be5f574b7ad78e40b3085b16aa72efd980`

## Outcome classification
OUTCOME A + OUTCOME C

## EXT-RQ1 (E0 semantic − anonymized)

- gemini-3.8-flash: delta=0.3098
- gpt-4o-mini: delta=0.59998
- llama3.1: delta=0.54392

## EXT-RQ2 (E1−E0 anonymized)

- gemini-3.8-flash: delta=0.27576
- gpt-4o-mini: delta=0.29648
- llama3.1: delta=0.16216

## Sensitivity consistency

- gemini-3.8-flash: CONSISTENT
- gpt-4o-mini: CONSISTENT
- llama3.1: CONSISTENT

## Cell summary

See `cell_summary.csv`.
