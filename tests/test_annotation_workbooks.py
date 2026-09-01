import unittest

import pandas as pd

from phasma_review.paths import ANNOTATION_DIR, ANNOTATOR_A_PATH, ANNOTATOR_B_PATH
from phasma_review.schema import ANNOTATION_COLUMNS


class AnnotationWorkbookTests(unittest.TestCase):
    def test_human_forms_match_blinded_csv_contracts(self):
        pairs = [
            (ANNOTATOR_A_PATH, ANNOTATION_DIR / "annotator_a_all_262.xlsx"),
            (ANNOTATOR_B_PATH, ANNOTATION_DIR / "annotator_b_blind_80.xlsx"),
        ]
        for csv_path, workbook_path in pairs:
            with self.subTest(workbook=workbook_path.name):
                csv = pd.read_csv(csv_path, encoding="utf-8-sig", keep_default_na=False)
                workbook = pd.read_excel(
                    workbook_path,
                    sheet_name="Annotations",
                    dtype=str,
                    keep_default_na=False,
                    engine="openpyxl",
                )
                self.assertEqual(list(workbook.columns), ANNOTATION_COLUMNS)
                pd.testing.assert_frame_equal(workbook, csv, check_dtype=False)


if __name__ == "__main__":
    unittest.main()
