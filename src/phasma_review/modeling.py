"""Leakage-resistant model comparison and locked-test evaluation.

Evaluation design:

* The locked test split was assigned before labels and is never used for model
  or hyperparameter selection.
* Exact duplicate text groups stay in one fold.
* A most-frequent classifier and the Steam recommendation itself are reported
  before text models.
* Fixed, deliberately small candidate models are compared with repeated
  stratified group cross-validation and a one-standard-error selection rule.
* The selected model and two baselines are evaluated once on the locked test
  set with group-bootstrap uncertainty intervals.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, clone
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_recall_fscore_support,
    recall_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline

from .analysis import build_featured_reviews
from .paths import (
    CV_RESULTS_PATH,
    FEATURED_REVIEWS_PATH,
    LABELED_REVIEWS_PATH,
    MODEL_MANIFEST_PATH,
    MODEL_PATH,
    RAW_REVIEWS_PATH,
    REPORTS_DIR,
    TEST_PREDICTIONS_PATH,
    TEST_RESULTS_PATH,
    ensure_output_directories,
)
from .utils import (
    RANDOM_SEED,
    percentile_interval,
    sha256_file,
    sha256_text_file,
    write_json,
)

MODEL_REPORT_PATH = REPORTS_DIR / "model_validation.md"
MODEL_CLASSES = (
    "Positive_only",
    "Negative_only",
    "Mixed",
    "Neutral_non_evaluative",
)


@dataclass(frozen=True)
class Candidate:
    name: str
    estimator: BaseEstimator
    complexity_rank: int
    kind: str = "text_model"


def _logistic_pipeline(
    analyzer: str,
    ngram_range: tuple[int, int],
    min_df: int = 2,
) -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer=analyzer,
                    ngram_range=ngram_range,
                    min_df=min_df,
                    max_df=0.98,
                    lowercase=True,
                    strip_accents="unicode",
                    sublinear_tf=True,
                    max_features=20_000,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=1.0,
                    class_weight="balanced",
                    max_iter=2_000,
                    random_state=RANDOM_SEED,
                ),
            ),
        ]
    )


def candidate_models() -> list[Candidate]:
    """Return the prespecified, intentionally narrow comparison set."""

    return [
        Candidate(
            "most_frequent",
            DummyClassifier(strategy="most_frequent", random_state=RANDOM_SEED),
            complexity_rank=-2,
            kind="baseline",
        ),
        Candidate(
            "word_unigram_logreg",
            _logistic_pipeline("word", (1, 1)),
            complexity_rank=0,
        ),
        Candidate(
            "word_1_2gram_logreg",
            _logistic_pipeline("word", (1, 2)),
            complexity_rank=1,
        ),
        Candidate(
            "char_3_5gram_logreg",
            _logistic_pipeline("char_wb", (3, 5)),
            complexity_rank=2,
        ),
    ]


def modeling_cohort(featured: pd.DataFrame) -> pd.DataFrame:
    """Use only interpretable English text with a model-supported final label."""

    cohort = featured[
        featured["language_status"].eq("English")
        & featured["text_informativeness"].eq("Sufficient")
        & featured["sentiment_composition"].isin(MODEL_CLASSES)
    ].copy()
    if cohort.empty:
        raise ValueError("No eligible English, sufficient-text modeling rows exist.")
    return cohort


def _steam_predictions(recommendation: pd.Series) -> np.ndarray:
    return np.where(
        recommendation.eq("Recommended"),
        "Positive_only",
        "Negative_only",
    )


def _fold_metrics(
    y_true: pd.Series,
    y_pred: np.ndarray,
    labels: list[str],
) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(
            recall_score(
                y_true,
                y_pred,
                labels=labels,
                average="macro",
                zero_division=0,
            )
        ),
        "macro_f1": float(
            f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
        ),
    }


def _group_counts_by_class(frame: pd.DataFrame) -> pd.Series:
    return (
        frame[["text_group_id", "sentiment_composition"]]
        .drop_duplicates()
        .groupby("sentiment_composition")["text_group_id"]
        .nunique()
    )


def repeated_group_cv(
    development: pd.DataFrame,
    repeats: int = 10,
) -> pd.DataFrame:
    """Compare all candidates without exposing the locked test set."""

    class_group_counts = _group_counts_by_class(development)
    if len(class_group_counts) < 2:
        raise ValueError("Modeling requires at least two development-set classes.")
    n_splits = min(5, int(class_group_counts.min()))
    if n_splits < 2:
        raise ValueError(
            "Every modeled class needs at least two distinct development text groups. "
            f"Observed group counts: {class_group_counts.to_dict()}"
        )

    rows: list[dict[str, object]] = []
    x = development["analysis_review"]
    y = development["sentiment_composition"]
    groups = development["text_group_id"]
    metric_labels = sorted(y.unique().tolist())
    candidates = candidate_models()

    for repeat in range(repeats):
        splitter = StratifiedGroupKFold(
            n_splits=n_splits,
            shuffle=True,
            random_state=RANDOM_SEED + repeat,
        )
        for fold, (train_index, validation_index) in enumerate(
            splitter.split(x, y, groups),
            start=1,
        ):
            train_groups = set(groups.iloc[train_index])
            validation_groups = set(groups.iloc[validation_index])
            if train_groups & validation_groups:
                raise AssertionError("A duplicate text group crossed a CV fold.")

            y_train = y.iloc[train_index]
            y_validation = y.iloc[validation_index]
            for candidate in candidates:
                estimator = clone(candidate.estimator)
                estimator.fit(x.iloc[train_index], y_train)
                predictions = estimator.predict(x.iloc[validation_index])
                rows.append(
                    {
                        "model": candidate.name,
                        "kind": candidate.kind,
                        "repeat": repeat + 1,
                        "fold": fold,
                        "n_train": len(train_index),
                        "n_validation": len(validation_index),
                        **_fold_metrics(y_validation, predictions, metric_labels),
                    }
                )

            # Steam recommendation is an explicit, zero-training reference
            # baseline. It cannot predict Mixed or Neutral classes.
            steam_predictions = _steam_predictions(
                development.iloc[validation_index]["recommendation"]
            )
            rows.append(
                {
                    "model": "steam_recommendation_mapping",
                    "kind": "metadata_baseline",
                    "repeat": repeat + 1,
                    "fold": fold,
                    "n_train": len(train_index),
                    "n_validation": len(validation_index),
                    **_fold_metrics(y_validation, steam_predictions, metric_labels),
                }
            )

    return pd.DataFrame(rows)


def select_text_model(cv_results: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    """Use a one-standard-error rule, preferring the simpler eligible model."""

    text_names = [item.name for item in candidate_models() if item.kind == "text_model"]
    text_results = cv_results[cv_results["model"].isin(text_names)].copy()
    if "repeat" not in text_results:
        # Unit-test/single-run fallback: each supplied observation is treated as
        # a resampling unit. Production CV always supplies explicit repeats.
        text_results["repeat"] = text_results.groupby("model").cumcount() + 1
    repeat_means = text_results.groupby(["model", "repeat"], as_index=False).agg(
        macro_f1=("macro_f1", "mean"),
        balanced_accuracy=("balanced_accuracy", "mean"),
        accuracy=("accuracy", "mean"),
    )
    summary = repeat_means.groupby("model", as_index=False).agg(
        mean_macro_f1=("macro_f1", "mean"),
        sd_macro_f1=("macro_f1", "std"),
        n_repeats=("macro_f1", "size"),
        mean_balanced_accuracy=("balanced_accuracy", "mean"),
        mean_accuracy=("accuracy", "mean"),
    )
    summary["sd_macro_f1"] = summary["sd_macro_f1"].fillna(0.0)
    summary["se_macro_f1"] = summary["sd_macro_f1"] / np.sqrt(summary["n_repeats"])
    best = summary.sort_values("mean_macro_f1", ascending=False).iloc[0]
    eligibility_floor = float(best["mean_macro_f1"] - best["se_macro_f1"])
    complexity = {item.name: item.complexity_rank for item in candidate_models()}
    summary["complexity_rank"] = summary["model"].map(complexity)
    summary["one_se_eligible"] = summary["mean_macro_f1"].ge(eligibility_floor)
    selected = (
        summary[summary["one_se_eligible"]]
        .sort_values(["complexity_rank", "mean_macro_f1"], ascending=[True, False])
        .iloc[0]["model"]
    )
    summary["selected"] = summary["model"].eq(selected)
    return str(selected), summary


def _metric_vector(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: list[str] | None = None,
) -> dict[str, float]:
    labels = labels or sorted(set(y_true) | set(y_pred))
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
    )
    result: dict[str, float] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(
            recall_score(
                y_true,
                y_pred,
                labels=labels,
                average="macro",
                zero_division=0,
            )
        ),
        "macro_f1": float(
            f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
        ),
    }
    for index, label in enumerate(labels):
        result[f"precision::{label}"] = float(precision[index])
        result[f"recall::{label}"] = float(recall[index])
        result[f"f1::{label}"] = float(f1[index])
    return result


def _group_bootstrap_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    groups: np.ndarray,
    seed_offset: int,
    labels: list[str],
    draws: int = 2_000,
) -> dict[str, tuple[float, float]]:
    unique_groups = np.unique(groups)
    group_indices = {group: np.flatnonzero(groups == group) for group in unique_groups}
    rng = np.random.default_rng(RANDOM_SEED + seed_offset)
    bootstrap: dict[str, list[float]] = {}
    for _ in range(draws):
        sampled_groups = rng.choice(
            unique_groups, size=len(unique_groups), replace=True
        )
        sampled_indices = np.concatenate(
            [group_indices[group] for group in sampled_groups]
        )
        values = _metric_vector(
            y_true[sampled_indices],
            y_pred[sampled_indices],
            labels=labels,
        )
        for metric, value in values.items():
            bootstrap.setdefault(metric, []).append(value)
    return {metric: percentile_interval(values) for metric, values in bootstrap.items()}


def _long_test_metrics(
    model_name: str,
    y_true: pd.Series,
    y_pred: np.ndarray,
    groups: pd.Series,
    seed_offset: int,
    labels: list[str],
) -> pd.DataFrame:
    point = _metric_vector(y_true.to_numpy(), np.asarray(y_pred), labels=labels)
    intervals = _group_bootstrap_metrics(
        y_true.to_numpy(),
        np.asarray(y_pred),
        groups.to_numpy(),
        seed_offset,
        labels,
    )
    rows: list[dict[str, object]] = []
    for metric, estimate in point.items():
        lower, upper = intervals.get(metric, (math.nan, math.nan))
        metric_name, _, class_name = metric.partition("::")
        rows.append(
            {
                "model": model_name,
                "metric": metric_name,
                "class": class_name or "overall",
                "estimate": estimate,
                "ci95_lower": lower,
                "ci95_upper": upper,
                "n_test": len(y_true),
                "interval_note": "Group bootstrap, 2,000 resamples.",
            }
        )
    return pd.DataFrame(rows)


def _candidate_by_name(name: str) -> Candidate:
    matches = [candidate for candidate in candidate_models() if candidate.name == name]
    if not matches:
        raise KeyError(f"Unknown candidate: {name}")
    return matches[0]


def _write_model_report(
    cohort: pd.DataFrame,
    selected_name: str,
    cv_results: pd.DataFrame,
    test_results: pd.DataFrame,
) -> None:
    # Reporting fix: the uncertainty unit is one complete repeated-CV run, not
    # an individual fold. This matches the one-standard-error selector.
    repeat_summary = cv_results.groupby(
        ["model", "kind", "repeat"], as_index=False
    ).agg(
        macro_f1=("macro_f1", "mean"),
        balanced_accuracy=("balanced_accuracy", "mean"),
    )
    all_summary = (
        repeat_summary.groupby(["model", "kind"], as_index=False)
        .agg(
            mean_macro_f1=("macro_f1", "mean"),
            sd_macro_f1=("macro_f1", "std"),
            mean_balanced_accuracy=("balanced_accuracy", "mean"),
        )
        .sort_values("mean_macro_f1", ascending=False)
    )
    cv_lines = [
        f"| {row.model} | {row.kind} | {row.mean_macro_f1:.3f} | "
        f"{row.sd_macro_f1:.3f} | {row.mean_balanced_accuracy:.3f} |"
        for row in all_summary.itertuples()
    ]
    overall_test = test_results[test_results["class"].eq("overall")]
    test_lines = [
        f"| {row.model} | {row.metric} | {row.estimate:.3f} | "
        f"{row.ci95_lower:.3f}–{row.ci95_upper:.3f} |"
        for row in overall_test.itertuples()
    ]
    lines = [
        "# Model Validation Report",
        "",
        (
            "> Model selection uses repeated stratified group CV on development "
            "data only. Exact duplicate texts cannot cross folds. The test set is opened "
            "once, after selection."
        ),
        "",
        "## Cohort",
        "",
        (
            f"Eligible adjudicated English/sufficient-text rows: **{len(cohort)}**. "
            f"Development: **{int(cohort['evaluation_partition'].eq('development').sum())}**; "
            f"locked test: **{int(cohort['evaluation_partition'].eq('locked_test').sum())}**."
        ),
        "",
        "## Development cross-validation",
        "",
        "| Model | Role | Mean macro F1 | SD | Mean balanced accuracy |",
        "|---|---|---:|---:|---:|",
        *cv_lines,
        "",
        (
            f"Selected text model: **{selected_name}**. The one-standard-error rule chose "
            "the least complex text model within the prespecified repeat-level CV "
            "uncertainty band of the highest mean macro F1. This is a complexity-control "
            "heuristic, not a test of statistical equivalence."
        ),
        "",
        "## Locked-test results",
        "",
        "| Model | Metric | Estimate | 95% group-bootstrap interval |",
        "|---|---|---:|---:|",
        *test_lines,
        "",
        "## Production limit",
        "",
        (
            "This artifact is **not approved for production inference**. No operational "
            "confidence/abstention threshold is set because false-positive and "
            "false-negative costs were not supplied, and the corpus is one game from one "
            "five-day window. A separately collected, blindly annotated future-update set "
            "of at least 100 reviews must pass the external validation gate first."
        ),
    ]
    MODEL_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_modeling(repeats: int = 10) -> dict[str, object]:
    """Run selection and the single planned locked-test evaluation."""

    ensure_output_directories()
    featured = (
        pd.read_csv(FEATURED_REVIEWS_PATH)
        if FEATURED_REVIEWS_PATH.exists()
        else build_featured_reviews()
    )
    cohort = modeling_cohort(featured)
    development = cohort[cohort["evaluation_partition"].eq("development")].copy()
    locked_test = cohort[cohort["evaluation_partition"].eq("locked_test")].copy()
    if development.empty or locked_test.empty:
        raise ValueError("Both development and locked-test cohorts must be non-empty.")
    if set(development["text_group_id"]) & set(locked_test["text_group_id"]):
        raise AssertionError(
            "A duplicate text group crossed development/test partitions."
        )
    unseen_test_classes = set(locked_test["sentiment_composition"]) - set(
        development["sentiment_composition"]
    )
    if unseen_test_classes:
        raise ValueError(
            "Locked test contains target classes absent from development; a classifier "
            f"cannot learn them: {sorted(unseen_test_classes)}"
        )

    cv_results = repeated_group_cv(development, repeats=repeats)
    selected_name, selection_summary = select_text_model(cv_results)
    cv_results.to_csv(CV_RESULTS_PATH, index=False)
    selection_summary.to_csv(
        CV_RESULTS_PATH.with_name("model_selection_summary.csv"),
        index=False,
    )

    selected_model = clone(_candidate_by_name(selected_name).estimator)
    selected_model.fit(
        development["analysis_review"],
        development["sentiment_composition"],
    )
    selected_predictions = selected_model.predict(locked_test["analysis_review"])
    selected_probabilities = selected_model.predict_proba(
        locked_test["analysis_review"]
    )

    dummy = DummyClassifier(strategy="most_frequent", random_state=RANDOM_SEED)
    dummy.fit(development["analysis_review"], development["sentiment_composition"])
    dummy_predictions = dummy.predict(locked_test["analysis_review"])
    steam_predictions = _steam_predictions(locked_test["recommendation"])
    metric_labels = sorted(development["sentiment_composition"].unique().tolist())

    test_results = pd.concat(
        [
            _long_test_metrics(
                selected_name,
                locked_test["sentiment_composition"],
                selected_predictions,
                locked_test["text_group_id"],
                1_000,
                metric_labels,
            ),
            _long_test_metrics(
                "most_frequent",
                locked_test["sentiment_composition"],
                dummy_predictions,
                locked_test["text_group_id"],
                2_000,
                metric_labels,
            ),
            _long_test_metrics(
                "steam_recommendation_mapping",
                locked_test["sentiment_composition"],
                steam_predictions,
                locked_test["text_group_id"],
                3_000,
                metric_labels,
            ),
        ],
        ignore_index=True,
    )
    test_results.to_csv(TEST_RESULTS_PATH, index=False)

    predictions = locked_test[
        [
            "review_id",
            "text_group_id",
            "evaluation_partition",
            "recommendation",
            "sentiment_composition",
            "primary_theme",
            "annotation_confidence",
        ]
    ].copy()
    predictions["predicted_sentiment"] = selected_predictions
    predictions["prediction_confidence"] = selected_probabilities.max(axis=1)
    predictions["correct"] = predictions["sentiment_composition"].eq(
        predictions["predicted_sentiment"]
    )
    for index, class_name in enumerate(selected_model.classes_):
        predictions[f"probability_{class_name}"] = selected_probabilities[:, index]
    predictions.to_csv(TEST_PREDICTIONS_PATH, index=False)

    joblib.dump(selected_model, MODEL_PATH)
    manifest = {
        "artifact_role": "research_only",
        "production_approved": False,
        "operational_abstention_threshold": None,
        "threshold_reason": (
            "Business error costs were not supplied; predictions require human review."
        ),
        "random_seed": RANDOM_SEED,
        "selected_model": selected_name,
        "selection_rule": "one_standard_error_then_lowest_complexity",
        "cv_repeats": repeats,
        "development_rows": len(development),
        "locked_test_rows": len(locked_test),
        "development_class_counts": development["sentiment_composition"]
        .value_counts()
        .to_dict(),
        "test_class_counts": locked_test["sentiment_composition"]
        .value_counts()
        .to_dict(),
        # Generated CSVs are text-normalized before hashing so a Windows
        # training run verifies after Git checks the repository out on Linux.
        "label_file_sha256": sha256_text_file(LABELED_REVIEWS_PATH),
        "featured_file_sha256": sha256_text_file(FEATURED_REVIEWS_PATH),
        "split_manifest_sha256": sha256_file(
            RAW_REVIEWS_PATH.with_name("split_manifest.csv")
        ),
    }
    write_json(manifest, MODEL_MANIFEST_PATH)
    _write_model_report(
        cohort,
        selected_name,
        cv_results,
        test_results,
    )
    return {
        "selected_model": selected_name,
        "cv_results": cv_results,
        "selection_summary": selection_summary,
        "test_results": test_results,
        "test_predictions": predictions,
        "manifest": manifest,
    }
