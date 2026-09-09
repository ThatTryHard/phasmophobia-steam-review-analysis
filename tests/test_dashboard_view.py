"""Presentation tests: saved evidence stays exact and review text stays inert."""

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from phasma_review import dashboard
from phasma_review.dashboard_view import render_dashboard


def embedded_payload(document):
    return json.loads(
        re.search(
            r'<script type="application/json" id="dashboard-data">(.*?)</script>',
            document,
            flags=re.DOTALL,
        ).group(1)
    )


class DashboardViewTests(unittest.TestCase):
    def test_review_text_cannot_close_json_script(self):
        review = '</script><script>alert("x")</script>& __FALLBACK__'
        document = render_dashboard({"review": review}, "<p>Fallback</p>")
        self.assertEqual(embedded_payload(document), {"review": review})
        self.assertNotIn('</script><script>alert("x")', document)
        self.assertIn("<p>Fallback</p>", document)

    def test_render_is_deterministic_and_has_no_remote_assets(self):
        payload = {"tables": {}, "agreement": [], "predictions": []}
        document = render_dashboard(payload)
        self.assertEqual(document, render_dashboard(payload))
        self.assertNotRegex(document, r'<script[^>]+src=')
        self.assertNotRegex(document, r'<link[^>]+rel=["\']stylesheet')
        self.assertIn('id="overview"', document)
        self.assertIn('id="players"', document)
        self.assertIn('id="model"', document)
        self.assertIn('id="evidence"', document)
        self.assertIn('id="font-license"', document)
        self.assertIn('data:font/woff;base64,', document)
        self.assertIn('Recommended. But what did they say?', document)
        self.assertNotIn('__JOURNAL_CSS__', document)
        self.assertNotIn('__FONT_FACE__', document)

    def test_nonfinite_payload_is_rejected(self):
        with self.assertRaises(ValueError):
            render_dashboard({"score": float("nan")})

    def test_writer_preserves_tables_and_handles_missing_supporting_files(self):
        names = (
            "kpi_summary.csv",
            "recommendation_sentiment_matrix.csv",
            "theme_summary.csv",
            "player_relation_summary.csv",
            "model_summary.csv",
            "audit_error_examples.csv",
            "review_level.csv",
        )
        tables = {name: pd.DataFrame() for name in names}
        tables["review_level.csv"] = pd.DataFrame(
            [{"review_id": "R1", "playtime_hours": float("nan")}]
        )
        original = tables["review_level.csv"].copy(deep=True)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "dashboard.html"
            with patch.multiple(
                dashboard,
                ANNOTATION_DIR=root,
                PROCESSED_DIR=root,
                MODEL_MANIFEST_PATH=root / "absent.json",
                TEST_PREDICTIONS_PATH=root / "absent.csv",
                ADJUDICATION_PATH=root / "absent-adjudication.csv",
                REPORTS_DIR=root,
                DASHBOARD_HTML_PATH=output,
            ):
                dashboard.write_dashboard_html(tables)
            payload = embedded_payload(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["agreement"], [])
        self.assertEqual(payload["manifest"], {})
        self.assertIsNone(payload["adjudication_rows"])
        self.assertEqual(
            payload["tables"]["review_level.csv"],
            [{"review_id": "R1", "playtime_hours": None}],
        )
        pd.testing.assert_frame_equal(tables["review_level.csv"], original)
