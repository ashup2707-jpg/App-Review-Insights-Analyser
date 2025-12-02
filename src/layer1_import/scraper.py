"""
Layer 1: Google Play Store scraper for IND Money reviews

This implementation now uses the `google-play-scraper` library instead of
Playwright/HTML parsing, which is brittle against DOM changes.

It fetches public reviews directly from Google's endpoints (no login),
filters to the last N weeks, and returns clean structured data.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

from google_play_scraper import reviews as gp_reviews, Sort
import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class PlaywrightScraper:
    """
    Scrapes Google Play Store reviews for the configured APP_ID using
    the `google-play-scraper` Python package.
    """
    
    def __init__(self, app_url: str, weeks_back: int = 12):
        """
        Initialize scraper
        
        Args:
            app_url: Google Play Store app URL
            weeks_back: Number of weeks to go back for reviews
        """
        self.app_url = app_url
        self.app_id = config.APP_ID
        self.weeks_back = weeks_back
        self.cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
        self.reviews = []
        
    async def scrape_reviews(self, max_scrolls: int = 100, target_count: int = 150) -> List[Dict]:
        """
        Scrape reviews from Google Play Store using google-play-scraper.

        Args:
            max_scrolls: Ignored (kept for backwards compatibility)
            target_count: Target number of reviews to collect (soft limit)

        Returns:
            List of dictionaries containing review data:
            review_id, content, score, date, thumbs_up_count
        """
        logger.info(f"Starting scrape for app_id={self.app_id} using google-play-scraper")
        logger.info(f"Collecting reviews from last {self.weeks_back} weeks (since {self.cutoff_date.date()})")

        all_reviews: List[Dict] = []
        continuation_token = None
        stop = False

        # google_play_scraper returns reviews sorted by newest first,
        # so we can stop once we hit reviews older than the cutoff_date.
        while not stop:
            batch, continuation_token = gp_reviews(
                self.app_id,
                lang="en",
                country="in",
                sort=Sort.NEWEST,
                count=100,
                continuation_token=continuation_token,
            )

            if not batch:
                logger.info("No more reviews returned from google-play-scraper.")
                break

            for r in batch:
                review_date = r.get("at")
                if isinstance(review_date, datetime):
                    if review_date < self.cutoff_date:
                        # We've gone past our time window; stop fetching
                        stop = True
                        break
                else:
                    # If date missing/invalid, keep but don't use for stopping logic
                    review_date = datetime.now()

                review = {
                    "review_id": r.get("reviewId"),
                    "content": (r.get("content") or "").strip(),
                    "score": int(r.get("score") or 0),
                    "date": review_date,
                    "thumbs_up_count": int(r.get("thumbsUpCount") or 0),
                }

                # Basic guard: skip empty-content reviews
                if review["content"]:
                    all_reviews.append(review)

                if len(all_reviews) >= target_count:
                    stop = True
                    break

            logger.info(f"Collected {len(all_reviews)} reviews so far...")

            if continuation_token is None:
                logger.info("No continuation token returned; reached end of available reviews.")
                break

        self.reviews = all_reviews
        logger.info(f"Successfully scraped {len(self.reviews)} reviews within date range using google-play-scraper")
        return self.reviews
    
    # The old HTML-parsing helpers are no longer needed now that we use
    # google-play-scraper, but `_is_within_date_range` is kept for clarity.

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string to datetime object
        
        Args:
            date_str: Date string from review
            
        Returns:
            datetime object
        """
        if not date_str:
            return datetime.now()
        
        try:
            # Handle relative dates like "2 days ago", "1 week ago"
            if 'ago' in date_str.lower():
                if 'day' in date_str:
                    days = int(date_str.split()[0])
                    return datetime.now() - timedelta(days=days)
                elif 'week' in date_str:
                    weeks = int(date_str.split()[0])
                    return datetime.now() - timedelta(weeks=weeks)
                elif 'month' in date_str:
                    months = int(date_str.split()[0])
                    return datetime.now() - timedelta(days=months*30)
            
            # Handle absolute dates like "November 15, 2024" or "15 November 2024"
            try:
                return datetime.strptime(date_str, "%B %d, %Y")
            except ValueError:
                return datetime.strptime(date_str, "%d %B %Y")
        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return datetime.now()
    
    def _is_within_date_range(self, review_date: datetime) -> bool:
        """Check if review date is within the specified range"""
        return review_date >= self.cutoff_date
    
    def save_to_csv(self, output_path: str):
        """
        Save reviews to CSV file
        
        Args:
            output_path: Path to output CSV file
        """
        if not self.reviews:
            logger.warning("No reviews to save")
            return
        
        df = pd.DataFrame(self.reviews)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(self.reviews)} reviews to {output_path}")


async def main():
    """Main function for testing scraper"""
    scraper = PlaywrightScraper(config.APP_URL, config.WEEKS_BACK)
    reviews = await scraper.scrape_reviews(max_scrolls=30)
    
    # Save to output directory
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(config.OUTPUT_DIR, f"reviews_raw_{datetime.now().strftime('%Y%m%d')}.csv")
    scraper.save_to_csv(output_file)
    
    print(f"\nScraping complete!")
    print(f"Total reviews collected: {len(reviews)}")
    print(f"Output file: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
