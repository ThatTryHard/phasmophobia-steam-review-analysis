# Reproducibility Contract

- Python: `3.12.*` (`.python-version` records the build used here).
- Dependencies: a fully resolved Python 3.12/Linux environment in
  `requirements-lock.txt`; concise direct requirements remain in
  `requirements.txt`.
- Seed: `20260813`, centralized in `src/phasma_review/utils.py`.
- Paths: resolved from repository root or explicit `PHASMA_PROJECT_ROOT`.
- Split: stored in `data/raw/split_manifest.csv` and hashed in the model
  manifest.
- Source: row counts, date scope, missingness, privacy removals, and SHA-256
  checksums are stored in `data/raw/source_manifest.json`.
- Label provenance: human single/agreed/adjudicated status is retained per row.
- Generated outputs: rebuilt through CLI commands, not hand-edited notebooks.

Run:

```bash
python -m pip install -r requirements-lock.txt
python -m pip install -e .
python -m pytest
python -m phasma_review.cli status
```

After annotation/adjudication:

```bash
python -m phasma_review.cli run-all
```

The test suite checks privacy columns, split/group isolation, blinded-template
schema, label validation, phrase boundaries, and model-selection logic. A clean
run from blank labels is expected to stop at the evidence gate; that is correct
behavior, not a failed reproduction.
