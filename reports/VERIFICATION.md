# Verification Record

Verified on 2026-08-31 with Python 3.12.13. The resolved dependency lock had
also been installed and exercised in a clean Python 3.12 environment during
the rebuild.

## Automated checks

| Check | Result |
|---|---|
| Fully resolved dependency installation | Pass |
| Editable package build without build isolation | Pass |
| `pip check` dependency consistency | Pass |
| Python source compilation | Pass |
| Test suite | **21 passed** |
| Synthetic analysis → model → dashboard integration | Pass |
| Deidentification and forbidden-column check | Pass |
| Duplicate-group development/test isolation | Pass |
| All locked-test rows present in Annotator B file | Pass |
| CSV ↔ Excel annotation/adjudication equality | Pass |
| Notebook v4 schema and no-stale-output check | Pass |
| Git whitespace/error check | Pass |

## Visual spreadsheet QA

Both human coding forms and the completed 10-row adjudication form were rendered
and inspected. Long review text wraps; header roles are visible;
identifier/text columns are visually distinct from editable fields; category
cells expose dropdown controls; codebook sheets are legible; and no formula
errors are present. Each form was imported through a guarded CLI path and
compared exactly with its canonical CSV.

## Completed evidence gates

`python -m phasma_review.cli status` reports 262/262 valid Annotator A rows,
80/80 valid Annotator B rows, an adjudication queue, and finalized labels. All
10 queued rows have validated final decisions. The full-corpus analysis,
development-only repeated group CV, planned locked-test evaluation, model
manifest, dashboard datasets, and self-contained HTML dashboard were generated
from those finalized labels.

## Evidence still required

Internal annotation and adjudication are complete. A genuinely later,
independently and blindly annotated set of at least 100 eligible reviews is
still required for temporal validation. Until then the model remains
research-only and no operational threshold is approved.
