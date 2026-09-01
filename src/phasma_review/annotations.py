"""Blinded annotation validation, agreement, and adjudication."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from .paths import (
    ADJUDICATION_PATH,
    ANNOTATION_DIR,
    ANNOTATOR_A_PATH,
    ANNOTATOR_B_PATH,
    LABELED_REVIEWS_PATH,
    RAW_REVIEWS_PATH,
    REPORTS_DIR,
    ensure_output_directories,
)
from .schema import (
    ANNOTATION_COLUMNS,
    CORE_LABEL_COLUMNS,
    AnnotationIncompleteError,
    derive_relation,
    validate_annotations,
)

AGREEMENT_CSV_PATH = ANNOTATION_DIR / "annotation_agreement.csv"
AGREEMENT_REPORT_PATH = REPORTS_DIR / "annotation_quality.md"
ANNOTATOR_B_EXPECTED_ROWS = 80

ADJUDICATION_EDITABLE_COLUMNS = [
    *(f"final_{column}" for column in CORE_LABEL_COLUMNS),
    "final_secondary_themes",
    "final_annotation_confidence",
    "adjudication_notes",
]


def _load_annotation(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Annotation file not found: {path}")
    frame = pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)
    missing = [column for column in ANNOTATION_COLUMNS if column not in frame]
    if missing:
        raise ValueError(f"{path.name} is missing columns: {missing}")
    return frame[ANNOTATION_COLUMNS].copy()


def annotation_status() -> dict[str, object]:
    status: dict[str, object] = {}
    for label, path in (
        ("annotator_a", ANNOTATOR_A_PATH),
        ("annotator_b", ANNOTATOR_B_PATH),
    ):
        if not path.exists():
            status[label] = {"exists": False, "completed": 0, "total": 0, "errors": []}
            continue
        frame = _load_annotation(path)
        validation = validate_annotations(frame)
        status[label] = {
            "exists": True,
            "completed": validation.completed_rows,
            "total": validation.total_rows,
            "valid_and_complete": validation.valid,
            "errors": list(validation.errors),
        }
    status["adjudication_exists"] = ADJUDICATION_PATH.exists()
    status["final_labels_exist"] = LABELED_REVIEWS_PATH.exists()
    return status


def import_annotation_workbook(
    workbook_path: Path,
    annotator: str,
    allow_less_complete: bool = False,
) -> pd.DataFrame:
    """Safely copy the human-facing Excel form back to the canonical CSV.

    Minor implementation fix: long-text annotation is more usable in a
    validated workbook, but downstream code retains a plain CSV contract.
    Locked IDs/text must match, invalid categories are rejected, and a stale
    workbook cannot replace more-complete CSV work without an explicit override.
    """

    targets = {"a": ANNOTATOR_A_PATH, "b": ANNOTATOR_B_PATH}
    if annotator not in targets:
        raise ValueError("annotator must be 'a' or 'b'.")
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")
    imported = pd.read_excel(
        workbook_path,
        sheet_name="Annotations",
        dtype=str,
        keep_default_na=False,
        engine="openpyxl",
    )
    if list(imported.columns) != ANNOTATION_COLUMNS:
        raise ValueError(
            "Workbook Annotations sheet columns changed; expected exactly: "
            f"{ANNOTATION_COLUMNS}"
        )
    target = targets[annotator]
    current = _load_annotation(target)
    if set(imported["review_id"]) != set(current["review_id"]):
        raise ValueError("Workbook review IDs differ from the locked template.")
    locked_text = current.set_index("review_id")["review_text"]
    imported_text = imported["review_id"].map(locked_text)
    if (
        imported_text.isna().any()
        or not imported["review_text"].eq(imported_text).all()
    ):
        raise ValueError("Workbook review text differs from the locked template.")

    imported_validation = validate_annotations(imported)
    if imported_validation.errors:
        raise ValueError(
            "Workbook contains invalid annotation values: "
            + "; ".join(imported_validation.errors)
        )
    current_validation = validate_annotations(current)
    if (
        imported_validation.completed_rows < current_validation.completed_rows
        and not allow_less_complete
    ):
        raise ValueError(
            "Workbook is less complete than the current CSV. Refusing to overwrite; "
            "use --allow-less-complete only if this rollback is intentional."
        )
    imported.to_csv(target, index=False, encoding="utf-8-sig")

    # Reproducibility fix: keep the canonical human-facing form synchronized
    # with the canonical CSV after a guarded import. Otherwise the project's
    # workbook/CSV equality invariant fails after a legitimate annotation run.
    canonical_workbook = target.with_suffix(".xlsx")
    if workbook_path.resolve() != canonical_workbook.resolve():
        shutil.copyfile(workbook_path, canonical_workbook)
    return imported


def _require_complete(frame: pd.DataFrame, label: str) -> None:
    validation = validate_annotations(frame)
    if not validation.valid:
        details = "; ".join(validation.errors) or "blank core labels remain"
        raise AnnotationIncompleteError(
            f"{label} is incomplete: {validation.completed_rows}/{validation.total_rows} "
            f"rows complete. {details}"
        )


def _safe_kappa(left: pd.Series, right: pd.Series) -> float:
    if len(set(left) | set(right)) < 2:
        return np.nan
    value = cohen_kappa_score(left, right)
    return float(value) if np.isfinite(value) else np.nan


def build_adjudication_queue() -> pd.DataFrame:
    """Measure agreement and create a human-only disagreement queue.

    Critical fix: all locked-test rows are double annotated. No AI-generated
    draft can enter the final labels or test metrics.
    """

    ensure_output_directories()
    annotator_a = _load_annotation(ANNOTATOR_A_PATH)
    annotator_b = _load_annotation(ANNOTATOR_B_PATH)
    _require_complete(annotator_a, "Annotator A")
    _require_complete(annotator_b, "Annotator B")
    source = pd.read_csv(RAW_REVIEWS_PATH)

    source_ids = set(source["review_id"])
    if set(annotator_a["review_id"]) != source_ids:
        raise ValueError("Annotator A must contain every source review exactly once.")
    if len(annotator_b) != ANNOTATOR_B_EXPECTED_ROWS:
        raise ValueError(
            f"Annotator B must contain exactly {ANNOTATOR_B_EXPECTED_ROWS} rows; "
            f"found {len(annotator_b)}."
        )
    locked_ids = set(
        source.loc[source["evaluation_partition"].eq("locked_test"), "review_id"]
    )
    if not locked_ids.issubset(set(annotator_b["review_id"])):
        missing = sorted(locked_ids - set(annotator_b["review_id"]))
        raise ValueError(f"Annotator B is missing locked-test rows: {missing[:5]}")
    source_text = source.set_index("review_id")["review_text"]
    for label, annotation_frame in (
        ("Annotator A", annotator_a),
        ("Annotator B", annotator_b),
    ):
        expected_text = annotation_frame["review_id"].map(source_text)
        if (
            expected_text.isna().any()
            or not annotation_frame["review_text"].eq(expected_text).all()
        ):
            raise ValueError(f"{label} review_text differs from the locked source.")

    paired = annotator_b.merge(
        annotator_a,
        on="review_id",
        how="left",
        suffixes=("_b", "_a"),
        validate="one_to_one",
    )
    if paired["review_text_a"].isna().any():
        raise ValueError("Annotator B contains review IDs absent from Annotator A.")
    if not paired["review_text_a"].eq(paired["review_text_b"]).all():
        raise ValueError("Review text changed between blinded annotation files.")

    agreement_rows: list[dict[str, object]] = []
    disagreement_mask = pd.Series(False, index=paired.index)
    for column in CORE_LABEL_COLUMNS:
        left = paired[f"{column}_a"]
        right = paired[f"{column}_b"]
        equal = left.eq(right)
        disagreement_mask |= ~equal
        agreement_rows.append(
            {
                "field": column,
                "n_double_annotated": len(paired),
                "percent_agreement": round(float(equal.mean() * 100), 2),
                "cohen_kappa": round(_safe_kappa(left, right), 4),
            }
        )

    agreement = pd.DataFrame(agreement_rows)
    agreement.to_csv(AGREEMENT_CSV_PATH, index=False)

    double_disagreement_ids = set(paired.loc[disagreement_mask, "review_id"])

    # Critical fix: identical normalized text must not receive inconsistent
    # labels merely because duplicate scraper rows were seen at different times.
    a_with_groups = annotator_a.merge(
        source[["review_id", "text_group_id"]],
        on="review_id",
        validate="one_to_one",
    )
    inconsistent_groups: set[str] = set()
    for text_group_id, group in a_with_groups.groupby("text_group_id"):
        if any(
            group[column].nunique(dropna=False) > 1 for column in CORE_LABEL_COLUMNS
        ):
            inconsistent_groups.add(text_group_id)
    duplicate_inconsistency_ids = set(
        a_with_groups.loc[
            a_with_groups["text_group_id"].isin(inconsistent_groups), "review_id"
        ]
    )
    queue_ids = double_disagreement_ids | duplicate_inconsistency_ids

    a_index = annotator_a.set_index("review_id")
    b_index = annotator_b.set_index("review_id")
    queue = annotator_a[annotator_a["review_id"].isin(queue_ids)][
        ["review_id", "review_text"]
    ].copy()
    queue["adjudication_reason"] = queue["review_id"].map(
        lambda review_id: "; ".join(
            reason
            for condition, reason in (
                (
                    review_id in double_disagreement_ids,
                    "independent_annotator_disagreement",
                ),
                (
                    review_id in duplicate_inconsistency_ids,
                    "duplicate_text_inconsistency",
                ),
            )
            if condition
        )
    )
    for column in CORE_LABEL_COLUMNS:
        queue[f"{column}_a"] = queue["review_id"].map(a_index[column])
        queue[f"{column}_b"] = queue["review_id"].map(b_index[column]).fillna("")
        queue[f"final_{column}"] = ""
    queue["final_secondary_themes"] = ""
    queue["final_annotation_confidence"] = ""
    queue["adjudication_notes"] = ""
    queue.to_csv(ADJUDICATION_PATH, index=False, encoding="utf-8-sig")

    report_lines = [
        "# Annotation Quality Report",
        "",
        "> Critical fix: agreement is measured only between two independent human annotators. Recommendation labels and heuristic flags were hidden.",
        "",
        f"- Double-annotated rows: **{len(paired)}**",
        f"- Rows with independent-annotator disagreement: **{len(double_disagreement_ids)}**",
        f"- Rows in inconsistently labeled duplicate-text groups: **{len(duplicate_inconsistency_ids)}**",
        f"- Unique rows requiring adjudication: **{len(queue_ids)}**",
        "- The locked test set is fully included in the double-annotated subset.",
        "",
        "| Field | N | Agreement | Cohen's κ |",
        "|---|---:|---:|---:|",
    ]
    for row in agreement_rows:
        report_lines.append(
            f"| {row['field']} | {row['n_double_annotated']} | "
            f"{row['percent_agreement']:.2f}% | {row['cohen_kappa']:.4f} |"
        )
    report_lines.extend(
        [
            "",
            (
                "Adjudication status: **Pending** — no model or dashboard should be "
                "produced until every queued row has a final human decision."
            ),
        ]
    )
    AGREEMENT_REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return queue


def _read_adjudication() -> pd.DataFrame:
    if not ADJUDICATION_PATH.exists():
        raise FileNotFoundError(
            f"Adjudication queue not found: {ADJUDICATION_PATH}. Build it first."
        )
    return pd.read_csv(ADJUDICATION_PATH, encoding="utf-8-sig", keep_default_na=False)


def _set_adjudication_report_status(status_line: str) -> None:
    """Keep the human-readable agreement report aligned with the evidence gate."""

    if not AGREEMENT_REPORT_PATH.exists():
        return
    lines = AGREEMENT_REPORT_PATH.read_text(encoding="utf-8").splitlines()
    lines = [
        line
        for line in lines
        if not line.startswith("Adjudication status:")
        and not line.startswith("No model or dashboard should be produced")
    ]
    while lines and lines[-1] == "":
        lines.pop()
    lines.extend(["", status_line])
    AGREEMENT_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_adjudication_decisions(adjudication: pd.DataFrame) -> None:
    """Apply the annotation codebook to adjudicated final decisions.

    Critical fix: adjudication is not allowed to bypass the same categorical,
    semantic, confidence, and note requirements imposed on independent labels.
    """

    required = [
        "review_id",
        "review_text",
        *ADJUDICATION_EDITABLE_COLUMNS,
    ]
    missing = [column for column in required if column not in adjudication]
    if missing:
        raise ValueError(f"Adjudication file is missing columns: {missing}")

    final_annotations = pd.DataFrame(
        {
            "review_id": adjudication["review_id"],
            "review_text": adjudication["review_text"],
            "language_status": adjudication["final_language_status"],
            "text_informativeness": adjudication[
                "final_text_informativeness"
            ],
            "sentiment_composition": adjudication[
                "final_sentiment_composition"
            ],
            "primary_theme": adjudication["final_primary_theme"],
            "secondary_themes": adjudication["final_secondary_themes"],
            "annotation_confidence": adjudication[
                "final_annotation_confidence"
            ],
            "annotation_notes": adjudication["adjudication_notes"],
        },
        columns=ANNOTATION_COLUMNS,
    )
    validation = validate_annotations(final_annotations)
    if not validation.valid:
        details = "; ".join(validation.errors) or "blank final labels remain"
        raise AnnotationIncompleteError(
            "Adjudication is incomplete or invalid: "
            f"{validation.completed_rows}/{validation.total_rows} rows complete. "
            f"{details}"
        )


def import_adjudication_workbook(workbook_path: Path) -> pd.DataFrame:
    """Guardedly import final human decisions from the Excel coding form.

    Critical fix: only final decision fields may change. Review IDs/text,
    disagreement reasons, and both independent annotators' labels are compared
    byte-for-byte with the canonical queue before any project data is updated.
    """

    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")
    current = _read_adjudication()
    imported = pd.read_excel(
        workbook_path,
        sheet_name="Adjudication",
        dtype=str,
        keep_default_na=False,
        engine="openpyxl",
    )
    if list(imported.columns) != list(current.columns):
        raise ValueError(
            "Workbook Adjudication sheet columns changed; expected exactly: "
            f"{list(current.columns)}"
        )
    if imported["review_id"].duplicated().any():
        raise ValueError("Workbook contains duplicate adjudication review IDs.")
    if set(imported["review_id"]) != set(current["review_id"]):
        raise ValueError("Workbook review IDs differ from the canonical queue.")

    imported = imported.set_index("review_id").loc[current["review_id"]].reset_index()
    protected_columns = [
        column
        for column in current.columns
        if column not in ADJUDICATION_EDITABLE_COLUMNS
    ]
    for column in protected_columns:
        if not imported[column].eq(current[column]).all():
            raise ValueError(
                f"Workbook protected column {column!r} differs from the canonical queue."
            )

    _validate_adjudication_decisions(imported)
    imported.to_csv(ADJUDICATION_PATH, index=False, encoding="utf-8-sig")
    canonical_workbook = ADJUDICATION_PATH.with_suffix(".xlsx")
    if workbook_path.resolve() != canonical_workbook.resolve():
        shutil.copyfile(workbook_path, canonical_workbook)
    _set_adjudication_report_status(
        f"Adjudication status: **Complete** — all {len(imported)} queued rows "
        "have validated final human decisions."
    )
    return imported


def finalize_labels() -> pd.DataFrame:
    """Create the only label file allowed downstream."""

    source = pd.read_csv(RAW_REVIEWS_PATH)
    annotator_a = _load_annotation(ANNOTATOR_A_PATH)
    annotator_b = _load_annotation(ANNOTATOR_B_PATH)
    _require_complete(annotator_a, "Annotator A")
    _require_complete(annotator_b, "Annotator B")
    adjudication = _read_adjudication()

    source_ids = set(source["review_id"])
    if set(annotator_a["review_id"]) != source_ids:
        raise ValueError("Annotator A must contain every source review exactly once.")
    if len(annotator_b) != ANNOTATOR_B_EXPECTED_ROWS:
        raise ValueError(
            f"Annotator B must contain exactly {ANNOTATOR_B_EXPECTED_ROWS} rows; "
            f"found {len(annotator_b)}."
        )
    locked_ids = set(
        source.loc[source["evaluation_partition"].eq("locked_test"), "review_id"]
    )
    if not locked_ids.issubset(set(annotator_b["review_id"])):
        raise ValueError("Annotator B no longer contains every locked-test row.")
    source_text = source.set_index("review_id")["review_text"]
    for label, annotation_frame in (
        ("Annotator A", annotator_a),
        ("Annotator B", annotator_b),
    ):
        expected_text = annotation_frame["review_id"].map(source_text)
        if (
            expected_text.isna().any()
            or not annotation_frame["review_text"].eq(expected_text).all()
        ):
            raise ValueError(f"{label} review_text differs from the locked source.")

    paired = annotator_b.merge(
        annotator_a,
        on="review_id",
        how="left",
        suffixes=("_b", "_a"),
        validate="one_to_one",
    )
    semantic_disagreement = pd.Series(False, index=paired.index)
    for column in CORE_LABEL_COLUMNS:
        semantic_disagreement |= ~paired[f"{column}_a"].eq(paired[f"{column}_b"])
    expected_ids = set(paired.loc[semantic_disagreement, "review_id"])
    a_with_groups = annotator_a.merge(
        source[["review_id", "text_group_id"]],
        on="review_id",
        validate="one_to_one",
    )
    for _, group in a_with_groups.groupby("text_group_id"):
        if any(
            group[column].nunique(dropna=False) > 1 for column in CORE_LABEL_COLUMNS
        ):
            expected_ids.update(group["review_id"])

    disagreement_ids = set(adjudication.get("review_id", pd.Series(dtype=str)))
    if disagreement_ids != expected_ids:
        raise ValueError(
            "Adjudication queue is stale or incomplete. Rebuild it before finalizing labels."
        )
    if disagreement_ids:
        _validate_adjudication_decisions(adjudication)

    final = annotator_a.copy()
    final["annotation_source"] = "human_single"
    b_ids = set(annotator_b["review_id"])
    final.loc[final["review_id"].isin(b_ids), "annotation_source"] = "human_agreed"

    if disagreement_ids:
        adjudication_index = adjudication.set_index("review_id")
        for review_id in disagreement_ids:
            mask = final["review_id"].eq(review_id)
            row = adjudication_index.loc[review_id]
            for column in CORE_LABEL_COLUMNS:
                final.loc[mask, column] = row[f"final_{column}"]
            final.loc[mask, "secondary_themes"] = row.get("final_secondary_themes", "")
            final.loc[mask, "annotation_confidence"] = row[
                "final_annotation_confidence"
            ]
            final.loc[mask, "annotation_notes"] = row.get("adjudication_notes", "")
            final.loc[mask, "annotation_source"] = "human_adjudicated"

    validation = validate_annotations(final[ANNOTATION_COLUMNS])
    if not validation.valid:
        raise ValueError(f"Final labels failed validation: {validation.errors}")

    final_with_groups = final.merge(
        source[["review_id", "text_group_id"]],
        on="review_id",
        validate="one_to_one",
    )
    for text_group_id, group in final_with_groups.groupby("text_group_id"):
        if any(
            group[column].nunique(dropna=False) > 1 for column in CORE_LABEL_COLUMNS
        ):
            raise ValueError(
                f"Final labels remain inconsistent within duplicate text group {text_group_id}."
            )

    merged = source.merge(
        final.drop(columns=["review_text"]),
        on="review_id",
        how="left",
        validate="one_to_one",
    )
    merged["recommendation_text_relation"] = merged.apply(
        lambda row: derive_relation(
            row["recommendation"],
            row["text_informativeness"],
            row["sentiment_composition"],
        ),
        axis=1,
    )
    LABELED_REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(LABELED_REVIEWS_PATH, index=False, encoding="utf-8")
    _set_adjudication_report_status(
        f"Adjudication status: **Complete** — all {len(adjudication)} queued rows "
        "have validated final human decisions, and 262 labels are finalized."
    )
    return merged
