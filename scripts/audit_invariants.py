"""Read-only checks for the critical data and split contracts."""

from __future__ import annotations

import json

import pandas as pd

from phasma_review.paths import (
    ADJUDICATION_PATH,
    ANNOTATOR_A_PATH,
    ANNOTATOR_B_PATH,
    FEATURED_REVIEWS_PATH,
    LABELED_REVIEWS_PATH,
    MODEL_MANIFEST_PATH,
    RAW_REVIEWS_PATH,
    SOURCE_MANIFEST_PATH,
    SPLIT_MANIFEST_PATH,
)
from phasma_review.prepare import FORBIDDEN_IDENTITY_COLUMNS
from phasma_review.schema import ANNOTATION_COLUMNS
from phasma_review.utils import sha256_file, sha256_text_file


def main() -> None:
    source = pd.read_csv(RAW_REVIEWS_PATH)
    annotator_a = pd.read_csv(ANNOTATOR_A_PATH, encoding="utf-8-sig")
    annotator_b = pd.read_csv(ANNOTATOR_B_PATH, encoding="utf-8-sig")
    assert len(source) == 262
    assert not FORBIDDEN_IDENTITY_COLUMNS.intersection(source.columns)
    assert list(annotator_a.columns) == ANNOTATION_COLUMNS
    assert list(annotator_b.columns) == ANNOTATION_COLUMNS
    assert len(annotator_a) == 262
    assert len(annotator_b) == 80
    leakage = source.groupby("text_group_id")["evaluation_partition"].nunique().max()
    assert leakage == 1
    locked = set(
        source.loc[source["evaluation_partition"].eq("locked_test"), "review_id"]
    )
    assert locked.issubset(set(annotator_b["review_id"]))
    source_manifest = json.loads(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert source_manifest["reviews_csv_sha256"] == sha256_file(RAW_REVIEWS_PATH)
    assert source_manifest["split_manifest_sha256"] == sha256_file(SPLIT_MANIFEST_PATH)
    for csv_path, workbook_path in (
        (ANNOTATOR_A_PATH, ANNOTATOR_A_PATH.with_suffix(".xlsx")),
        (ANNOTATOR_B_PATH, ANNOTATOR_B_PATH.with_suffix(".xlsx")),
    ):
        csv = pd.read_csv(csv_path, encoding="utf-8-sig", keep_default_na=False)
        workbook = pd.read_excel(
            workbook_path,
            sheet_name="Annotations",
            dtype=str,
            keep_default_na=False,
            engine="openpyxl",
        )
        assert list(workbook.columns) == ANNOTATION_COLUMNS
        pd.testing.assert_frame_equal(workbook, csv, check_dtype=False)

    if ADJUDICATION_PATH.exists():
        adjudication = pd.read_csv(
            ADJUDICATION_PATH,
            encoding="utf-8-sig",
            keep_default_na=False,
        )
        adjudication_workbook = pd.read_excel(
            ADJUDICATION_PATH.with_suffix(".xlsx"),
            sheet_name="Adjudication",
            dtype=str,
            keep_default_na=False,
            engine="openpyxl",
        )
        pd.testing.assert_frame_equal(
            adjudication_workbook,
            adjudication,
            check_dtype=False,
        )
        required_final = [
            "final_language_status",
            "final_text_informativeness",
            "final_sentiment_composition",
            "final_primary_theme",
            "final_annotation_confidence",
        ]
        assert adjudication[required_final].ne("").all(axis=None)

    if LABELED_REVIEWS_PATH.exists():
        labeled = pd.read_csv(LABELED_REVIEWS_PATH)
        assert len(labeled) == len(source)
        assert set(labeled["review_id"]) == set(source["review_id"])
        assert labeled["annotation_source"].isin(
            {"human_single", "human_agreed", "human_adjudicated"}
        ).all()
        assert not labeled["sentiment_composition"].isna().any()

    if MODEL_MANIFEST_PATH.exists():
        model_manifest = json.loads(MODEL_MANIFEST_PATH.read_text(encoding="utf-8"))
        assert model_manifest["production_approved"] is False
        # Generated CSV hashes normalize CRLF/LF so Windows-built artifacts
        # remain verifiable in GitHub Actions on Linux.
        assert model_manifest["label_file_sha256"] == sha256_text_file(
            LABELED_REVIEWS_PATH
        )
        assert model_manifest["featured_file_sha256"] == sha256_text_file(
            FEATURED_REVIEWS_PATH
        )

    print(
        "Critical data, privacy, blinding, adjudication, split, and artifact "
        "invariants pass."
    )


if __name__ == "__main__":
    main()
