# Model Validation Report

> Model selection uses repeated stratified group CV on development data only. Exact duplicate texts cannot cross folds. The test set is used only after selection.

## Cohort

Eligible adjudicated English/sufficient-text rows: **231**. Development: **187**; locked test: **44**.

## Development cross-validation

| Model | Role | Mean macro F1 | SD | Mean balanced accuracy |
|---|---|---:|---:|---:|
| char_3_5gram_logreg | text_model | 0.619 | 0.029 | 0.621 |
| word_1_2gram_logreg | text_model | 0.613 | 0.019 | 0.621 |
| word_unigram_logreg | text_model | 0.601 | 0.015 | 0.622 |
| steam_recommendation_mapping | metadata_baseline | 0.400 | 0.001 | 0.480 |
| most_frequent | baseline | 0.165 | 0.000 | 0.250 |

Selected text model: **word_1_2gram_logreg**. The one-standard-error rule chose the least complex text model within the prespecified repeat-level CV uncertainty band of the highest mean macro F1. This is a complexity-control heuristic, not a test of statistical equivalence.

## Locked-test results

| Model | Metric | Estimate | 95% group-bootstrap interval |
|---|---|---:|---:|
| word_1_2gram_logreg | accuracy | 0.659 | 0.488–0.793 |
| word_1_2gram_logreg | balanced_accuracy | 0.654 | 0.453–0.808 |
| word_1_2gram_logreg | macro_f1 | 0.623 | 0.436–0.755 |
| most_frequent | accuracy | 0.432 | 0.268–0.600 |
| most_frequent | balanced_accuracy | 0.250 | 0.250–0.250 |
| most_frequent | macro_f1 | 0.151 | 0.106–0.188 |
| steam_recommendation_mapping | accuracy | 0.568 | 0.390–0.717 |
| steam_recommendation_mapping | balanced_accuracy | 0.500 | 0.500–0.500 |
| steam_recommendation_mapping | macro_f1 | 0.353 | 0.258–0.414 |

## Production limit

This artifact is **not approved for production inference**. No operational confidence/abstention threshold is set because false-positive and false-negative costs were not supplied, and the corpus is one game from one five-day window. A separately collected, blindly annotated future-update set of at least 100 reviews must pass the external validation gate first.
