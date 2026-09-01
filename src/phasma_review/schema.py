"""Annotation codebook constants and validation rules.

Critical fix: sentiment is now judged from review text alone. Steam
recommendation is not an annotation field and mismatch is derived only after
human labels are finalized.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

LANGUAGE_VALUES = ("English", "Non-English", "Mixed/Uncertain")
INFORMATIVENESS_VALUES = ("Sufficient", "Insufficient")
SENTIMENT_VALUES = (
    "Positive_only",
    "Negative_only",
    "Mixed",
    "Neutral_non_evaluative",
    "Not_applicable",
)
THEME_VALUES = (
    "Gameplay_praise",
    "Technical_issue",
    "Update_or_change",
    "Nostalgia_or_loss",
    "Feature_request",
    "Humor_or_meme",
    "General_evaluation",
    "Other",
    "Not_applicable",
)
CONFIDENCE_VALUES = ("High", "Medium", "Low")

ANNOTATION_COLUMNS = [
    "review_id",
    "review_text",
    "language_status",
    "text_informativeness",
    "sentiment_composition",
    "primary_theme",
    "secondary_themes",
    "annotation_confidence",
    "annotation_notes",
]

CORE_LABEL_COLUMNS = [
    "language_status",
    "text_informativeness",
    "sentiment_composition",
    "primary_theme",
]

# Critical fix: confidence is required for every completed human annotation.
# It is excluded from agreement/adjudication because confidence is metadata,
# not a semantic label on which annotators must agree.
REQUIRED_LABEL_COLUMNS = CORE_LABEL_COLUMNS + ["annotation_confidence"]


class AnnotationIncompleteError(RuntimeError):
    """Raised when downstream analysis is attempted before human labeling."""


@dataclass(frozen=True)
class AnnotationValidation:
    valid: bool
    completed_rows: int
    total_rows: int
    errors: tuple[str, ...]


def _clean(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def validate_annotations(frame: pd.DataFrame) -> AnnotationValidation:
    errors: list[str] = []
    missing_columns = [column for column in ANNOTATION_COLUMNS if column not in frame]
    if missing_columns:
        return AnnotationValidation(
            valid=False,
            completed_rows=0,
            total_rows=len(frame),
            errors=(f"Missing annotation columns: {missing_columns}",),
        )

    cleaned = frame.copy()
    for column in ANNOTATION_COLUMNS:
        cleaned[column] = _clean(cleaned[column])

    completed_mask = cleaned[REQUIRED_LABEL_COLUMNS].ne("").all(axis=1)

    allowed = {
        "language_status": set(LANGUAGE_VALUES),
        "text_informativeness": set(INFORMATIVENESS_VALUES),
        "sentiment_composition": set(SENTIMENT_VALUES),
        "primary_theme": set(THEME_VALUES),
        "annotation_confidence": set(CONFIDENCE_VALUES),
    }
    for column, values in allowed.items():
        invalid = sorted(set(cleaned.loc[cleaned[column].ne(""), column]) - values)
        if invalid:
            errors.append(f"Invalid {column} values: {invalid}")

    sufficient = cleaned["text_informativeness"].eq("Sufficient")
    insufficient = cleaned["text_informativeness"].eq("Insufficient")
    if (sufficient & cleaned["sentiment_composition"].eq("Not_applicable")).any():
        errors.append("Sufficient rows cannot use sentiment Not_applicable.")
    if (sufficient & cleaned["primary_theme"].eq("Not_applicable")).any():
        errors.append("Sufficient rows cannot use primary_theme Not_applicable.")
    if (
        insufficient & ~cleaned["sentiment_composition"].isin(["", "Not_applicable"])
    ).any():
        errors.append("Insufficient rows must use sentiment Not_applicable.")
    if (insufficient & ~cleaned["primary_theme"].isin(["", "Not_applicable"])).any():
        errors.append("Insufficient rows must use primary_theme Not_applicable.")

    for index, value in cleaned["secondary_themes"].items():
        if not value:
            continue
        secondary = [item.strip() for item in value.split(";") if item.strip()]
        invalid_secondary = sorted(set(secondary) - set(THEME_VALUES))
        if invalid_secondary:
            errors.append(
                f"Row {index} has invalid secondary_themes: {invalid_secondary}"
            )
        if "Not_applicable" in secondary:
            errors.append(
                f"Row {index} cannot use Not_applicable as a secondary theme."
            )
        if cleaned.at[index, "primary_theme"] in secondary:
            errors.append(f"Row {index} repeats primary_theme in secondary_themes.")
        if len(secondary) != len(set(secondary)):
            errors.append(f"Row {index} repeats a secondary theme.")

    low_without_note = cleaned["annotation_confidence"].eq("Low") & cleaned[
        "annotation_notes"
    ].eq("")
    if low_without_note.any():
        errors.append("Low-confidence rows require annotation_notes.")
    other_without_note = cleaned["primary_theme"].eq("Other") & cleaned[
        "annotation_notes"
    ].eq("")
    if other_without_note.any():
        errors.append("Rows with primary_theme Other require annotation_notes.")

    duplicate_ids = cleaned["review_id"].duplicated().sum()
    if duplicate_ids:
        errors.append(f"Duplicate review_id rows: {duplicate_ids}")

    return AnnotationValidation(
        valid=not errors and bool(completed_mask.all()),
        completed_rows=int(completed_mask.sum()),
        total_rows=len(cleaned),
        errors=tuple(errors),
    )


def derive_relation(recommendation: str, informativeness: str, sentiment: str) -> str:
    """Derive recommendation/text relationship without conflating concepts."""

    if informativeness == "Insufficient":
        return "Insufficient text"
    if sentiment == "Mixed":
        return "Qualified / mixed opinion"
    if sentiment == "Neutral_non_evaluative":
        return "Non-evaluative text"
    if recommendation == "Recommended" and sentiment == "Positive_only":
        return "Aligned positive"
    if recommendation == "Not Recommended" and sentiment == "Negative_only":
        return "Aligned negative"
    if (recommendation == "Recommended" and sentiment == "Negative_only") or (
        recommendation == "Not Recommended" and sentiment == "Positive_only"
    ):
        return "Hard contradiction"
    return "Unclassified"
