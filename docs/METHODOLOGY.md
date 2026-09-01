# Prespecified Methodology

## Research question and estimand

The primary estimand is the proportion of rows in the available 262-review
corpus within each recommendation/text relationship category. This is a
descriptive corpus estimand. It is not the population prevalence among all
Phasmophobia players, all Steam reviewers, or all future review windows.

Primary categories are mutually distinct: aligned positive, aligned negative,
hard contradiction, qualified/mixed opinion, non-evaluative text, and
insufficient text.

## Data and split

The privacy-safe migration retains review text, recommendation, date, playtime,
engagement metadata, and purchase-state metadata. Direct and platform-specific
identifiers are removed. Exact normalized text receives a shared
`text_group_id`.

Before any new human label exists, `StratifiedGroupKFold` assigns one fifth of
text groups to `locked_test`, stratified approximately by Steam recommendation.
Recommendation is used only because the target human sentiment is unavailable
at split time. The manifest is then immutable. No normalized text group can
cross development/test.

## Human measurement

Annotator A labels the complete corpus. Annotator B independently labels 80
rows: every locked-test row plus a recommendation-balanced development subset.
Both see only randomized ID and text. Semantic agreement is reported as raw
agreement and Cohen's κ by field. All semantic disagreements and all
within-duplicate inconsistencies require human adjudication.

## Descriptive analysis

All observed rows contribute to full-corpus estimates. Wilson intervals are
reported for proportions; they are conditional uncertainty summaries, not a
selection-bias correction. Medians, quartiles, missing counts, and 2,000-draw
nonparametric bootstrap intervals summarize behavioral variables.

Chi-square tests and Cramér's V are exploratory. Expected counts below five are
flagged. There is no causal identification strategy, random assignment, or
credible control for player self-selection; therefore the report makes no
causal claims.

Prespecified sensitivity analyses cover one row per normalized text versus all
submitted rows, excluding low-confidence annotations, and playtime bins at
10/100, 50/200, and 100/300 hours.

## Modeling

The modeling cohort contains adjudicated English, sufficient-text reviews with
one of four sentiment-composition labels. The target is human-coded text
sentiment; Steam recommendation is not a model feature.

Development comparisons use ten repeats of stratified group CV (up to five
folds, reduced only if the rarest class has fewer distinct groups). Metrics are
macro F1, balanced accuracy, accuracy, and class-level precision/recall/F1.
Prespecified references are a most-frequent classifier and direct mapping from
Steam recommendation to positive/negative sentiment.

Text candidates are fixed TF-IDF logistic-regression pipelines: word unigrams,
word 1–2 grams, and character 3–5 grams. A one-standard-error rule chooses the
least complex candidate whose mean macro F1 is within one standard error of the
best mean. This resolves the “more model capacity versus small data” tradeoff
in favor of lower variance and interpretability.

After selection, the chosen model and two baselines are evaluated once on the
locked test set. Exact text groups are the bootstrap resampling unit for 95%
intervals. Test results do not trigger further tuning.

## Temporal validation and drift

The five-day, one-game source cannot establish post-update stability. A separate
file must contain at least 100 eligible English/sufficient reviews, all dated
after the source window, with no normalized text overlap and independent blind
human labels. `validate-external` enforces those gates. The repository supplies
the contract, not fabricated future data.
