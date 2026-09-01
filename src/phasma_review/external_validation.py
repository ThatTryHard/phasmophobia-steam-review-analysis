"""Temporal validation gate for reviews collected after the development window."""

from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, recall_score

from .features import clean_review_text, normalized_text_key
from .modeling import MODEL_CLASSES
from .paths import (
    EXTERNAL_RESULTS_PATH,
    EXTERNAL_REVIEWS_PATH,
    MODEL_PATH,
    RAW_REVIEWS_PATH,
)
from .schema import ANNOTATION_COLUMNS, validate_annotations
from .utils import RANDOM_SEED, percentile_interval

EXTERNAL_REQUIRED_COLUMNS = [
    "review_id",
    "review_date",
    "recommendation",
    "review_text",
    "language_status",
    "text_informativeness",
    "sentiment_composition",
    "primary_theme",
    "secondary_themes",
    "annotation_confidence",
    "annotation_notes",
    "annotation_source",
    "annotation_protocol_version",
]


def write_external_template() -> None:
    """Create a schema-only template; never invent future observations."""

    EXTERNAL_REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not EXTERNAL_REVIEWS_PATH.exists():
        pd.DataFrame(columns=EXTERNAL_REQUIRED_COLUMNS).to_csv(
            EXTERNAL_REVIEWS_PATH,
            index=False,
        )


def validate_external_set(minimum_rows: int = 100) -> pd.DataFrame:
    """Evaluate only a genuinely later, independently labeled review set."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError("Fit the research model before external validation.")
    if not EXTERNAL_REVIEWS_PATH.exists():
        raise FileNotFoundError("External validation template/data does not exist.")
    external = pd.read_csv(EXTERNAL_REVIEWS_PATH)
    missing = [column for column in EXTERNAL_REQUIRED_COLUMNS if column not in external]
    if missing:
        raise ValueError(f"External validation file is missing columns: {missing}")
    if len(external) < minimum_rows:
        raise ValueError(
            f"External validation requires at least {minimum_rows} rows; found {len(external)}."
        )
    if external[EXTERNAL_REQUIRED_COLUMNS].isna().any().any():
        raise ValueError("External validation rows must be fully labeled.")
    if external["review_id"].duplicated().any():
        raise ValueError("External review_id values must be unique.")
    invalid_recommendations = sorted(
        set(external["recommendation"]) - {"Recommended", "Not Recommended"}
    )
    if invalid_recommendations:
        raise ValueError(
            f"Unexpected external recommendation values: {invalid_recommendations}"
        )
    allowed_sources = {"human_agreed", "human_adjudicated"}
    if not external["annotation_source"].isin(allowed_sources).all():
        raise ValueError(
            "Every external row must be independently double-coded and use "
            "annotation_source human_agreed or human_adjudicated."
        )
    if not external["annotation_protocol_version"].eq("v2_blind").all():
        raise ValueError("External rows must use annotation_protocol_version v2_blind.")
    annotation_validation = validate_annotations(external[ANNOTATION_COLUMNS])
    if not annotation_validation.valid:
        raise ValueError(
            "External annotation fields fail the codebook: "
            + "; ".join(annotation_validation.errors)
        )

    source = pd.read_csv(RAW_REVIEWS_PATH)
    source_dates = pd.to_datetime(source["review_date"], errors="coerce")
    external_dates = pd.to_datetime(external["review_date"], errors="coerce")
    if external_dates.isna().any():
        raise ValueError("Every external review_date must be parseable.")
    if source_dates.notna().any() and external_dates.min() <= source_dates.max():
        raise ValueError(
            "External reviews must all postdate the source collection window."
        )

    source_keys = set(source["review_text"].map(normalized_text_key))
    external_keys = external["review_text"].map(normalized_text_key)
    if external_keys.isin(source_keys).any():
        raise ValueError("External validation text overlaps the development corpus.")

    cohort = external[
        external["language_status"].eq("English")
        & external["text_informativeness"].eq("Sufficient")
        & external["sentiment_composition"].isin(MODEL_CLASSES)
    ].copy()
    if len(cohort) < minimum_rows:
        raise ValueError(
            f"At least {minimum_rows} eligible English/sufficient rows are required; "
            f"found {len(cohort)}."
        )
    model = joblib.load(MODEL_PATH)
    metric_labels = sorted(model.classes_.tolist())
    unseen_classes = set(cohort["sentiment_composition"]) - set(metric_labels)
    if unseen_classes:
        raise ValueError(
            "External labels include classes the fitted development model never saw: "
            f"{sorted(unseen_classes)}"
        )
    predictions = model.predict(cohort["review_text"].map(clean_review_text))
    y_true = cohort["sentiment_composition"]
    metrics = {
        "accuracy": accuracy_score(y_true, predictions),
        "balanced_accuracy": recall_score(
            y_true,
            predictions,
            labels=metric_labels,
            average="macro",
            zero_division=0,
        ),
        "macro_f1": f1_score(
            y_true,
            predictions,
            labels=metric_labels,
            average="macro",
            zero_division=0,
        ),
    }
    group_keys = cohort["review_text"].map(normalized_text_key).to_numpy()
    unique_groups = np.unique(group_keys)
    group_indices = {
        group: np.flatnonzero(group_keys == group) for group in unique_groups
    }
    rng = np.random.default_rng(RANDOM_SEED + 9_000)
    bootstrap = {metric: [] for metric in metrics}
    y_array = y_true.to_numpy()
    predictions_array = np.asarray(predictions)
    for _ in range(2_000):
        sampled_groups = rng.choice(
            unique_groups, size=len(unique_groups), replace=True
        )
        indices = np.concatenate([group_indices[group] for group in sampled_groups])
        bootstrap["accuracy"].append(
            accuracy_score(y_array[indices], predictions_array[indices])
        )
        bootstrap["balanced_accuracy"].append(
            recall_score(
                y_array[indices],
                predictions_array[indices],
                labels=metric_labels,
                average="macro",
                zero_division=0,
            )
        )
        bootstrap["macro_f1"].append(
            f1_score(
                y_array[indices],
                predictions_array[indices],
                labels=metric_labels,
                average="macro",
                zero_division=0,
            )
        )
    rows: list[dict[str, object]] = []
    for metric, estimate in metrics.items():
        lower, upper = percentile_interval(bootstrap[metric])
        rows.append(
            {
                "metric": metric,
                "estimate": estimate,
                "ci95_lower": lower,
                "ci95_upper": upper,
                "n": len(y_true),
                "interval_note": "Normalized-text-group bootstrap, 2,000 resamples.",
            }
        )
    result = pd.DataFrame(rows)
    result.to_csv(EXTERNAL_RESULTS_PATH, index=False)
    return result
