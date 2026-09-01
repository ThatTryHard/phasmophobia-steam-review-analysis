import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from phasma_review.schema import derive_relation


class SyntheticPipelineTests(unittest.TestCase):
    def test_analysis_model_and_dashboard_end_to_end(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            processed = root / "data" / "processed"
            raw = root / "data" / "raw"
            processed.mkdir(parents=True)
            raw.mkdir(parents=True)
            rows = []
            classes = {
                "Positive_only": (
                    "great fun love ghosts",
                    "Recommended",
                    "Gameplay_praise",
                ),
                "Negative_only": (
                    "bad broken hate crash",
                    "Not Recommended",
                    "Technical_issue",
                ),
                "Mixed": (
                    "fun ghosts but broken crash",
                    "Recommended",
                    "Technical_issue",
                ),
                "Neutral_non_evaluative": (
                    "question about feature settings",
                    "Not Recommended",
                    "Feature_request",
                ),
            }
            review_number = 0
            for sentiment, (text, recommendation, theme) in classes.items():
                for group_number in range(11):
                    review_number += 1
                    partition = "development" if group_number < 8 else "locked_test"
                    row = {
                        "review_id": f"R{review_number:04d}",
                        "text_group_id": f"G{review_number:04d}",
                        "evaluation_partition": partition,
                        "review_date": "2026-06-10",
                        "recommendation": recommendation,
                        "playtime_hours": float(review_number + 1),
                        "helpful_count": review_number % 3,
                        "funny_count": review_number % 2,
                        "steam_purchase": True,
                        "received_for_free": False,
                        "written_during_early_access": False,
                        "weighted_vote_score": 0.5,
                        "comment_count": 0,
                        "review_text": f"{text} example{group_number}",
                        "language_status": "English",
                        "text_informativeness": "Sufficient",
                        "sentiment_composition": sentiment,
                        "primary_theme": theme,
                        "secondary_themes": "",
                        "annotation_confidence": "High",
                        "annotation_notes": "",
                        "annotation_source": "human_agreed",
                    }
                    row["recommendation_text_relation"] = derive_relation(
                        recommendation,
                        "Sufficient",
                        sentiment,
                    )
                    rows.append(row)
            frame = pd.DataFrame(rows)
            frame.to_csv(processed / "labeled_reviews.csv", index=False)
            frame[["review_id", "text_group_id", "evaluation_partition"]].to_csv(
                raw / "split_manifest.csv",
                index=False,
            )
            frame[
                [
                    "review_id",
                    "text_group_id",
                    "evaluation_partition",
                    "review_date",
                    "recommendation",
                    "playtime_hours",
                    "helpful_count",
                    "funny_count",
                    "steam_purchase",
                    "received_for_free",
                    "written_during_early_access",
                    "weighted_vote_score",
                    "comment_count",
                    "review_text",
                ]
            ].to_csv(raw / "reviews.csv", index=False)

            command = [
                sys.executable,
                "-c",
                (
                    "from phasma_review.analysis import run_analysis; "
                    "from phasma_review.modeling import run_modeling; "
                    "from phasma_review.dashboard import run_dashboard; "
                    "run_analysis(); run_modeling(repeats=1); run_dashboard()"
                ),
            ]
            environment = os.environ.copy()
            environment["PHASMA_PROJECT_ROOT"] = str(root)
            completed = subprocess.run(
                command,
                env=environment,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((root / "reports" / "dashboard.html").exists())
            self.assertTrue((root / "models" / "model_manifest.json").exists())
            self.assertTrue((processed / "test_results.csv").exists())


if __name__ == "__main__":
    unittest.main()
