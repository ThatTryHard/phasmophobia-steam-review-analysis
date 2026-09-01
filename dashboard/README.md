# Dashboard

After blinded human annotation and adjudication are complete, run:

```bash
python -m phasma_review.cli run-all
```

This generates a self-contained results dashboard at `reports/dashboard.html`
and its source tables under `data/dashboard/`. Missing metadata is represented
as `Unknown`; uncertainty and denominators are displayed; qualitative model
errors follow a deterministic diagnostic selection rule.

The public dashboard is deployed from `docs/index.html` through GitHub Pages.
