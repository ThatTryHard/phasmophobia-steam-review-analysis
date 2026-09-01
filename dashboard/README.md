# Dashboard status

The previous Tableau workbook was retired because it embedded results from a
heuristic-selected, mostly AI-drafted label set and converted missing pilot
flags to false. It must not be used.

After blinded human annotation and adjudication are complete, run:

```bash
python -m phasma_review.cli run-all
```

This generates a self-contained audited dashboard at
`reports/dashboard.html` and its source tables under `data/dashboard/`.
Missing metadata is represented as `Unknown`; uncertainty and denominators are
included; qualitative errors follow a deterministic selection rule.
