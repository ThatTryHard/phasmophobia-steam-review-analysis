from playwright.sync_api import sync_playwright
import pandas as pd
import time
import re
from utils import extract_playtime, safe_locator_text

def scrape_steam_reviews(
    app_id,
    game_title,
    total_pages=5,
    scroll_per_page=3
):

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        all_reviews = []

        seen_reviews = set()

        for p_num in range(1, total_pages + 1):

            print(f"\nScraping Page {p_num}...")

            url = (
                f"https://steamcommunity.com/app/"
                f"{app_id}/reviews/?browsefilter=mostrecent&paged={p_num}"
            )

            page.goto(url)

            page.wait_for_timeout(3000)

            # Scroll multiple times
            for _ in range(scroll_per_page):

                page.mouse.wheel(0, 2500)

                time.sleep(2)

            reviews = page.locator('.apphub_Card').all()

            print(f"Detected {len(reviews)} reviews.")

            for r in reviews:

                review_text = safe_locator_text(
                    r.locator('.apphub_CardTextContent')
                )

                # Skip duplicate reviews
                if review_text in seen_reviews:
                    continue

                seen_reviews.add(review_text)

                recommendation = safe_locator_text(
                    r.locator('.title')
                )

                playtime_raw = safe_locator_text(
                    r.locator('.hours')
                )

                review_date = safe_locator_text(
                    r.locator('.date_posted')
                )

                helpful_text = safe_locator_text(
                    r.locator('.found_helpful')
                )

                author_name = safe_locator_text(
                    r.locator('.apphub_CardContentAuthorName')
                )

                playtime_hours = extract_playtime(
                    playtime_raw
                )

                review_length = len(review_text)

                all_reviews.append({

                    "game_title": game_title,

                    "author_name": author_name,

                    "review_date": review_date,

                    "recommendation": recommendation,

                    "playtime_raw": playtime_raw,

                    "playtime_hours": playtime_hours,

                    "review_length": review_length,

                    "helpful_text": helpful_text,

                    "review_text": review_text

                })

            # Cooling down
            time.sleep(2)

        browser.close()

        return pd.DataFrame(all_reviews)


if __name__ == "__main__":

    df = scrape_steam_reviews(

        app_id="739630",
        game_title="Phasmophobia",

        total_pages=5,

        scroll_per_page=3

    )

    print("\nDataset Preview:")
    print(df.head())

    print(f"\nTotal Reviews Collected: {len(df)}")

    df.to_csv(

        "data/raw/phasmophobia_reviews_raw.csv",

        index=False
    )

    print("\nRaw dataset saved successfully.")