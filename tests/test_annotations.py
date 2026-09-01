import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from phasma_review import annotations
from phasma_review.schema import ANNOTATION_COLUMNS


def label_row(review_id, text, sentiment, theme="General_evaluation"):
    return {
        "review_id": review_id,
        "review_text": text,
        "language_status": "English",
        "text_informativeness": "Sufficient",
        "sentiment_composition": sentiment,
        "primary_theme": theme,
        "secondary_themes": "",
        "annotation_confidence": "High",
        "annotation_notes": "",
    }


class AnnotationWorkflowTests(unittest.TestCase):
    @staticmethod
    def _adjudication_row() -> dict[str, str]:
        return {
            "review_id": "R1",
            "review_text": "mixed after the update",
            "adjudication_reason": "independent_annotator_disagreement",
            "language_status_a": "English",
            "language_status_b": "English",
            "final_language_status": "English",
            "text_informativeness_a": "Sufficient",
            "text_informativeness_b": "Sufficient",
            "final_text_informativeness": "Sufficient",
            "sentiment_composition_a": "Mixed",
            "sentiment_composition_b": "Negative_only",
            "final_sentiment_composition": "Mixed",
            "primary_theme_a": "Update_or_change",
            "primary_theme_b": "Technical_issue",
            "final_primary_theme": "Update_or_change",
            "final_secondary_themes": "Technical_issue",
            "final_annotation_confidence": "Medium",
            "adjudication_notes": "Consensus retained both expressed aspects.",
        }

    def test_adjudication_workbook_import_preserves_locked_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_path = root / "adjudication_queue.csv"
            workbook_path = root / "completed.xlsx"
            workbook_path.write_bytes(b"mock workbook")
            current = pd.DataFrame([self._adjudication_row()])
            current.to_csv(queue_path, index=False, encoding="utf-8-sig")
            imported = current.copy()
            imported.loc[0, "review_text"] = "edited text"

            with (
                patch.object(annotations, "ADJUDICATION_PATH", queue_path),
                patch.object(
                    annotations,
                    "AGREEMENT_REPORT_PATH",
                    root / "annotation_quality.md",
                ),
                patch.object(
                    annotations.pd,
                    "read_excel",
                    return_value=imported,
                ),
            ):
                with self.assertRaisesRegex(ValueError, "protected column"):
                    annotations.import_adjudication_workbook(workbook_path)

    def test_valid_adjudication_workbook_round_trips_to_canonical_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue_path = root / "adjudication_queue.csv"
            workbook_path = root / "completed.xlsx"
            workbook_bytes = b"mock workbook"
            workbook_path.write_bytes(workbook_bytes)
            current = pd.DataFrame([self._adjudication_row()])
            current.loc[0, "final_sentiment_composition"] = ""
            current.loc[0, "final_primary_theme"] = ""
            current.loc[0, "final_secondary_themes"] = ""
            current.loc[0, "final_annotation_confidence"] = ""
            current.loc[0, "adjudication_notes"] = ""
            current.to_csv(queue_path, index=False, encoding="utf-8-sig")
            completed = pd.DataFrame([self._adjudication_row()])

            with (
                patch.object(annotations, "ADJUDICATION_PATH", queue_path),
                patch.object(
                    annotations,
                    "AGREEMENT_REPORT_PATH",
                    root / "annotation_quality.md",
                ),
                patch.object(
                    annotations.pd,
                    "read_excel",
                    return_value=completed,
                ),
            ):
                result = annotations.import_adjudication_workbook(workbook_path)

            pd.testing.assert_frame_equal(result, completed)
            saved = pd.read_csv(
                queue_path,
                encoding="utf-8-sig",
                keep_default_na=False,
            )
            pd.testing.assert_frame_equal(saved, completed)
            self.assertEqual(
                queue_path.with_suffix(".xlsx").read_bytes(),
                workbook_bytes,
            )

    def test_disagreement_and_duplicate_inconsistency_require_adjudication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "reviews.csv"
            a_path = root / "a.csv"
            b_path = root / "b.csv"
            adjudication_path = root / "adjudication.csv"
            agreement_csv = root / "agreement.csv"
            agreement_report = root / "agreement.md"
            final_path = root / "labeled.csv"
            source = pd.DataFrame(
                [
                    {
                        "review_id": "R1",
                        "review_text": "same",
                        "text_group_id": "G1",
                        "evaluation_partition": "development",
                        "recommendation": "Recommended",
                    },
                    {
                        "review_id": "R2",
                        "review_text": "same",
                        "text_group_id": "G1",
                        "evaluation_partition": "development",
                        "recommendation": "Recommended",
                    },
                    {
                        "review_id": "R3",
                        "review_text": "bad",
                        "text_group_id": "G2",
                        "evaluation_partition": "locked_test",
                        "recommendation": "Not Recommended",
                    },
                    {
                        "review_id": "R4",
                        "review_text": "great",
                        "text_group_id": "G3",
                        "evaluation_partition": "locked_test",
                        "recommendation": "Recommended",
                    },
                ]
            )
            source.to_csv(source_path, index=False)
            a = pd.DataFrame(
                [
                    label_row("R1", "same", "Positive_only"),
                    label_row("R2", "same", "Negative_only"),
                    label_row("R3", "bad", "Negative_only"),
                    label_row("R4", "great", "Positive_only"),
                ],
                columns=ANNOTATION_COLUMNS,
            )
            b = pd.DataFrame(
                [
                    label_row("R3", "bad", "Mixed"),
                    label_row("R4", "great", "Positive_only"),
                ],
                columns=ANNOTATION_COLUMNS,
            )
            a.to_csv(a_path, index=False)
            b.to_csv(b_path, index=False)
            patched = {
                "RAW_REVIEWS_PATH": source_path,
                "ANNOTATOR_A_PATH": a_path,
                "ANNOTATOR_B_PATH": b_path,
                "ADJUDICATION_PATH": adjudication_path,
                "AGREEMENT_CSV_PATH": agreement_csv,
                "AGREEMENT_REPORT_PATH": agreement_report,
                "LABELED_REVIEWS_PATH": final_path,
                "ANNOTATOR_B_EXPECTED_ROWS": 2,
            }
            with patch.multiple(annotations, **patched):
                queue = annotations.build_adjudication_queue()
                self.assertEqual(set(queue["review_id"]), {"R1", "R2", "R3"})
                queue.loc[
                    queue["review_id"].isin(["R1", "R2"]), "final_language_status"
                ] = "English"
                queue.loc[
                    queue["review_id"].isin(["R1", "R2"]), "final_text_informativeness"
                ] = "Sufficient"
                queue.loc[
                    queue["review_id"].isin(["R1", "R2"]), "final_sentiment_composition"
                ] = "Positive_only"
                queue.loc[
                    queue["review_id"].isin(["R1", "R2"]), "final_primary_theme"
                ] = "General_evaluation"
                queue.loc[queue["review_id"].eq("R3"), "final_language_status"] = (
                    "English"
                )
                queue.loc[queue["review_id"].eq("R3"), "final_text_informativeness"] = (
                    "Sufficient"
                )
                queue.loc[
                    queue["review_id"].eq("R3"), "final_sentiment_composition"
                ] = "Negative_only"
                queue.loc[queue["review_id"].eq("R3"), "final_primary_theme"] = (
                    "General_evaluation"
                )
                queue["final_annotation_confidence"] = "High"
                queue.to_csv(adjudication_path, index=False)
                final = annotations.finalize_labels()
                duplicate_labels = final[final["text_group_id"].eq("G1")][
                    "sentiment_composition"
                ]
                self.assertEqual(duplicate_labels.nunique(), 1)
                self.assertEqual(
                    final.loc[final["review_id"].eq("R3"), "annotation_source"].iloc[0],
                    "human_adjudicated",
                )


if __name__ == "__main__":
    unittest.main()
