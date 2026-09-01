import unittest

import pandas as pd

from phasma_review.schema import (
    ANNOTATION_COLUMNS,
    derive_relation,
    validate_annotations,
)


def row(**overrides):
    values = {
        "review_id": "R0001",
        "review_text": "fun but buggy",
        "language_status": "English",
        "text_informativeness": "Sufficient",
        "sentiment_composition": "Mixed",
        "primary_theme": "Technical_issue",
        "secondary_themes": "Gameplay_praise",
        "annotation_confidence": "Medium",
        "annotation_notes": "",
    }
    values.update(overrides)
    return values


class SchemaTests(unittest.TestCase):
    def test_complete_valid_annotation(self):
        result = validate_annotations(pd.DataFrame([row()], columns=ANNOTATION_COLUMNS))
        self.assertTrue(result.valid)

    def test_confidence_is_required(self):
        result = validate_annotations(
            pd.DataFrame([row(annotation_confidence="")], columns=ANNOTATION_COLUMNS)
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.completed_rows, 0)

    def test_insufficient_requires_not_applicable(self):
        result = validate_annotations(
            pd.DataFrame(
                [
                    row(
                        text_informativeness="Insufficient",
                        sentiment_composition="Mixed",
                    )
                ],
                columns=ANNOTATION_COLUMNS,
            )
        )
        self.assertFalse(result.valid)

    def test_secondary_theme_and_low_confidence_rules(self):
        duplicate_theme = validate_annotations(
            pd.DataFrame(
                [row(secondary_themes="Technical_issue")],
                columns=ANNOTATION_COLUMNS,
            )
        )
        self.assertFalse(duplicate_theme.valid)
        low_without_note = validate_annotations(
            pd.DataFrame(
                [row(annotation_confidence="Low", annotation_notes="")],
                columns=ANNOTATION_COLUMNS,
            )
        )
        self.assertFalse(low_without_note.valid)

    def test_relation_taxonomy_does_not_conflate_mixed(self):
        self.assertEqual(
            derive_relation("Recommended", "Sufficient", "Mixed"),
            "Qualified / mixed opinion",
        )
        self.assertEqual(
            derive_relation("Recommended", "Sufficient", "Negative_only"),
            "Hard contradiction",
        )
        self.assertEqual(
            derive_relation("Recommended", "Insufficient", "Not_applicable"),
            "Insufficient text",
        )


if __name__ == "__main__":
    unittest.main()
