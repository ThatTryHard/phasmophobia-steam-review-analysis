# Data Card

## Dataset

`data/raw/reviews.csv` is a deidentified 262-row corpus migrated from the
project's original expanded raw file. It contains 197 `Recommended` and 65 `Not
Recommended` rows. Review dates span 2026-06-09 through 2026-06-13. The exact
Steam query parameters, pagination completeness, sort
order, retry behavior, and inclusion probabilities were not preserved by the
original collection process.

## Retained fields

- randomized review and normalized-text-group IDs;
- pre-label development/test partition;
- review date and text;
- Steam recommendation;
- playtime and engagement counts;
- purchase/free/early-access flags, including genuine missing values.

## Removed fields

Author display names, Steam IDs, recommendation IDs, old manual/AI labels,
keyword-selection flags, and scraper-only display strings are not part of the
audited data contract. Randomized IDs cannot be joined back to the removed
identity fields within this repository.

## Known quality limits

- There are 250 normalized-text groups; 19 rows belong to a duplicated group.
  Duplicates are grouped, not silently ignored.
- One legacy pilot row lacks most structured metadata; missing remains missing.
- Language was not trusted from the scraper; blinded humans assign a language
  status from text.
- Playtime is self/platform-reported metadata and may be missing or stale.
- Review text is public but can contain personal or offensive language. Do not
  republish unnecessary raw examples.

## Representativeness

This is not a probability sample. It cannot support claims about all players,
non-reviewers, other games, other languages, or later updates. Recommendation
balance must not be mistaken for player sentiment prevalence.

## Permitted use

Use for reproducible educational/research analysis of this observed corpus.
Do not use for consequential person-level decisions, harassment, author
profiling, or production moderation.
