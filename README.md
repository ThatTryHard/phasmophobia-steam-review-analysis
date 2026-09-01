# Phasmophobia Steam Review Analysis

Human-annotated NLP study of written sentiment and Steam recommendations.

**Live dashboard:** [Explore the results](https://thattryhard.github.io/phasmophobia-steam-review-analysis/)

**Release:** [v2.0.0](https://github.com/ThatTryHard/phasmophobia-steam-review-analysis/releases/tag/v2.0.0)

## Project overview

Steam reviews reduce player feedback to a binary `Recommended` or
`Not Recommended` signal, even when the written text is qualified, mixed,
non-evaluative, or too limited to interpret. This project examines one focused
question:

> Within the available Phasmophobia review corpus, how does sentiment expressed
> in review text relate to Steam's binary recommendation?

The study uses 262 de-identified reviews collected from 9 to 13 June 2026. All
reviews were labeled from text alone by a primary human annotator. A second
human independently labeled 80 reviews, including the complete locked
evaluation partition, and all 10 disagreements were adjudicated before analysis.

## Key findings

Agreement between annotators was strong. Cohen's kappa was **0.836** for text
informativeness, **0.869** for sentiment composition, and **0.910** for primary
theme across the 80 double-annotated reviews.

Within this observed corpus, the final recommendation and text relationships
were:

| Relationship | Count | Estimate | 95% Wilson interval |
|---|---:|---:|---:|
| Hard contradiction | 3/262 | 1.1% | 0.4% to 3.3% |
| Qualified or mixed opinion | 45/262 | 17.2% | 13.1% to 22.2% |
| Non-evaluative text | 31/262 | 11.8% | 8.5% to 16.3% |
| Insufficient text | 31/262 | 11.8% | 8.5% to 16.3% |

These estimates describe the collected five-day corpus. They are not estimates
for all Phasmophobia players or all Steam reviews.

## Annotation design

- Annotator A labeled all 262 review texts.
- Annotator B independently labeled 80 texts, including every row assigned to
  the locked evaluation partition.
- Recommendation, playtime, dates, heuristic flags, and prior labels were hidden
  during annotation.
- Sentiment composition, informativeness, primary theme, and confidence were
  recorded as separate fields.
- Every semantic disagreement was resolved before final labels were generated.

Exact agreement results are available in
[`reports/annotation_quality.md`](reports/annotation_quality.md), and the full
codebook is documented in [`docs/ANNOTATION_GUIDE.md`](docs/ANNOTATION_GUIDE.md).

## Analysis design

- All 262 observed reviews are included in descriptive corpus summaries.
- Hard contradiction, mixed opinion, non-evaluative text, and insufficient text
  remain distinct categories.
- Exact normalized-text duplicates are assigned to the same data partition.
- Missing playtime and purchase fields remain missing or `Unknown`.
- Proportions include denominators and Wilson intervals.
- Behavioral medians include nonparametric bootstrap intervals.
- Duplicate handling, annotation confidence, and alternate playtime cut points
  receive sensitivity checks.
- Association tests are interpreted as exploratory, not causal.

## Model validation

Eligible English reviews with sufficient text were divided into development and
locked-test cohorts using the preassigned duplicate-aware partition. Candidate
models were compared only on development data with repeated stratified group
cross-validation.

The comparison includes:

- a most-frequent baseline;
- a transparent Steam-recommendation mapping baseline;
- word-unigram TF-IDF with Logistic Regression;
- word 1-2 gram TF-IDF with Logistic Regression;
- character 3-5 gram TF-IDF with Logistic Regression.

The one-standard-error rule selected the word 1-2 gram model. On the 44 eligible
locked-test reviews, it achieved:

| Metric | Estimate | 95% group-bootstrap interval |
|---|---:|---:|
| Accuracy | 0.659 | 0.488 to 0.793 |
| Balanced accuracy | 0.654 | 0.453 to 0.808 |
| Macro F1 | 0.623 | 0.436 to 0.755 |

The Steam mapping baseline achieved **0.353 macro F1**, while the most-frequent
baseline achieved **0.151**. The complete comparison and class-level metrics are
in [`reports/model_validation.md`](reports/model_validation.md).

## Project architecture

The repository separates analytical presentation from reusable implementation.
The ordered notebooks describe the research workflow, while annotation
validation, feature engineering, statistical analysis, model evaluation, and
dashboard generation live in the tested `phasma_review` package under `src/`.

This structure allows the same implementation to run through Jupyter, the
command line, automated tests, and GitHub Actions without duplicating analytical
logic or relying on notebook execution state.

```text
data/raw/            de-identified corpus and immutable split manifest
data/annotations/    blinded annotation and adjudication files
data/processed/      final labels, analysis tables, and model results
data/dashboard/      generated dashboard tables
data/external/       future temporal-validation contract
src/phasma_review/   reusable pipeline implementation
notebooks/           ordered research workflow
scripts/             notebook generation and integrity checks
tests/               unit and end-to-end pipeline tests
reports/             generated analysis and validation reports
docs/                methodology, data card, model card, and Pages site
```

## Reproduce the project

Use Python 3.12 and run from the repository root:

```bash
python -m pip install -r requirements-lock.txt
python -m pip install -e .
python -m phasma_review.cli status
python -m phasma_review.cli run-all
python scripts/audit_invariants.py
python -m pytest
```

The pipeline enforces annotation, adjudication, duplicate-group, and artifact
integrity requirements before generating downstream results. Detailed setup
instructions are available in
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).

## Limitations

- The corpus covers one game and a five-day review window.
- Original scraping coverage, ordering, and inclusion probabilities were not
  preserved well enough to establish population representativeness.
- Wilson and bootstrap intervals quantify uncertainty conditional on the
  observed corpus; they do not correct unknown selection bias.
- Playtime and recommendation relationships are observational and not causal.
- The locked test contains only 44 eligible reviews, so uncertainty remains
  substantial.
- Cross-game and future-update performance have not been established.

## Model status

The saved model is a research artifact, not a production service. It has no
approved operating threshold, monitoring policy, business error-cost matrix, or
external temporal validation. It should not be used for consequential automated
decisions.

## Version history

Version `v2.0.0` introduced the current human-annotation, grouped-validation,
and reproducibility design. Historical implementation decisions and retired
artifacts are documented separately in
[`reports/IMPLEMENTATION_NOTES.md`](reports/IMPLEMENTATION_NOTES.md).
