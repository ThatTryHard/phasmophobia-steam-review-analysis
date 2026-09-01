"""Central project paths resolved consistently from the repository root."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(
    os.environ.get(
        "PHASMA_PROJECT_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
ANNOTATION_DIR = DATA_DIR / "annotations"
PROCESSED_DIR = DATA_DIR / "processed"
DASHBOARD_DATA_DIR = DATA_DIR / "dashboard"
EXTERNAL_DIR = DATA_DIR / "external"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"

RAW_REVIEWS_PATH = RAW_DIR / "reviews.csv"
SPLIT_MANIFEST_PATH = RAW_DIR / "split_manifest.csv"
SOURCE_MANIFEST_PATH = RAW_DIR / "source_manifest.json"

ANNOTATOR_A_PATH = ANNOTATION_DIR / "annotator_a_all_262.csv"
ANNOTATOR_B_PATH = ANNOTATION_DIR / "annotator_b_blind_80.csv"
ADJUDICATION_PATH = ANNOTATION_DIR / "adjudication_queue.csv"

LABELED_REVIEWS_PATH = PROCESSED_DIR / "labeled_reviews.csv"
FEATURED_REVIEWS_PATH = PROCESSED_DIR / "featured_reviews.csv"

PREVALENCE_RESULTS_PATH = PROCESSED_DIR / "prevalence_results.csv"
BEHAVIOR_RESULTS_PATH = PROCESSED_DIR / "behavior_results.csv"
ASSOCIATION_RESULTS_PATH = PROCESSED_DIR / "association_results.csv"
SENSITIVITY_RESULTS_PATH = PROCESSED_DIR / "sensitivity_results.csv"

CV_RESULTS_PATH = PROCESSED_DIR / "cv_results.csv"
TEST_RESULTS_PATH = PROCESSED_DIR / "test_results.csv"
TEST_PREDICTIONS_PATH = PROCESSED_DIR / "test_predictions.csv"
MODEL_PATH = MODELS_DIR / "sentiment_pipeline.joblib"
MODEL_MANIFEST_PATH = MODELS_DIR / "model_manifest.json"
EXTERNAL_REVIEWS_PATH = EXTERNAL_DIR / "future_update_reviews.csv"
EXTERNAL_RESULTS_PATH = PROCESSED_DIR / "external_validation_results.csv"


def ensure_output_directories() -> None:
    """Create only known project output directories."""

    for path in (
        RAW_DIR,
        ANNOTATION_DIR,
        PROCESSED_DIR,
        DASHBOARD_DATA_DIR,
        EXTERNAL_DIR,
        MODELS_DIR,
        REPORTS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
