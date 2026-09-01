# Phasmophobia Steam Review Analysis — audited rebuild

This repository studies one precise question:

> Within the available Phasmophobia review corpus, how often does the text
> express clear agreement, a qualified/mixed opinion, non-evaluative content,
> insufficient evidence, or a hard contradiction relative to Steam's binary
> recommendation?

The original project could not answer that question reliably. Its 171 labeled
rows were selected with label-related heuristics, 133 labels began as
AI-assisted drafts, annotators could see Steam recommendation signals, and one
small random split was repeatedly reused. Those results, the fitted model, and
the Tableau workbook have been retired. They must not be quoted.

## Current evidence status

**The planned annotation and internal evaluation are complete.** Annotator A
labeled all 262 reviews, Annotator B independently labeled 80 reviews including
the full locked-test partition, and all 10 semantic disagreements received
documented final human decisions. No legacy or AI-assisted label was reused.

| Gate | Evidence | Status |
|---|---|---|
| 1. Annotation A | One human labels all 262 texts blind | Complete |
| 2. Annotation B | Second human labels 80 texts, including all locked-test rows | Complete |
| 3. Adjudication | Resolve every semantic or duplicate-text inconsistency | Complete: 10/10 rows |
| 4. Analysis | Full 262-row corpus with distinct outcomes | Complete |
| 5. Internal validation | Repeated group CV plus one locked-test evaluation | Complete |
| 6. External validity | ≥100 later, independent, blindly labeled eligible reviews | Not yet available |

The annotation files expose only randomized `review_id` and `review_text`.
Steam recommendation, playtime, dates, heuristic flags, and prior labels are
absent, so annotators cannot use them as shortcuts.

## Final results

Agreement between the two humans was strong: Cohen's κ was **0.836** for text
informativeness, **0.869** for sentiment composition, and **0.910** for primary
theme (80 double-annotated rows). Exact counts and field-level agreement are in
[`reports/annotation_quality.md`](reports/annotation_quality.md).

Within this observed corpus—not the full Steam-review population—the final
recommendation/text relationships were:

| Relationship | Count | Estimate | 95% Wilson interval |
|---|---:|---:|---:|
| Hard contradiction | 3/262 | 1.1% | 0.4%–3.3% |
| Qualified / mixed opinion | 45/262 | 17.2% | 13.1%–22.2% |
| Non-evaluative text | 31/262 | 11.8% | 8.5%–16.3% |
| Insufficient text | 31/262 | 11.8% | 8.5%–16.3% |

The one-standard-error rule selected the word 1–2 gram TF-IDF/logistic model.
On the 44-row locked test it achieved **0.623 macro F1** (95% group-bootstrap
interval **0.436–0.755**) and **0.659 accuracy** (**0.488–0.793**). Point
estimates exceeded the Steam-label mapping baseline (macro F1 **0.353**) and
most-frequent baseline (**0.151**), but the test set remains small and this is
not external or production validation. See
[`reports/model_validation.md`](reports/model_validation.md).

## What was fixed

### Critical

- The full 262-row observed corpus is labeled; no sentiment-enriched subsample
  is used to estimate prevalence.
- Author names, Steam IDs, recommendation IDs, legacy labels, and heuristic
  flags are removed.
- Development/test assignment is locked before human labeling. Exact duplicate
  text groups cannot cross the boundary.
- All test rows receive two independent human annotations. Every semantic
  disagreement is adjudicated before evaluation.
- `Mixed`, `Neutral_non_evaluative`, `Insufficient text`, and `Hard
  contradiction` are separate; “mismatch” is never a catch-all class.

### Major

- Models are compared with repeated stratified **group** cross-validation using
  macro F1, balanced accuracy, class-level metrics, and uncertainty intervals.
- A most-frequent baseline and a transparent Steam-label mapping baseline are
  reported before text models.
- Candidate models and hyperparameters are deliberately narrow and fixed. A
  one-standard-error rule prefers the simplest model close to the best CV mean.
- Missing playtime and purchase flags remain missing/`Unknown`; they are not
  silently imputed as zero or false.
- Full-corpus proportions include denominators and Wilson intervals; behavioral
  medians include bootstrap intervals; sparse association tables are flagged.
- Duplicate handling, annotation confidence, and player-hour cut points receive
  prespecified sensitivity checks.

### Minor and operational

- All paths resolve from the repository root, random seeds are centralized, and
  dependencies/Python are pinned.
- One canonical feature module replaces divergent notebook logic. Phrase-aware
  boundaries prevent substring mistakes such as matching `lag` inside `flag`.
- The generated dashboard uses an explicit deterministic error-audit sample,
  never a cherry-picked “representative examples” claim.
- The model manifest says `production_approved: false`. No business confidence
  threshold is guessed.

See [reports/IMPLEMENTATION_NOTES.md](reports/IMPLEMENTATION_NOTES.md) for the
issue-by-issue audit trail.

## Reproduce the project

Use Python 3.12 and run from the repository root:

```bash
python -m pip install -r requirements-lock.txt
python -m pip install -e .
python -m phasma_review.cli status
```

Then follow [docs/ANNOTATION_GUIDE.md](docs/ANNOTATION_GUIDE.md). After both
annotators finish:

```bash
python -m phasma_review.cli build-adjudication
python -m phasma_review.cli import-adjudication-workbook path/to/completed_adjudication.xlsx
python -m phasma_review.cli run-all
python -m pytest
```

`run-all` executes in dependency order and stops immediately if annotations or
adjudication are incomplete. It creates:

- analysis tables under `data/processed/`;
- audited dashboard tables under `data/dashboard/`;
- the research model and manifest under `models/`;
- stakeholder reports and `reports/dashboard.html` under `reports/`.

The notebooks are thin, ordered interfaces to the tested package code. Rebuild
them with `python scripts/build_notebooks.py`.

## Repository layout

```text
data/raw/            deidentified observed corpus and immutable split manifest
data/annotations/    blinded templates and human adjudication workspace
data/external/       future-update temporal validation contract
src/phasma_review/   tested source of truth
notebooks/           ordered audit/reproduction interface
scripts/             notebook and integrity helpers
tests/               unit and pipeline-invariant tests
reports/             audit notes and generated reports
dashboard/           dashboard contract (legacy workbook retired)
```

## Methodological limits

The source file covers one game and a five-day review window (2026-06-09 through
2026-06-13). Its
scraping completeness, language filter, ordering, and inclusion probability
were not preserved well enough to call it representative of all Steam reviews
or players. Wilson/bootstrap intervals quantify finite-sample uncertainty under
a conditional sampling interpretation; they do not repair selection bias.
Playtime associations are observational, not causal. Reviews may be duplicated,
sarcastic, multilingual, or update-specific. Cross-game and post-update
performance are unknown until the external validation gate passes.

The tradeoff between labeling more data and fitting a more complex model is
resolved in favor of label validity and simple baselines. With only 262 observed
rows, increasing model complexity would manufacture variance, not evidence.

## Production status

This is a reproducible research/portfolio pipeline, not a production service.
It has no latency SLO, monitoring owner, human-review SLA, business error-cost
matrix, or approved abstention threshold. Do not automate moderation, player
decisions, employee decisions, or any other consequential action with it.
