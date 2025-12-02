"""
Layer 1: Playwright-based scraper for Google Play Store reviews
Scrapes IND Money app reviews without authentication
"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class PlaywrightScraper:
    """Scrapes Google Play Store reviews using Playwright"""
    
    def __init__(self, app_url: str, weeks_back: int = 12):
        """
        Initialize scraper
        
        Args:
            app_url: Google Play Store app URL
            weeks_back: Number of weeks to go back for reviews
        """
        self.app_url = app_url
        self.weeks_back = weeks_back
        self.cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
        self.reviews = []
        
    async def scrape_reviews(self, max_scrolls: int = 20) -> List[Dict]:
        """
        Scrape reviews from Google Play Store
        
        Args:
            max_scrolls: Maximum number of scroll attempts to load more reviews
            
        Returns:
            List of review dictionaries
        """
        logger.info(f"Starting scrape for {self.app_url}")
        logger.info(f"Collecting reviews from last {self.weeks_back} weeks (since {self.cutoff_date.date()})")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                # Navigate to app page
                logger.info("Navigating to Google Play Store...")
                await page.goto(self.app_url, wait_until='networkidle', timeout=60000)
                await asyncio.sleep(3)
                
                # Click on "See all reviews" button if present
                try:
                    see_all_button = page.locator('button:has-text("See all reviews")')
                    if await see_all_button.count() > 0:
                        await see_all_button.first.click()
                        await asyncio.sleep(2)
                        logger.info("Clicked 'See all reviews' button")
                except Exception as e:
                    logger.warning(f"Could not click 'See all reviews': {e}")
                
                # Scroll to load reviews
                logger.info(f"Scrolling to load reviews (max {max_scrolls} scrolls)...")
                for i in range(max_scrolls):
                    # Scroll down
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(2)
                    
                    # Check if we've loaded enough reviews
                    review_count = await page.locator('[data-review-id]').count()
                    logger.info(f"Scroll {i+1}/{max_scrolls}: Loaded {review_count} reviews")
                    
                    # Stop if no new reviews are loading
                    if i > 5 and review_count < (i * 10):
                        logger.info("No more reviews loading, stopping scroll")
                        break
                
                # Extract reviews from page
                logger.info("Extracting review data...")
                html_content = await page.content()
                self.reviews = self._parse_reviews(html_content)
                
                logger.info(f"Successfully scraped {len(self.reviews)} reviews")
                
            except Exception as e:
                logger.error(f"Error during scraping: {e}")
                raise
            finally:
                await browser.close()
        
        return self.reviews
    
    def _parse_reviews(self, html_content: str) -> List[Dict]:
        """
        Parse reviews from HTML content
        
        Args:
            html_content: HTML content from page
            
        Returns:
            List of parsed review dictionaries
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        reviews = []
        
        # Find all review containers
        review_elements = soup.find_all(attrs={'data-review-id': True})
        logger.info(f"Found {len(review_elements)} review elements")
        
        for elem in review_elements:
            try:
                review = self._extract_review_data(elem)
                if review and self._is_within_date_range(review['date']):
                    reviews.append(review)
            except Exception as e:
                logger.warning(f"Error parsing review: {e}")
                continue
        
        logger.info(f"Extracted {len(reviews)} reviews within date range")
        return reviews
    
    def _extract_review_data(self, element) -> Dict:
        """
        Extract review data from a review element
        
        Args:
            element: BeautifulSoup element containing review
            
        Returns:
            Dictionary with review data
        """
        # Extract review ID
        review_id = element.get('data-review-id', '')
        
        # Extract rating (star rating)
        rating_elem = element.find(attrs={'role': 'img'})
        rating = 0
        if rating_elem and 'aria-label' in rating_elem.attrs:
            aria_label = rating_elem['aria-label']
            if 'Rated' in aria_label:
                try:
                    rating = int(aria_label.split()[1])
                except:
                    rating = 0
        
        # Extract review text
        content_elem = element.find('div', {'class': lambda x: x and 'review-text' in str(x).lower()})
        if not content_elem:
            # Try alternative selectors
            content_elem = element.find('div', {'jsname': True})
        content = content_elem.get_text(strip=True) if content_elem else ""
        
        # Extract date
        date_elem = element.find('span', {'class': lambda x: x and 'review-date' in str(x).lower()})
        if not date_elem:
            # Try finding by text pattern
            date_elem = element.find('span', string=lambda x: x and any(month in str(x) for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']))
        
        date_str = date_elem.get_text(strip=True) if date_elem else ""
        review_date = self._parse_date(date_str)
        
        # Extract thumbs up count
        thumbs_up = 0
        thumbs_elem = element.find('div', string=lambda x: x and 'people found this review helpful' in str(x).lower())
        if thumbs_elem:
            try:
                thumbs_up = int(thumbs_elem.get_text().split()[0])
            except:
                thumbs_up = 0
        
        return {
            'review_id': review_id,
            'content': content,
            'score': rating,
            'date': review_date,
            'thumbs_up_count': thumbs_up
        }
    
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
            
            # Handle absolute dates like "November 15, 2024"
            return datetime.strptime(date_str, "%B %d, %Y")
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
