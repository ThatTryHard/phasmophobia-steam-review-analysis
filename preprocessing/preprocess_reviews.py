import pandas as pd
import numpy as np
import re


# =========================
# LOAD DATA
# =========================

INPUT_PATH = "data/raw/phasmophobia_reviews_raw.csv"

OUTPUT_PATH = "data/processed/phasmophobia_reviews_processed.csv"

df = pd.read_csv(INPUT_PATH)


# =========================
# TEXT CLEANING
# =========================

def clean_review_text(text):

    if not isinstance(text, str):
        return ""

    # Remove "Posted: ..."
    text = re.sub(
        r'Posted:\s*.*?\n',
        '',
        text,
        flags=re.IGNORECASE
    )

    # Remove EARLY ACCESS REVIEW
    text = re.sub(
        r'EARLY ACCESS REVIEW',
        '',
        text,
        flags=re.IGNORECASE
    )

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


df['cleaned_review'] = df['review_text'].apply(
    clean_review_text
)


# =========================
# HELPFUL / FUNNY PARSING
# =========================

def extract_helpful_count(text):

    if not isinstance(text, str):
        return 0

    if "No one" in text:
        return 0

    match = re.search(
        r'(\d+)\s*people? found this review helpful',
        text
    )

    if match:
        return int(match.group(1))

    return 0


def extract_funny_count(text):

    if not isinstance(text, str):
        return 0

    # Usually last number in helpful_text
    numbers = re.findall(r'\d+', text)

    if len(numbers) >= 2:
        return int(numbers[-1])

    return 0


df['helpful_count'] = df['helpful_text'].apply(
    extract_helpful_count
)

df['funny_count'] = df['helpful_text'].apply(
    extract_funny_count
)


# =========================
# BASIC NLP FEATURES
# =========================

df['word_count'] = df['cleaned_review'].apply(
    lambda x: len(str(x).split())
)

df['char_count'] = df['cleaned_review'].apply(
    lambda x: len(str(x))
)


# =========================
# KEYWORD FEATURES
# =========================

UPDATE_KEYWORDS = [
    'update',
    'patch',
    'customization',
    'rework',
    'changed',
    'animation',
    'character'
]

BUG_KEYWORDS = [
    'bug',
    'glitch',
    'broken',
    'janky',
    'sluggish',
    'crash',
    'unplayable',
    'lag'
]

EMOTIONAL_KEYWORDS = [
    'love',
    'hate',
    'ruined',
    'fun',
    'sad',
    'disappointed',
    'great',
    'amazing',
    'miss'
]


def contains_keywords(text, keywords):

    text = str(text).lower()

    return any(
        keyword in text
        for keyword in keywords
    )


df['contains_update_keyword'] = df[
    'cleaned_review'
].apply(
    lambda x: contains_keywords(
        x,
        UPDATE_KEYWORDS
    )
)

df['contains_bug_keyword'] = df[
    'cleaned_review'
].apply(
    lambda x: contains_keywords(
        x,
        BUG_KEYWORDS
    )
)

df['contains_emotional_keyword'] = df[
    'cleaned_review'
].apply(
    lambda x: contains_keywords(
        x,
        EMOTIONAL_KEYWORDS
    )
)


# =========================
# PLAYER SEGMENTATION
# =========================

df['is_veteran'] = df['playtime_hours'] > 100

df['playtime_segment'] = pd.cut(

    df['playtime_hours'],

    bins=[0, 10, 50, 100, 300, np.inf],

    labels=[
        'New',
        'Casual',
        'Regular',
        'Veteran',
        'Hardcore'
    ]
)


# =========================
# EXPORT
# =========================

df.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nPreprocessing Complete.")
print(f"Processed file saved to:\n{OUTPUT_PATH}")

print("\nDataset Shape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())