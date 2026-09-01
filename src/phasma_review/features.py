"""Canonical text cleaning and feature engineering.

Major fix: all rows now use one implementation. Minor fix: keyword matching
uses phrase-aware word boundaries, avoiding substring errors such as matching
``lag`` inside ``flag``.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

import numpy as np
import pandas as pd

THEME_TERMS: dict[str, tuple[str, ...]] = {
    "keyword_update": (
        "update",
        "updates",
        "patch",
        "hotfix",
        "rework",
        "reworked",
        "changed",
        "change",
        "customization",
        "character model",
        "revert",
    ),
    "keyword_technical_issue": (
        "bug",
        "bugs",
        "glitch",
        "glitches",
        "broken",
        "crash",
        "crashes",
        "lag",
        "laggy",
        "stutter",
        "stuttery",
        "unplayable",
        "softlocked",
        "motion sickness",
        "animation lock",
        "janky",
        "sluggish",
    ),
    "keyword_positive": (
        "great",
        "fun",
        "love",
        "awesome",
        "good",
        "amazing",
        "enjoy",
        "best",
        "scary",
        "worth",
        "recommend",
    ),
    "keyword_negative": (
        "ruined",
        "hate",
        "sad",
        "disappointed",
        "terrible",
        "awful",
        "broken",
        "regret",
        "boring",
        "bad",
        "worst",
        "annoying",
        "frustrating",
    ),
    "keyword_nostalgia": (
        "used to love",
        "used to enjoy",
        "used to be fun",
        "miss the old",
        "ruined the game",
        "they killed",
        "great until",
        "before the update",
        "bring back",
        "downhill",
        "no longer recommend",
        "old phasmo",
        "old version",
    ),
}


def clean_review_text(text: object) -> str:
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"Posted:\s*.*?(?:\n|$)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"EARLY ACCESS REVIEW", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Product refunded", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def normalized_text_key(text: object) -> str:
    return clean_review_text(text).casefold()


def _phrase_pattern(phrase: str) -> str:
    escaped = re.escape(phrase).replace(r"\ ", r"\s+")
    return rf"(?<!\w){escaped}(?!\w)"


def contains_any_phrase(text: object, phrases: Iterable[str]) -> bool:
    normalized = clean_review_text(text).casefold()
    return any(
        re.search(_phrase_pattern(phrase.casefold()), normalized) for phrase in phrases
    )


def player_group(hours: float | None) -> str:
    if hours is None or pd.isna(hours):
        return "Unknown"
    hours = float(hours)
    if hours <= 10:
        return "New (≤10h)"
    if hours <= 50:
        return "Casual (10–50h)"
    if hours <= 100:
        return "Regular (50–100h)"
    if hours <= 300:
        return "Veteran (100–300h)"
    return "Hardcore (>300h)"


def suspected_non_latin_script(text: object) -> bool:
    """Conservative flag only; humans make the final language decision."""

    normalized = clean_review_text(text)
    return bool(re.search(r"[\u0400-\u052f\u0600-\u06ff\u4e00-\u9fff]", normalized))


def engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["analysis_review"] = result["review_text"].map(clean_review_text)
    result["word_count"] = result["analysis_review"].map(
        lambda value: len(value.split())
    )
    result["char_count"] = result["analysis_review"].str.len()
    result["playtime_hours"] = pd.to_numeric(result["playtime_hours"], errors="coerce")
    result["playtime_missing"] = result["playtime_hours"].isna()
    result["log_playtime"] = np.log1p(result["playtime_hours"])
    result["player_group"] = result["playtime_hours"].map(player_group)
    result["suspected_non_latin_script"] = result["analysis_review"].map(
        suspected_non_latin_script
    )
    for feature_name, terms in THEME_TERMS.items():
        result[feature_name] = result["analysis_review"].map(
            lambda text, vocabulary=terms: contains_any_phrase(text, vocabulary)
        )
    result["keyword_low_information"] = result["word_count"].le(5)
    return result
