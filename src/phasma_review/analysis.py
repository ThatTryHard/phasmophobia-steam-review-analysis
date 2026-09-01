"""Descriptive analysis with explicit estimands and uncertainty.

Methodological design:

* Every observed review is included; no heuristic-selected labeled subset is
  used to estimate prevalence.
* Hard contradictions, mixed opinions, non-evaluative text, and insufficient
  text remain separate outcomes.
* Missing playtime is retained as missing, not converted to zero.
* Confidence intervals and duplicate/confidence sensitivity checks accompany
  point estimates.
* Association results are labelled exploratory and never interpreted as
  causal effects.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from .features import engineer_features
from .paths import (
    ASSOCIATION_RESULTS_PATH,
    BEHAVIOR_RESULTS_PATH,
    FEATURED_REVIEWS_PATH,
    LABELED_REVIEWS_PATH,
    PREVALENCE_RESULTS_PATH,
    REPORTS_DIR,
    SENSITIVITY_RESULTS_PATH,
    ensure_output_directories,
)
from .schema import AnnotationIncompleteError
from .utils import RANDOM_SEED, percentile_interval, wilson_interval

ANALYSIS_REPORT_PATH = REPORTS_DIR / "analysis_report.md"


def load_labeled_reviews() -> pd.DataFrame:
    """Load the adjudicated human label table or fail closed."""

    if not LABELED_REVIEWS_PATH.exists():
        raise AnnotationIncompleteError(
            "Adjudicated labels do not exist. Complete both blinded annotation "
            "files, build/adjudicate the disagreement queue, and finalize labels."
        )
    frame = pd.read_csv(LABELED_REVIEWS_PATH)
    if frame.empty or frame["sentiment_composition"].isna().any():
        raise AnnotationIncompleteError("Final label file is empty or incomplete.")
    return frame


def build_featured_reviews(frame: pd.DataFrame | None = None) -> pd.DataFrame:
    """Apply the one canonical feature implementation to finalized labels."""

    ensure_output_directories()
    labeled = load_labeled_reviews() if frame is None else frame.copy()
    featured = engineer_features(labeled)
    featured.to_csv(FEATURED_REVIEWS_PATH, index=False)
    return featured


def _categorical_summary(
    frame: pd.DataFrame,
    variable: str,
    scope: str,
) -> pd.DataFrame:
    counts = frame[variable].fillna("Missing").value_counts(dropna=False)
    rows: list[dict[str, object]] = []
    denominator = len(frame)
    for category, count in counts.items():
        lower, upper = wilson_interval(int(count), denominator)
        rows.append(
            {
                "scope": scope,
                "variable": variable,
                "category": category,
                "n": int(count),
                "denominator": denominator,
                "proportion": count / denominator if denominator else math.nan,
                "ci95_lower": lower,
                "ci95_upper": upper,
                "interval_note": (
                    "Wilson interval; descriptive corpus is a census of the "
                    "available file, so superpopulation inference is conditional."
                ),
            }
        )
    return pd.DataFrame(rows)


def prevalence_tables(featured: pd.DataFrame) -> pd.DataFrame:
    """Estimate prevalence on the full corpus and prespecified subgroups."""

    parts = [
        _categorical_summary(featured, "recommendation", "all_observed_reviews"),
        _categorical_summary(featured, "language_status", "all_observed_reviews"),
        _categorical_summary(featured, "text_informativeness", "all_observed_reviews"),
        _categorical_summary(featured, "sentiment_composition", "all_observed_reviews"),
        _categorical_summary(featured, "primary_theme", "all_observed_reviews"),
        _categorical_summary(
            featured,
            "recommendation_text_relation",
            "all_observed_reviews",
        ),
    ]
    interpretable_english = featured[
        featured["language_status"].eq("English")
        & featured["text_informativeness"].eq("Sufficient")
    ]
    parts.extend(
        [
            _categorical_summary(
                interpretable_english,
                "sentiment_composition",
                "english_sufficient_text",
            ),
            _categorical_summary(
                interpretable_english,
                "recommendation_text_relation",
                "english_sufficient_text",
            ),
        ]
    )
    result = pd.concat(parts, ignore_index=True)
    result.to_csv(PREVALENCE_RESULTS_PATH, index=False)
    return result


def _bootstrap_median_interval(
    values: pd.Series,
    seed_offset: int,
    draws: int = 2_000,
) -> tuple[float, float]:
    clean = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if clean.size < 2:
        return (math.nan, math.nan)
    rng = np.random.default_rng(RANDOM_SEED + seed_offset)
    medians = np.median(
        rng.choice(clean, size=(draws, clean.size), replace=True),
        axis=1,
    )
    return percentile_interval(medians)


def behavior_tables(featured: pd.DataFrame) -> pd.DataFrame:
    """Summarize playtime and engagement without turning missing into zero."""

    rows: list[dict[str, object]] = []
    grouping_variables = (
        "recommendation",
        "sentiment_composition",
        "recommendation_text_relation",
        "player_group",
    )
    metrics = ("playtime_hours", "helpful_count", "funny_count", "word_count")
    seed_offset = 0
    for grouping in grouping_variables:
        for category, group in featured.groupby(grouping, dropna=False, observed=True):
            for metric in metrics:
                numeric = pd.to_numeric(group[metric], errors="coerce")
                observed = numeric.dropna()
                lower, upper = _bootstrap_median_interval(observed, seed_offset)
                seed_offset += 1
                rows.append(
                    {
                        "grouping_variable": grouping,
                        "group": category,
                        "metric": metric,
                        "n_rows": len(group),
                        "n_observed": len(observed),
                        "n_missing": int(numeric.isna().sum()),
                        "median": observed.median() if len(observed) else math.nan,
                        "q1": observed.quantile(0.25) if len(observed) else math.nan,
                        "q3": observed.quantile(0.75) if len(observed) else math.nan,
                        "median_ci95_lower": lower,
                        "median_ci95_upper": upper,
                        "interval_note": "Nonparametric bootstrap, 2,000 resamples.",
                    }
                )
    result = pd.DataFrame(rows)
    result.to_csv(BEHAVIOR_RESULTS_PATH, index=False)
    return result


def _cramers_v(table: pd.DataFrame, chi2: float) -> float:
    n = table.to_numpy().sum()
    minimum_dimension = min(table.shape[0] - 1, table.shape[1] - 1)
    if n == 0 or minimum_dimension <= 0:
        return math.nan
    return math.sqrt(chi2 / (n * minimum_dimension))


def association_tables(featured: pd.DataFrame) -> pd.DataFrame:
    """Run prespecified exploratory association tests with sparse-cell warnings."""

    analysis = featured[
        featured["language_status"].eq("English")
        & featured["text_informativeness"].eq("Sufficient")
    ]
    rows: list[dict[str, object]] = []
    for outcome in ("sentiment_composition", "primary_theme", "player_group"):
        table = pd.crosstab(analysis["recommendation"], analysis[outcome])
        if table.shape[0] < 2 or table.shape[1] < 2:
            rows.append(
                {
                    "predictor": "recommendation",
                    "outcome": outcome,
                    "n": int(table.to_numpy().sum()),
                    "chi_square": math.nan,
                    "degrees_of_freedom": math.nan,
                    "p_value": math.nan,
                    "cramers_v": math.nan,
                    "minimum_expected_count": math.nan,
                    "sparse_warning": True,
                    "interpretation_limit": "Test undefined: fewer than two levels.",
                }
            )
            continue
        chi2, p_value, dof, expected = chi2_contingency(table)
        minimum_expected = float(expected.min())
        rows.append(
            {
                "predictor": "recommendation",
                "outcome": outcome,
                "n": int(table.to_numpy().sum()),
                "chi_square": chi2,
                "degrees_of_freedom": int(dof),
                "p_value": p_value,
                "cramers_v": _cramers_v(table, chi2),
                "minimum_expected_count": minimum_expected,
                "sparse_warning": bool((expected < 5).any()),
                "interpretation_limit": (
                    "Exploratory association only; no causal interpretation and "
                    "no multiplicity-adjusted confirmatory claim."
                ),
            }
        )
    result = pd.DataFrame(rows)
    result.to_csv(ASSOCIATION_RESULTS_PATH, index=False)
    return result


def _relation_rates(frame: pd.DataFrame, scenario: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relation in (
        "Hard contradiction",
        "Qualified / mixed opinion",
        "Non-evaluative text",
        "Insufficient text",
    ):
        count = int(frame["recommendation_text_relation"].eq(relation).sum())
        lower, upper = wilson_interval(count, len(frame))
        rows.append(
            {
                "analysis": "relation_rate",
                "scenario": scenario,
                "category": relation,
                "n": count,
                "denominator": len(frame),
                "estimate": count / len(frame) if len(frame) else math.nan,
                "ci95_lower": lower,
                "ci95_upper": upper,
            }
        )
    return rows


def _player_scheme(hours: object, breaks: tuple[int, int]) -> str:
    if pd.isna(hours):
        return "Unknown"
    low, high = breaks
    value = float(hours)
    if value <= low:
        return f"≤{low}h"
    if value <= high:
        return f"{low}–{high}h"
    return f">{high}h"


def sensitivity_tables(featured: pd.DataFrame) -> pd.DataFrame:
    """Quantify dependence on duplicates, confidence, and playtime cut points."""

    rows: list[dict[str, object]] = []
    rows.extend(_relation_rates(featured, "all_rows"))
    rows.extend(
        _relation_rates(
            featured.drop_duplicates("text_group_id"),
            "one_row_per_normalized_text",
        )
    )
    rows.extend(
        _relation_rates(
            featured[~featured["annotation_confidence"].eq("Low")],
            "exclude_low_confidence_annotations",
        )
    )

    for breaks in ((10, 100), (50, 200), (100, 300)):
        scheme_name = f"playtime_cutpoints_{breaks[0]}_{breaks[1]}"
        groups = featured["playtime_hours"].map(
            lambda value, cut_points=breaks: _player_scheme(value, cut_points)
        )
        cross = pd.crosstab(groups, featured["recommendation"], dropna=False)
        for group, values in cross.iterrows():
            denominator = int(values.sum())
            recommended = int(values.get("Recommended", 0))
            lower, upper = wilson_interval(recommended, denominator)
            rows.append(
                {
                    "analysis": "player_group_recommendation_rate",
                    "scenario": scheme_name,
                    "category": group,
                    "n": recommended,
                    "denominator": denominator,
                    "estimate": recommended / denominator if denominator else math.nan,
                    "ci95_lower": lower,
                    "ci95_upper": upper,
                }
            )

    result = pd.DataFrame(rows)
    result.to_csv(SENSITIVITY_RESULTS_PATH, index=False)
    return result


def _format_percent(value: float) -> str:
    return "NA" if pd.isna(value) else f"{value:.1%}"


def _find_prevalence(
    prevalence: pd.DataFrame,
    variable: str,
    category: str,
    scope: str = "all_observed_reviews",
) -> pd.Series | None:
    match = prevalence[
        prevalence["variable"].eq(variable)
        & prevalence["category"].eq(category)
        & prevalence["scope"].eq(scope)
    ]
    return None if match.empty else match.iloc[0]


def write_analysis_report(
    featured: pd.DataFrame,
    prevalence: pd.DataFrame,
    associations: pd.DataFrame,
) -> None:
    """Write an honest, stakeholder-readable report without causal claims."""

    relation_lines: list[str] = []
    for category in (
        "Hard contradiction",
        "Qualified / mixed opinion",
        "Non-evaluative text",
        "Insufficient text",
    ):
        row = _find_prevalence(prevalence, "recommendation_text_relation", category)
        if row is not None:
            relation_lines.append(
                f"| {category} | {int(row['n'])}/{int(row['denominator'])} | "
                f"{_format_percent(row['proportion'])} | "
                f"{_format_percent(row['ci95_lower'])}–{_format_percent(row['ci95_upper'])} |"
            )

    sparse_count = int(associations["sparse_warning"].sum()) if len(associations) else 0
    lines = [
        "# Analysis Report",
        "",
        (
            "> Results use all observed reviews and adjudicated human "
            "labels. Mixed, non-evaluative, insufficient, and contradictory text are not "
            "collapsed."
        ),
        "",
        "## Scope and estimand",
        "",
        (
            f"The corpus contains **{len(featured)} review rows** and "
            f"**{featured['text_group_id'].nunique()} unique normalized texts**. Results "
            "describe this available Phasmophobia review file. Collection coverage outside "
            "this file is not documented well enough to claim representativeness of all "
            "players, all Steam reviews, other games, or future updates."
        ),
        "",
        "## Recommendation/text relationship",
        "",
        "| Relationship | Count | Estimate | 95% Wilson interval |",
        "|---|---:|---:|---:|",
        *relation_lines,
        "",
        (
            "Intervals express sampling-style uncertainty conditional on treating this "
            "corpus as a sample from a broader review process. They are not a correction "
            "for unknown selection bias."
        ),
        "",
        "## Behavioral analysis",
        "",
        (
            "Playtime and engagement summaries use medians, interquartile ranges, and "
            "2,000-draw bootstrap intervals. Missing playtime remains missing and is "
            "counted explicitly."
        ),
        "",
        "## Association tests",
        "",
        (
            f"The prespecified chi-square tables are exploratory; **{sparse_count}** "
            "table(s) have expected cell counts below five. P-values are not used as causal "
            "evidence or as a license for post-hoc storytelling."
        ),
        "",
        "## Robustness limits",
        "",
        (
            "Results are recomputed after deduplicating normalized text, excluding "
            "low-confidence annotations, and changing playtime cut points. A future-update "
            "temporal validation set is still required before any claim of stability under "
            "concept drift."
        ),
    ]
    ANALYSIS_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis() -> dict[str, pd.DataFrame]:
    featured = build_featured_reviews()
    prevalence = prevalence_tables(featured)
    behavior = behavior_tables(featured)
    associations = association_tables(featured)
    sensitivity = sensitivity_tables(featured)
    write_analysis_report(featured, prevalence, associations)
    return {
        "featured": featured,
        "prevalence": prevalence,
        "behavior": behavior,
        "associations": associations,
        "sensitivity": sensitivity,
    }
