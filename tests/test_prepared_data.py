import unittest

import pandas as pd

from phasma_review.paths import ANNOTATOR_A_PATH, ANNOTATOR_B_PATH, RAW_REVIEWS_PATH
from phasma_review.prepare import FORBIDDEN_IDENTITY_COLUMNS
from phasma_review.schema import ANNOTATION_COLUMNS, validate_annotations


class PreparedDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = pd.read_csv(RAW_REVIEWS_PATH)
        cls.a = pd.read_csv(
            ANNOTATOR_A_PATH, encoding="utf-8-sig", keep_default_na=False
        )
        cls.b = pd.read_csv(
            ANNOTATOR_B_PATH, encoding="utf-8-sig", keep_default_na=False
        )

    def test_full_universe_and_privacy(self):
        self.assertEqual(len(self.source), 262)
        self.assertFalse(FORBIDDEN_IDENTITY_COLUMNS.intersection(self.source.columns))
        self.assertEqual(self.source["review_id"].nunique(), 262)

    def test_duplicate_groups_do_not_cross_holdout(self):
        partitions_per_group = self.source.groupby("text_group_id")[
            "evaluation_partition"
        ].nunique()
        self.assertEqual(int(partitions_per_group.max()), 1)

    def test_annotation_files_are_blinded_sized_and_schema_valid(self):
        self.assertEqual(list(self.a.columns), ANNOTATION_COLUMNS)
        self.assertEqual(list(self.b.columns), ANNOTATION_COLUMNS)
        self.assertEqual(len(self.a), 262)
        self.assertEqual(len(self.b), 80)

        # Lifecycle fix: these are intentionally mutable annotation files.
        # Requiring every label to remain blank makes CI fail after a valid
        # human annotation import, so test the locked content and codebook
        # validity at either the blank, partial, or complete project stage.
        source_text = self.source.set_index("review_id")["review_text"]
        self.assertTrue(
            self.a["review_text"].eq(self.a["review_id"].map(source_text)).all()
        )
        self.assertTrue(
            self.b["review_text"].eq(self.b["review_id"].map(source_text)).all()
        )
        self.assertEqual(validate_annotations(self.a).errors, ())
        self.assertEqual(validate_annotations(self.b).errors, ())

    def test_all_locked_test_rows_are_double_annotated(self):
        locked_ids = set(
            self.source.loc[
                self.source["evaluation_partition"].eq("locked_test"), "review_id"
            ]
        )
        self.assertTrue(locked_ids.issubset(set(self.b["review_id"])))


if __name__ == "__main__":
    unittest.main()
