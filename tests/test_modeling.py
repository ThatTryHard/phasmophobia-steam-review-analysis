import unittest

import pandas as pd

from phasma_review.modeling import repeated_group_cv, select_text_model


class ModelingTests(unittest.TestCase):
    def test_one_standard_error_rule_prefers_simpler_eligible_model(self):
        rows = []
        values = {
            "word_unigram_logreg": [0.68, 0.72, 0.70, 0.70],
            "word_1_2gram_logreg": [0.71, 0.73, 0.69, 0.71],
            "char_3_5gram_logreg": [0.69, 0.74, 0.70, 0.71],
        }
        for model, scores in values.items():
            for score in scores:
                rows.append(
                    {
                        "model": model,
                        "macro_f1": score,
                        "balanced_accuracy": score,
                        "accuracy": score,
                    }
                )
        selected, summary = select_text_model(pd.DataFrame(rows))
        self.assertEqual(selected, "word_unigram_logreg")
        self.assertEqual(int(summary["selected"].sum()), 1)

    def test_group_cv_runs_with_duplicate_rows(self):
        vocabulary = {
            "Positive_only": "great fun love",
            "Negative_only": "bad broken hate",
            "Mixed": "fun but broken",
            "Neutral_non_evaluative": "question feature description",
        }
        rows = []
        for label, words in vocabulary.items():
            for group_number in range(3):
                for _ in range(2):
                    rows.append(
                        {
                            "analysis_review": f"{words} token{group_number}",
                            "sentiment_composition": label,
                            "text_group_id": f"{label}-{group_number}",
                            "recommendation": (
                                "Recommended"
                                if label in {"Positive_only", "Mixed"}
                                else "Not Recommended"
                            ),
                        }
                    )
        results = repeated_group_cv(pd.DataFrame(rows), repeats=1)
        self.assertEqual(
            set(results["model"]),
            {
                "most_frequent",
                "steam_recommendation_mapping",
                "word_unigram_logreg",
                "word_1_2gram_logreg",
                "char_3_5gram_logreg",
            },
        )


if __name__ == "__main__":
    unittest.main()
