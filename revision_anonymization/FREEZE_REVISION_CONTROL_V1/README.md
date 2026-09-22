# REVISION_CONTROL_V1 — reproducibility freeze index

**Status:** FROZEN (no further LLM execution, rescoring, or protocol changes without a new protocol ID).

This directory documents **what** constitutes the accepted revision experiment snapshot. Binary artifacts remain at their canonical paths (hashed in `../FINAL_ARTIFACT_MANIFEST.sha256`).

| Category | Location |
|----------|----------|
| Provenance metadata | `PROVENANCE.json` |
| SHA-256 manifest | `../FINAL_ARTIFACT_MANIFEST.sha256` |
| Frozen publication numbers | `../results/PUBLICATION_RESULTS_FREEZE.md` |
| Full analysis report | `../results/REVISION_CONTROL_RESULTS.md` |
| Claim / reviewer matrices | `../REVISION_CLAIM_MATRIX.md`, `../REVIEWER_RESOLUTION_MATRIX.md` |

**Regenerate checksums only** (after intentional artifact change):

```bash
cd sems-research
python3 revision_anonymization/scripts/generate_final_manifest.py   # if added; else use freeze workflow documented in PROVENANCE.json
```

At freeze time, manifest was generated from the complete 120-run tree under `outputs/runs/anonymization_exp_v1/`.
