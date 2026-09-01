"""Generate results tables and a self-contained HTML dashboard.

Reporting design:

* Missing pilot metadata remains ``Unknown`` instead of silently becoming
  ``False``.
* Mixed, non-evaluative, insufficient, and hard-contradiction rows are shown
  separately.
* Every proportion carries its denominator and interval.
* Qualitative examples use a reproducible diagnostic rule and are never
  described as representative.
"""

from __future__ import annotations

import html
from pathlib import Path

import pandas as pd

from .analysis import run_analysis
from .paths import (
    DASHBOARD_DATA_DIR,
    FEATURED_REVIEWS_PATH,
    PREVALENCE_RESULTS_PATH,
    REPORTS_DIR,
    TEST_PREDICTIONS_PATH,
    TEST_RESULTS_PATH,
    ensure_output_directories,
)

DASHBOARD_HTML_PATH = REPORTS_DIR / "dashboard.html"


def _tri_state(value: object) -> str:
    if pd.isna(value) or str(value).strip() == "":
        return "Unknown"
    if value is True or str(value).strip().lower() in {"true", "1", "yes"}:
        return "True"
    if value is False or str(value).strip().lower() in {"false", "0", "no"}:
        return "False"
    return "Unknown"


def _save(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    frame.to_csv(DASHBOARD_DATA_DIR / name, index=False)
    return frame


def _matrix(featured: pd.DataFrame) -> pd.DataFrame:
    counts = (
        featured.groupby(
            ["recommendation", "sentiment_composition"],
            observed=True,
        )
        .size()
        .rename("n")
        .reset_index()
    )
    counts["recommendation_denominator"] = counts.groupby("recommendation")[
        "n"
    ].transform("sum")
    counts["within_recommendation_proportion"] = (
        counts["n"] / counts["recommendation_denominator"]
    )
    counts["corpus_denominator"] = len(featured)
    counts["corpus_proportion"] = counts["n"] / len(featured)
    return counts


def _theme_summary(featured: pd.DataFrame) -> pd.DataFrame:
    result = (
        featured.groupby(["primary_theme", "recommendation"], observed=True)
        .size()
        .rename("n")
        .reset_index()
    )
    result["theme_denominator"] = result.groupby("primary_theme")["n"].transform("sum")
    result["within_theme_proportion"] = result["n"] / result["theme_denominator"]
    return result


def _player_summary(featured: pd.DataFrame) -> pd.DataFrame:
    result = (
        featured.groupby(
            ["player_group", "recommendation_text_relation"],
            observed=True,
            dropna=False,
        )
        .size()
        .rename("n")
        .reset_index()
    )
    result["player_group_denominator"] = result.groupby("player_group")["n"].transform(
        "sum"
    )
    result["within_player_group_proportion"] = (
        result["n"] / result["player_group_denominator"]
    )
    return result


def _review_level(featured: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "review_id",
        "review_date",
        "evaluation_partition",
        "recommendation",
        "review_text",
        "language_status",
        "text_informativeness",
        "sentiment_composition",
        "primary_theme",
        "annotation_confidence",
        "annotation_source",
        "recommendation_text_relation",
        "playtime_hours",
        "playtime_missing",
        "player_group",
        "helpful_count",
        "funny_count",
        "steam_purchase",
        "received_for_free",
        "written_during_early_access",
        "word_count",
    ]
    result = featured[columns].copy()
    for column in (
        "steam_purchase",
        "received_for_free",
        "written_during_early_access",
    ):
        result[column] = result[column].map(_tri_state)
    return result


def _audit_error_examples(featured: pd.DataFrame) -> pd.DataFrame:
    if not TEST_PREDICTIONS_PATH.exists():
        return pd.DataFrame(
            columns=[
                "review_id",
                "actual",
                "predicted",
                "prediction_confidence",
                "review_text",
                "selection_rule",
            ]
        )
    predictions = pd.read_csv(TEST_PREDICTIONS_PATH)
    correct = predictions["correct"].map(
        lambda value: value is True or str(value).strip().lower() == "true"
    )
    errors = predictions[~correct].copy()
    errors = errors.merge(
        featured[["review_id", "review_text"]],
        on="review_id",
        how="left",
        validate="one_to_one",
    )
    errors = errors.rename(
        columns={
            "sentiment_composition": "actual",
            "predicted_sentiment": "predicted",
        }
    )
    errors = (
        errors.sort_values(
            ["actual", "predicted", "prediction_confidence", "review_id"],
            ascending=[True, True, True, True],
        )
        .groupby(["actual", "predicted"], as_index=False, group_keys=False)
        .head(2)
    )
    errors["selection_rule"] = (
        "Up to two lowest-confidence locked-test errors per actual/predicted pair; "
        "ties broken by review_id. Diagnostic sample, not representative."
    )
    return errors[
        [
            "review_id",
            "actual",
            "predicted",
            "prediction_confidence",
            "review_text",
            "selection_rule",
        ]
    ]


def build_dashboard_tables() -> dict[str, pd.DataFrame]:
    ensure_output_directories()
    if not FEATURED_REVIEWS_PATH.exists() or not PREVALENCE_RESULTS_PATH.exists():
        run_analysis()
    featured = pd.read_csv(FEATURED_REVIEWS_PATH)
    prevalence = pd.read_csv(PREVALENCE_RESULTS_PATH)

    kpis = prevalence[
        prevalence["variable"].eq("recommendation_text_relation")
        & prevalence["scope"].eq("all_observed_reviews")
    ].copy()
    kpis = kpis.rename(columns={"category": "kpi"})
    kpis.insert(0, "scope_limit", "Observed corpus only; not all Steam players/reviews")

    model_summary = (
        pd.read_csv(TEST_RESULTS_PATH)
        if TEST_RESULTS_PATH.exists()
        else pd.DataFrame(
            columns=[
                "model",
                "metric",
                "class",
                "estimate",
                "ci95_lower",
                "ci95_upper",
                "n_test",
                "interval_note",
            ]
        )
    )
    tables = {
        "kpi_summary.csv": kpis,
        "recommendation_sentiment_matrix.csv": _matrix(featured),
        "theme_summary.csv": _theme_summary(featured),
        "player_relation_summary.csv": _player_summary(featured),
        "review_level.csv": _review_level(featured),
        "model_summary.csv": model_summary,
        "audit_error_examples.csv": _audit_error_examples(featured),
    }
    return {name: _save(frame, name) for name, frame in tables.items()}


def _table_html(frame: pd.DataFrame, maximum_rows: int = 40) -> str:
    if frame.empty:
        return '<p class="blocked">Not available until its upstream gate passes.</p>'
    display = frame.head(maximum_rows).copy()
    for column in display.select_dtypes(include=["float"]).columns:
        display[column] = display[column].map(
            lambda value: "" if pd.isna(value) else f"{value:.3f}"
        )
    suffix = (
        f'<p class="note">Showing {maximum_rows} of {len(frame)} rows.</p>'
        if len(frame) > maximum_rows
        else ""
    )
    return display.to_html(index=False, escape=True, border=0) + suffix


def write_dashboard_html(tables: dict[str, pd.DataFrame]) -> Path:
    model_gate = (
        "The predeclared locked-test evaluation is complete; model results remain "
        "research-only and require future temporal validation."
        if not tables["model_summary.csv"].empty
        else "Model results remain blank until the locked-test evaluation is run."
    )
    sections = [
        (
            "Recommendation/text relationship",
            (
                "Counts use the entire observed corpus. Categories are mutually distinct; "
                "a mixed opinion is not a hard contradiction."
            ),
            tables["kpi_summary.csv"],
        ),
        (
            "Recommendation × human sentiment",
            "Every percentage includes its displayed denominator.",
            tables["recommendation_sentiment_matrix.csv"],
        ),
        (
            "Themes",
            "Themes were assigned blind to Steam recommendation.",
            tables["theme_summary.csv"],
        ),
        (
            "Player groups",
            "Cut points are descriptive; alternate definitions are in sensitivity_results.csv.",
            tables["player_relation_summary.csv"],
        ),
        (
            "Locked-test model metrics",
            (
                "The selected model and prespecified baselines are shown with uncertainty. "
                "This model is research-only."
            ),
            tables["model_summary.csv"],
        ),
        (
            "Selected model error examples",
            "These are not representative examples. The selection rule is included in each row.",
            tables["audit_error_examples.csv"],
        ),
    ]
    section_html = "\n".join(
        f"<section><h2>{html.escape(title)}</h2><p>{html.escape(note)}</p>"
        f"{_table_html(table)}</section>"
        for title, note, table in sections
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Phasmophobia Review Analysis | Results Dashboard</title>
  <style>
    :root {{ color-scheme: light; --ink:#15202b; --muted:#53606c; --line:#d9e0e6; --accent:#0b6e75; }}
    body {{ font-family: Inter, ui-sans-serif, system-ui, sans-serif; color:var(--ink); margin:0; background:#f6f8fa; }}
    main {{ max-width:1180px; margin:auto; padding:32px 20px 64px; }}
    header, section {{ background:white; border:1px solid var(--line); border-radius:10px; padding:22px; margin-bottom:18px; }}
    h1, h2 {{ margin-top:0; }} h2 {{ color:var(--accent); }}
    .scope {{ border-left:5px solid #b25d00; }} .blocked {{ color:#8a3b12; font-weight:600; }}
    .note, p {{ color:var(--muted); line-height:1.5; }}
    table {{ width:100%; border-collapse:collapse; font-size:0.88rem; overflow-wrap:anywhere; }}
    th, td {{ padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
    th {{ background:#eef5f5; position:sticky; top:0; }}
    section {{ overflow-x:auto; }}
  </style>
</head>
<body><main>
  <header class="scope">
    <h1>Phasmophobia Steam Review Analysis</h1>
    <p><strong>Scope:</strong> the available 262-row review corpus only. This page does not claim population representativeness, causality, cross-game validity, or stability after a future update.</p>
    <p><strong>Evidence gate:</strong> all displayed human-label results come from completed blinded annotation and adjudication. {html.escape(model_gate)}</p>
  </header>
  {section_html}
</main></body></html>"""
    DASHBOARD_HTML_PATH.write_text(document, encoding="utf-8")
    return DASHBOARD_HTML_PATH


def run_dashboard() -> dict[str, pd.DataFrame]:
    tables = build_dashboard_tables()
    write_dashboard_html(tables)
    return tables
