# Analysis Report

> Major fix: results below use all observed reviews and adjudicated human labels. Mixed, non-evaluative, insufficient, and contradictory text are not collapsed.

## Scope and estimand

The corpus contains **262 review rows** and **250 unique normalized texts**. Results describe this available Phasmophobia review file. Collection coverage outside this file is not documented well enough to claim representativeness of all players, all Steam reviews, other games, or future updates.

## Recommendation/text relationship

| Relationship | Count | Estimate | 95% Wilson interval |
|---|---:|---:|---:|
| Hard contradiction | 3/262 | 1.1% | 0.4%–3.3% |
| Qualified / mixed opinion | 45/262 | 17.2% | 13.1%–22.2% |
| Non-evaluative text | 31/262 | 11.8% | 8.5%–16.3% |
| Insufficient text | 31/262 | 11.8% | 8.5%–16.3% |

Intervals express sampling-style uncertainty conditional on treating this corpus as a sample from a broader review process. They are not a correction for unknown selection bias.

## Behavioral analysis

Playtime and engagement summaries use medians, interquartile ranges, and 2,000-draw bootstrap intervals. Missing playtime remains missing and is counted explicitly.

## Association tests

The prespecified chi-square tables are exploratory; **2** table(s) have expected cell counts below five. P-values are not used as causal evidence or as a license for post-hoc storytelling.

## Robustness limits

Results are recomputed after deduplicating normalized text, excluding low-confidence annotations, and changing playtime cut points. A future-update temporal validation set is still required before any claim of stability under concept drift.
