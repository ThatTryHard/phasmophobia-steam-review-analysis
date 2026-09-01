import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from phasma_review.analysis import load_labeled_reviews
from phasma_review.schema import AnnotationIncompleteError


class EvidenceGateTests(unittest.TestCase):
    def test_analysis_fails_without_human_final_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "not_created.csv"
            with (
                patch("phasma_review.analysis.LABELED_REVIEWS_PATH", missing),
                self.assertRaises(AnnotationIncompleteError),
            ):
                load_labeled_reviews()


if __name__ == "__main__":
    unittest.main()
