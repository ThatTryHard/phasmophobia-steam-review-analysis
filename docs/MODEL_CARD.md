# Research Model Card

## Status

The model artifact was generated after completed human annotation,
adjudication, and development-only selection. It is **research-only** and
`production_approved: false`.

## Intended use

Compare simple text baselines and audit error types within this fixed
Phasmophobia review study. Predictions are not a replacement for human labels.

## Not intended for

- moderation or sanctions;
- decisions about identifiable people;
- other games, languages, platforms, or future updates without validation;
- estimating recommendation prevalence;
- causal inference;
- unattended online inference.

## Input and output

Input is cleaned English review text. Output is a probability distribution and
one of `Positive_only`, `Negative_only`, `Mixed`, or
`Neutral_non_evaluative`. Insufficient/non-English text is outside the model's
validated input scope.

## Selection and evaluation

Three fixed TF-IDF/logistic candidates are compared with repeated stratified
group CV on development data. A one-standard-error rule prefers simplicity.
The locked test was evaluated once with group-bootstrap intervals. The selected
word 1–2 gram TF-IDF/logistic model reached 0.623 macro F1 (95% interval
0.436–0.755) and 0.659 accuracy (0.488–0.793) on 44 eligible locked-test rows.
The corresponding Steam-label baseline macro F1 was 0.353. Full class-level
metrics appear in `reports/model_validation.md`; no legacy performance claim is
retained.

## Failure modes

Expected failures include sarcasm, memes, mixed praise/criticism, very short
text, new update vocabulary, multilingual text, and class shifts. Exact
duplicate handling does not address near-duplicates or coordinated copy-paste
campaigns. Confidence is not calibrated for a business decision.

## Fairness and ethics

The source lacks reliable demographic attributes, so demographic fairness
cannot be measured. Absence of a measured disparity is not evidence of
fairness. Language restriction creates a known coverage disparity. Review
authors must not be identified or profiled.

## Operational threshold

Unset. The user selected a portfolio/research pipeline and did not provide the
cost of false positives, false negatives, abstentions, or human review. The
pipeline therefore refuses to manufacture an approval threshold. Any future
deployment needs a cost matrix, calibrated probabilities, target coverage,
monitoring owner, rollback plan, and external temporal validation.
