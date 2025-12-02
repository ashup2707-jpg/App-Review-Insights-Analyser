"""
Simple Google Play scraper for INDmoney reviews.

Goal:
- Fetch ~15–20 latest real reviews (text + rating + date + thumbs_up_count)
  from the public Google Play page for INDmoney:
  https://play.google.com/store/apps/details?id=in.indwealth&hl=en_IN

Usage (from project root):
    python3 -m src.layer1_import.gplay_simple_scraper --count 20 --weeks-back 12

This writes a clean CSV into the configured OUTPUT_DIR so you can
inspect the raw reviews without going through the full pipeline.
"""

import argparse
from datetime import datetime, timedelta
from typing import List, Dict
import os
import sys

import pandas as pd
from google_play_scraper import reviews as gp_reviews, Sort

# Add project root to path for config / utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger  # type: ignore
import config  # type: ignore


logger = setup_logger(__name__)


def fetch_latest_reviews(
    app_id: str,
    weeks_back: int = 12,
    count: int = 20,
) -> List[Dict]:
    """
    Fetch latest Google Play reviews for the given app_id.

    Returns a list of dicts with:
      - review_id
      - content
      - score
      - date
      - thumbs_up_count
    """
    cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
    logger.info(
        f"Fetching up to {count} reviews for app_id={app_id}, "
        f"from last {weeks_back} weeks (since {cutoff_date.date()})"
    )

    all_reviews: List[Dict] = []
    continuation_token = None
    stop = False

    while not stop and len(all_reviews) < count:
        batch, continuation_token = gp_reviews(
            app_id,
            lang="en",
            country="in",
            sort=Sort.NEWEST,
            count=min(100, count - len(all_reviews)),
            continuation_token=continuation_token,
        )

        if not batch:
            logger.info("No more reviews returned from google-play-scraper.")
            break

        for r in batch:
            review_date = r.get("at")
            if isinstance(review_date, datetime) and review_date < cutoff_date:
                stop = True
                break

            review = {
                "review_id": r.get("reviewId"),
                "content": (r.get("content") or "").strip(),
                "score": int(r.get("score") or 0),
                "date": review_date if isinstance(review_date, datetime) else None,
                "thumbs_up_count": int(r.get("thumbsUpCount") or 0),
            }

            if review["content"]:
                all_reviews.append(review)

            if len(all_reviews) >= count:
                stop = True
                break

        if continuation_token is None:
            logger.info("No continuation token returned; reached end of available reviews.")
            break

    logger.info(f"Fetched {len(all_reviews)} reviews with non-empty content.")
    return all_reviews


def main():
    parser = argparse.ArgumentParser(description="Simple INDmoney Google Play scraper")
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of reviews to fetch (approximate upper bound)",
    )
    parser.add_argument(
        "--weeks-back",
        type=int,
        default=12,
        help="How many weeks back to include reviews from",
    )
    args = parser.parse_args()

    app_id = config.APP_ID
    output_dir = config.OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    reviews = fetch_latest_reviews(app_id, weeks_back=args.weeks_back, count=args.count)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"reviews_raw_simple_{timestamp}.csv")

    if not reviews:
        logger.warning("No reviews fetched – CSV will not be created.")
        print("No reviews fetched. Check logs for details.")
        return

    df = pd.DataFrame(reviews)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} reviews to {output_path}")
    print(f"Saved {len(df)} reviews to {output_path}")


if __name__ == "__main__":
    main()


