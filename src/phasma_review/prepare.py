"""Privacy-safe source migration and blinded annotation preparation."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from .features import clean_review_text, normalized_text_key
from .paths import (
    ANNOTATOR_A_PATH,
    ANNOTATOR_B_PATH,
    RAW_REVIEWS_PATH,
    SOURCE_MANIFEST_PATH,
    SPLIT_MANIFEST_PATH,
    ensure_output_directories,
)
from .schema import ANNOTATION_COLUMNS
from .utils import (
    RANDOM_SEED,
    largest_remainder_allocation,
    sha256_file,
    write_json,
)

PUBLIC_SOURCE_COLUMNS = [
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

FORBIDDEN_IDENTITY_COLUMNS = {
    "author_name",
    "author_steamid",
    "author_steamid_norm",
    "recommendation_id",
    "recommendation_id_norm",
}


def _parse_date(value: object, default_year: int = 2026) -> str:
    if pd.isna(value):
        return ""
    text = re.sub(r"^Posted:\s*", "", str(value).strip(), flags=re.IGNORECASE)
    if not re.search(r"\b\d{4}\b", text):
        text = f"{text} {default_year}"
    parsed = pd.to_datetime(text, errors="coerce")
    return "" if pd.isna(parsed) else parsed.strftime("%Y-%m-%d")


def _fallback_helpful_count(value: object) -> int:
    if not isinstance(value, str):
        return 0
    match = re.search(
        r"(\d+)\s+people? found this review helpful",
        value,
        flags=re.IGNORECASE,
    )
    return int(match.group(1)) if match else 0


def _as_bool_or_missing(value: object) -> object:
    if pd.isna(value) or str(value).strip() == "":
        return pd.NA
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    return pd.NA


def sanitize_legacy_reviews(legacy: pd.DataFrame) -> pd.DataFrame:
    """Create the deidentified 262-row source universe.

    No author name, Steam ID, recommendation ID, assisted label, or heuristic
    flag is retained. Exact duplicate text is grouped so it cannot be split
    across development and test partitions.
    """

    required = {"review_text", "recommendation", "playtime_hours"}
    missing = sorted(required - set(legacy.columns))
    if missing:
        raise ValueError(f"Legacy source is missing required columns: {missing}")

    frame = legacy.copy()
    frame["review_text"] = frame["review_text"].map(clean_review_text)
    frame = frame[frame["review_text"].ne("")].reset_index(drop=True)
    frame["recommendation"] = frame["recommendation"].fillna("").astype(str).str.strip()
    invalid_recommendations = sorted(
        set(frame["recommendation"]) - {"Recommended", "Not Recommended"}
    )
    if invalid_recommendations:
        raise ValueError(f"Unexpected recommendation values: {invalid_recommendations}")

    if "review_date" not in frame:
        frame["review_date"] = ""
    frame["review_date"] = frame["review_date"].map(_parse_date)
    frame["playtime_hours"] = pd.to_numeric(frame["playtime_hours"], errors="coerce")
    if frame["playtime_hours"].lt(0).any():
        raise ValueError("playtime_hours cannot be negative.")

    for column in (
        "helpful_count",
        "funny_count",
        "weighted_vote_score",
        "comment_count",
    ):
        if column not in frame:
            frame[column] = pd.NA
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if "helpful_text" in frame:
        missing_helpful = frame["helpful_count"].isna()
        frame.loc[missing_helpful, "helpful_count"] = frame.loc[
            missing_helpful, "helpful_text"
        ].map(_fallback_helpful_count)
    frame["helpful_count"] = frame["helpful_count"].fillna(0).astype(int)
    frame["funny_count"] = frame["funny_count"].fillna(0).astype(int)
    for column in ("helpful_count", "funny_count", "comment_count"):
        if frame[column].dropna().lt(0).any():
            raise ValueError(f"{column} cannot be negative.")
    if (
        frame["weighted_vote_score"].dropna().lt(0).any()
        or frame["weighted_vote_score"].dropna().gt(1).any()
    ):
        raise ValueError("weighted_vote_score must be between zero and one.")

    for column in (
        "steam_purchase",
        "received_for_free",
        "written_during_early_access",
    ):
        if column not in frame:
            frame[column] = pd.NA
        frame[column] = frame[column].map(_as_bool_or_missing).astype("boolean")

    frame["_text_key"] = frame["review_text"].map(normalized_text_key)
    unique_keys = sorted(frame["_text_key"].unique())
    group_lookup = {key: f"G{index:04d}" for index, key in enumerate(unique_keys, 1)}
    frame["text_group_id"] = frame["_text_key"].map(group_lookup)

    # The test partition is locked before human labels exist.
    # Group-aware splitting prevents identical review text from crossing the boundary.
    splitter = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=RANDOM_SEED,
    )
    _train_index, test_index = next(
        splitter.split(
            frame,
            y=frame["recommendation"],
            groups=frame["text_group_id"],
        )
    )
    frame["evaluation_partition"] = "development"
    frame.loc[test_index, "evaluation_partition"] = "locked_test"

    # Randomized public IDs prevent the source row order and author identifiers
    # from becoming part of the analytical contract.
    frame = frame.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    frame["review_id"] = [f"R{index:04d}" for index in range(1, len(frame) + 1)]

    result = frame.reindex(columns=PUBLIC_SOURCE_COLUMNS)
    forbidden_present = FORBIDDEN_IDENTITY_COLUMNS.intersection(result.columns)
    if forbidden_present:
        raise AssertionError(
            f"Identity columns survived sanitization: {forbidden_present}"
        )
    if result["review_id"].duplicated().any():
        raise AssertionError("review_id must be unique.")
    return result


def _blank_template(rows: pd.DataFrame) -> pd.DataFrame:
    template = rows[["review_id", "review_text"]].copy()
    for column in ANNOTATION_COLUMNS[2:]:
        template[column] = ""
    return template[ANNOTATION_COLUMNS]


def _select_annotator_b_rows(
    source: pd.DataFrame, target_rows: int = 80
) -> pd.DataFrame:
    """Select all locked-test rows plus a recommendation-balanced dev subset."""

    locked = source[source["evaluation_partition"].eq("locked_test")].copy()
    if len(locked) > target_rows:
        raise ValueError("Locked test set exceeds Annotator B target size.")

    needed = target_rows - len(locked)
    development = source[source["evaluation_partition"].eq("development")].copy()
    # Sample distinct text groups for the extra agreement subset.
    candidates = development.drop_duplicates("text_group_id")
    sizes = candidates["recommendation"].value_counts().to_dict()
    allocation = largest_remainder_allocation(sizes, needed)
    extra_parts: list[pd.DataFrame] = []
    for offset, (recommendation, count) in enumerate(sorted(allocation.items())):
        group = candidates[candidates["recommendation"].eq(recommendation)]
        extra_parts.append(
            group.sample(n=count, random_state=RANDOM_SEED + 100 + offset)
        )
    extra = (
        pd.concat(extra_parts, ignore_index=True) if extra_parts else candidates.head(0)
    )
    selected = pd.concat([locked, extra], ignore_index=True)
    if len(selected) != target_rows:
        raise AssertionError(
            f"Expected {target_rows} Annotator B rows, found {len(selected)}"
        )
    return selected.sample(frac=1, random_state=RANDOM_SEED + 200).reset_index(
        drop=True
    )


def write_annotation_templates(source: pd.DataFrame, overwrite: bool = False) -> None:
    """Write blinded files without overwriting annotation work by default."""

    ensure_output_directories()
    for path in (ANNOTATOR_A_PATH, ANNOTATOR_B_PATH):
        if path.exists() and not overwrite:
            raise FileExistsError(
                f"Refusing to overwrite existing annotation file: {path}. "
                "Use overwrite=True only before annotation starts."
            )

    annotator_a = _blank_template(
        source.sample(frac=1, random_state=RANDOM_SEED + 300).reset_index(drop=True)
    )
    annotator_b = _blank_template(_select_annotator_b_rows(source))
    annotator_a.to_csv(ANNOTATOR_A_PATH, index=False, encoding="utf-8-sig")
    annotator_b.to_csv(ANNOTATOR_B_PATH, index=False, encoding="utf-8-sig")


def save_sanitized_source(source: pd.DataFrame) -> None:
    ensure_output_directories()
    source.to_csv(RAW_REVIEWS_PATH, index=False, encoding="utf-8")
    source[["review_id", "text_group_id", "evaluation_partition"]].to_csv(
        SPLIT_MANIFEST_PATH,
        index=False,
        encoding="utf-8",
    )
    dates = pd.to_datetime(source["review_date"], errors="coerce")
    # Persist exact corpus/split checksums and known scope facts so a changed
    # input cannot masquerade as the frozen source set.
    write_json(
        {
            "schema_version": "2.0",
            "sanitization_version": "privacy_safe_full_corpus_v2",
            "random_seed": RANDOM_SEED,
            "row_count": len(source),
            "unique_text_groups": int(source["text_group_id"].nunique()),
            "recommendation_counts": source["recommendation"].value_counts().to_dict(),
            "partition_counts": source["evaluation_partition"].value_counts().to_dict(),
            "review_date_min": dates.min().strftime("%Y-%m-%d"),
            "review_date_max": dates.max().strftime("%Y-%m-%d"),
            "missing_counts": source.isna().sum().astype(int).to_dict(),
            "removed_identity_fields": sorted(FORBIDDEN_IDENTITY_COLUMNS),
            "reviews_csv_sha256": sha256_file(RAW_REVIEWS_PATH),
            "split_manifest_sha256": sha256_file(SPLIT_MANIFEST_PATH),
        },
        SOURCE_MANIFEST_PATH,
    )


def migrate_and_prepare(
    legacy_path: Path,
    overwrite_annotations: bool = False,
) -> pd.DataFrame:
    # Refuse before touching the immutable source/split if human
    # annotation work already exists.
    if not overwrite_annotations:
        existing = [
            path for path in (ANNOTATOR_A_PATH, ANNOTATOR_B_PATH) if path.exists()
        ]
        if existing:
            raise FileExistsError(
                "Refusing migration because annotation files already exist: "
                + ", ".join(str(path) for path in existing)
            )
    legacy = pd.read_csv(legacy_path)
    source = sanitize_legacy_reviews(legacy)
    save_sanitized_source(source)
    write_annotation_templates(source, overwrite=overwrite_annotations)
    return source


def prepare_from_sanitized_source(overwrite_annotations: bool = False) -> pd.DataFrame:
    if not RAW_REVIEWS_PATH.exists():
        raise FileNotFoundError(
            f"Sanitized source not found: {RAW_REVIEWS_PATH}. Run migration first."
        )
    source = pd.read_csv(RAW_REVIEWS_PATH)
    forbidden = FORBIDDEN_IDENTITY_COLUMNS.intersection(source.columns)
    if forbidden:
        raise ValueError(f"Sanitized source contains forbidden columns: {forbidden}")
    write_annotation_templates(source, overwrite=overwrite_annotations)
    return source
