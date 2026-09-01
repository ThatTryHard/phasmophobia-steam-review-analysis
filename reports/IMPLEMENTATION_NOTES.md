# Audit Remediation Log

This log maps every ranked weakness to a concrete implementation. Comments
immediately above the relevant source sections state what changed and why.

## Critical

| Weakness before | Fix after | Evidence |
|---|---|---|
| Heuristic-selected 171-row label set invalidated prevalence claims | Label and analyze all 262 observed rows | `prepare.py`, `analysis.py` |
| 133 AI-assisted drafts and visible recommendation cues created circular labels | Two blinded human files expose only ID/text; all test rows double-coded | annotation templates, `ANNOTATION_GUIDE.md` |
| “Mismatch” conflated mixed, ambiguous, and contradictory text | Prespecified separate sentiment and relationship categories | `schema.py` |
| One small reusable split and duplicate contamination risk | Split locked before labels; normalized text groups isolated in holdout and CV | `prepare.py`, `modeling.py` |
| No independent reliability/adjudication gate | Agreement/κ, disagreement queue, duplicate-consistency queue, required human adjudication | `annotations.py` |

## Major

| Weakness before | Fix after | Evidence |
|---|---|---|
| No defensible baselines | Most-frequent and Steam-mapping baselines precede text candidates | `modeling.py` |
| Convenient accuracy and point estimates | Macro F1, balanced accuracy, class metrics, Wilson/group-bootstrap intervals | `analysis.py`, `modeling.py` |
| Validation-set tuning risk | Fixed candidates; repeated development group CV; one-standard-error selection | `modeling.py` |
| Missing metadata interpreted as false/zero | Nullable booleans and explicit missing counts/`Unknown` | `prepare.py`, `dashboard.py` |
| Overstated generalizability | Corpus estimand and one-game/one-window limits stated on every report | methodology/data/model cards |
| No drift check | Strict ≥100-row later-date, no-overlap external validation gate | `external_validation.py` |
| Fragile notebook-dependent implementation | Package source of truth, CLI gates, central paths/seeds, tests | `src/`, `tests/`, `Makefile` |

## Minor / polish

| Weakness before | Fix after | Evidence |
|---|---|---|
| Substring keyword errors | Phrase-aware word boundaries | `features.py` |
| Unclear non-English behavior | Human language field and model-scope exclusion | codebook, `modeling.py` |
| Cherry-picked “representative” examples | Deterministic lowest-confidence error audit sample with rule attached | `dashboard.py` |
| Direct platform/user identifiers | Removed from public source and forbidden by tests | `prepare.py`, data card |
| Silent result reuse | Legacy artifacts removed; every downstream stage fails closed | CLI and status command |

## Explicit tradeoff

The original recommendation to broaden data and the recommendation to reduce
complexity do not conflict at the measurement stage: all 262 existing rows are
now labeled. For modeling, the limited sample still cannot support broad model
capacity. Label rigor and simple baselines are prioritized; genuinely broader
evidence is deferred to the future temporal set rather than simulated through
resampling or aggressive tuning.

## Remaining human evidence dependencies

Two items cannot be completed by code without inventing evidence:

1. independent human annotation/adjudication under the supplied codebook;
2. a later review collection for temporal validation.

The pipeline blocks results at both points and states exactly how to satisfy
them. Everything else from the audit is implemented.
