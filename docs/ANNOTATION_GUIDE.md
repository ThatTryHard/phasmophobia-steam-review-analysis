# Blinded Human Annotation Guide

## Why this protocol exists

> Critical fix: sentiment must be inferred from text, not copied from Steam's
> recommendation or from a heuristic/AI draft.

Annotator A labels all 262 rows. Annotator B independently labels the supplied
80-row file. Do not show either annotator the raw source, Steam recommendation,
playtime, the other annotator's file, model output, keyword flags, or the old
repository. Do not discuss individual rows until both files are complete.

Save CSV files as UTF-8. Do not reorder columns, change `review_id`, or edit
`review_text`. Blank `secondary_themes` and `annotation_notes` are allowed;
every other annotation field is required.

For easier coding, each annotator may instead use their separate `.xlsx` form.
It contains dropdown validation and the same blinded rows; never exchange forms
until both are complete. Import a saved form back into the canonical CSV with:

```bash
python -m phasma_review.cli import-workbook \
  data/annotations/annotator_a_all_262.xlsx --annotator a
python -m phasma_review.cli import-workbook \
  data/annotations/annotator_b_blind_80.xlsx --annotator b
```

The importer rejects edited IDs/text, invalid codebook values, and a stale form
that would overwrite more-complete CSV work.

## Decision order

1. Assign `language_status` from the text alone.
2. Decide whether the text supplies enough interpretable evaluative evidence.
3. If insufficient, use `Not_applicable` for sentiment and theme.
4. If sufficient, assign one sentiment composition and one primary theme.
5. Record annotation confidence based on evidence clarity, not personal
   certainty about the game.

## Field definitions

### `language_status`

| Value | Operational definition |
|---|---|
| `English` | The evaluative content is primarily intelligible English. Common gaming terms, names, and emojis do not change this. |
| `Non-English` | Evaluative content is not in English. Do not translate it for this study. |
| `Mixed/Uncertain` | Multiple languages materially contribute, or the language cannot be identified confidently. |

### `text_informativeness`

| Value | Operational definition |
|---|---|
| `Sufficient` | The text contains interpretable evidence about the game/player experience, even if brief, sarcastic, or mixed. |
| `Insufficient` | Empty/gibberish, only an unrelated token, an uninterpretable meme, or non-English content that cannot be coded under this English-language protocol. |

Do not use a fixed word-count rule. “Fun” can be sufficient; a long copypasta
can be insufficient.

### `sentiment_composition`

| Value | Operational definition |
|---|---|
| `Positive_only` | Evaluative content is favorable with no material criticism. |
| `Negative_only` | Evaluative content is unfavorable with no material praise. |
| `Mixed` | Material favorable and unfavorable evaluations both appear, including praise qualified by a consequential complaint. |
| `Neutral_non_evaluative` | Intelligible/informative content describes, requests, jokes, or asks something without a defensible positive/negative evaluation. |
| `Not_applicable` | Required when `text_informativeness` is `Insufficient`. |

Judge expressed content, not an assumed overall verdict. Do not turn sarcasm
into a label unless the textual cue is defensible. Explain difficult sarcasm in
`annotation_notes`.

### `primary_theme`

Choose the single theme carrying the main point.

| Value | Operational definition |
|---|---|
| `Gameplay_praise` | Enjoyment, scares, co-op experience, mechanics, or value. |
| `Technical_issue` | Bugs, crashes, lag, control/animation failures, or performance. |
| `Update_or_change` | A patch, rework, new/removed feature, or design change is central. |
| `Nostalgia_or_loss` | Explicit preference for an earlier state or perceived decline. |
| `Feature_request` | A requested feature/change is central. |
| `Humor_or_meme` | The main function is humor, meme, or playful performance. |
| `General_evaluation` | Overall evaluation without a more specific central theme. |
| `Other` | Sufficient content outside the listed themes; explain in notes. |
| `Not_applicable` | Required when text is insufficient. |

### `secondary_themes`

Optional. Use semicolon-separated values from the theme list, excluding the
primary theme and `Not_applicable`. Do not create new spellings.

### `annotation_confidence`

| Value | Operational definition |
|---|---|
| `High` | Direct evidence; another trained annotator should reach the same code. |
| `Medium` | Some ambiguity, but one code is better supported. |
| `Low` | Sarcasm, language uncertainty, or competing interpretations materially affect the code. Add a note. |

## Agreement and adjudication

After both files are complete, run:

```bash
python -m phasma_review.cli build-adjudication
```

The report calculates percent agreement and Cohen's κ. A third human
adjudicator—or a documented consensus meeting after independent coding—fills
every `final_*` field in the generated Excel adjudication form. The queue also includes any
exact duplicate texts that Annotator A coded inconsistently. Adjudicators must
apply this codebook, not default to Steam recommendation or majority vote.

Import the completed form with:

```powershell
python -m phasma_review.cli import-adjudication-workbook path/to/completed_adjudication.xlsx
```

The importer rejects changes to IDs, review text, disagreement reasons, or the
original A/B labels. The finalized label file is generated by code; never edit
it manually.
