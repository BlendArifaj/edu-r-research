# GEMINI_38_EDUR_RESULTS_FREEZE

- Model: `gemini-3.8-flash` (provider: gemini)
- Experiment fingerprint: `dcbf96ce01f36e01`
- Identifier manifest SHA-256: `82b5996608d30229552cfbd0d426d6d2ed373078fec336aa5e6bc58ea262b41b`
- Historical Gemini 2.5 preserved under `outputs/runs/anonymization_exp_v1/` (unchanged)

## Validity (identifier 40)
{
  "attempted": 40,
  "valid": 39,
  "model_invalid": 1,
  "infra": 0
}

## Identifier pivot (mean pairwise F1)

| Model | Identifier | C0 | C1 | C2 | C3 |
| --- | --- | --- | --- | --- | --- |
| gemini-3.8-flash | SEMANTIC | 0.9245 | 0.9245 | 0.89978 | 0.87158 |
| gemini-3.8-flash | ANONYMIZED | 0.2491 | 0.81952 | 0.82236 | 0.76006 |

## C0 semantic − anonymized delta
0.6754

## Best anonymized
C2 F1=0.82236

## RQ3 (12 semantic)

- C0: compliance=1.0 stability=1.0
- C1: compliance=1.0 stability=0.9649
- C2: compliance=1.0 stability=1.0
- C3: compliance=1.0 stability=1.0
