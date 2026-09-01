import unittest

import pandas as pd

from phasma_review.features import contains_any_phrase, engineer_features, player_group


class FeatureTests(unittest.TestCase):
    def test_phrase_boundaries_prevent_substring_false_positive(self):
        self.assertFalse(contains_any_phrase("The flag is green", ["lag"]))
        self.assertTrue(contains_any_phrase("The game has awful lag", ["lag"]))
        self.assertTrue(
            contains_any_phrase("Please bring   back the old version", ["bring back"])
        )

    def test_missing_playtime_is_not_zero(self):
        frame = pd.DataFrame({"review_text": ["fun"], "playtime_hours": [None]})
        result = engineer_features(frame)
        self.assertTrue(result.loc[0, "playtime_missing"])
        self.assertTrue(pd.isna(result.loc[0, "log_playtime"]))
        self.assertEqual(result.loc[0, "player_group"], "Unknown")

    def test_player_group_boundaries(self):
        self.assertEqual(player_group(10), "New (≤10h)")
        self.assertEqual(player_group(50), "Casual (10–50h)")
        self.assertEqual(player_group(101), "Veteran (100–300h)")


if __name__ == "__main__":
    unittest.main()
