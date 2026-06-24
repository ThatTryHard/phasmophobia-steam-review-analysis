from pathlib import Path
from datetime import datetime
import time
import urllib.parse

import pandas as pd
import requests


# ==========================
# CONFIGURATION
# ==========================

GAME_TITLE = "Phasmophobia"
APP_ID = "739630"

TARGET_TOTAL_REVIEWS = 300
REVIEWS_PER_REQUEST = 100
SLEEP_SECONDS = 1.5

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

EXPANDED_RAW_PATH = RAW_DIR / "phasmophobia_reviews_expanded_raw.csv"


# ==========================
# HELPER FUNCTIONS
# ==========================

def timestamp_to_date(timestamp_value):
    try:
        return datetime.fromtimestamp(int(timestamp_value)).strftime("%Y-%m-%d")
    except Exception:
        return ""


def minutes_to_hours(minutes_value):
    try:
        return round(float(minutes_value) / 60, 1)
    except Exception:
        return 0.0


def normalize_recommendation(voted_up):
    return "Recommended" if bool(voted_up) else "Not Recommended"


def load_existing_dataset(path):
    if path.exists():
        df = pd.read_csv(path)

        if "recommendation_id" not in df.columns:
            df["recommendation_id"] = ""

        return df

    return pd.DataFrame()


def get_existing_ids(df):
    if df.empty or "recommendation_id" not in df.columns:
        return set()

    return set(
        df["recommendation_id"]
        .dropna()
        .astype(str)
        .tolist()
    )


def fetch_review_batch(app_id, cursor):
    encoded_cursor = urllib.parse.quote(cursor)

    url = (
        f"https://store.steampowered.com/appreviews/{app_id}"
        f"?json=1"
        f"&filter=recent"
        f"&language=english"
        f"&review_type=all"
        f"&purchase_type=all"
        f"&num_per_page={REVIEWS_PER_REQUEST}"
        f"&cursor={encoded_cursor}"
    )

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        }
    )

    response.raise_for_status()
    return response.json()


def parse_review(raw_review):
    author = raw_review.get("author", {})

    playtime_minutes = (
        author.get("playtime_at_review")
        or author.get("playtime_forever")
        or 0
    )

    playtime_hours = minutes_to_hours(playtime_minutes)

    return {
        "game_title": GAME_TITLE,
        "author_name": "",
        "author_steamid": author.get("steamid", ""),
        "recommendation_id": str(raw_review.get("recommendationid", "")),
        "review_date": timestamp_to_date(raw_review.get("timestamp_created", "")),
        "recommendation": normalize_recommendation(raw_review.get("voted_up", False)),
        "playtime_raw": f"{playtime_hours} hrs on record",
        "playtime_hours": playtime_hours,
        "helpful_text": "",
        "helpful_count": int(raw_review.get("votes_up", 0) or 0),
        "funny_count": int(raw_review.get("votes_funny", 0) or 0),
        "review_text": raw_review.get("review", ""),
        "language": raw_review.get("language", ""),
        "steam_purchase": raw_review.get("steam_purchase", ""),
        "received_for_free": raw_review.get("received_for_free", ""),
        "written_during_early_access": raw_review.get("written_during_early_access", ""),
        "weighted_vote_score": raw_review.get("weighted_vote_score", ""),
        "comment_count": raw_review.get("comment_count", "")
    }


# ==========================
# MAIN SCRIPT
# ==========================

def main():
    existing_df = load_existing_dataset(EXPANDED_RAW_PATH)
    existing_ids = get_existing_ids(existing_df)

    print(f"Existing rows: {len(existing_df)}")
    print(f"Existing recommendation IDs: {len(existing_ids)}")

    cursor = "*"
    seen_cursors = set()
    new_rows = []

    while True:
        if len(existing_df) + len(new_rows) >= TARGET_TOTAL_REVIEWS:
            break

        if cursor in seen_cursors:
            print("Cursor repeated. Stopping to avoid infinite loop.")
            break

        seen_cursors.add(cursor)

        print(f"\nFetching batch with cursor: {cursor[:60]}...")

        data = fetch_review_batch(APP_ID, cursor)
        reviews = data.get("reviews", [])

        if not reviews:
            print("No more reviews returned.")
            break

        added_this_batch = 0

        for raw_review in reviews:
            parsed = parse_review(raw_review)
            recommendation_id = parsed["recommendation_id"]

            if recommendation_id and recommendation_id in existing_ids:
                continue

            if not str(parsed["review_text"]).strip():
                continue

            existing_ids.add(recommendation_id)
            new_rows.append(parsed)
            added_this_batch += 1

            if len(existing_df) + len(new_rows) >= TARGET_TOTAL_REVIEWS:
                break

        print(f"Reviews returned: {len(reviews)}")
        print(f"New unique reviews added this batch: {added_this_batch}")
        print(f"Total after this batch: {len(existing_df) + len(new_rows)}")

        cursor = data.get("cursor", "")

        if not cursor:
            print("No next cursor returned.")
            break

        time.sleep(SLEEP_SECONDS)

    new_df = pd.DataFrame(new_rows)

    if existing_df.empty:
        final_df = new_df
    else:
        final_df = pd.concat([existing_df, new_df], ignore_index=True)

    if "recommendation_id" in final_df.columns:
        final_df = final_df.drop_duplicates(
            subset=["recommendation_id"],
            keep="first"
        )

    final_df = final_df.reset_index(drop=True)

    final_df.to_csv(EXPANDED_RAW_PATH, index=False)

    print("\nDone.")
    print(f"New rows collected: {len(new_df)}")
    print(f"Total rows saved: {len(final_df)}")
    print(f"Saved to: {EXPANDED_RAW_PATH}")


if __name__ == "__main__":
    main()
