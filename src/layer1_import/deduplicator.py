"""
Layer 1: Deduplicator for review data
Removes duplicate reviews based on content similarity
"""
import pandas as pd
import hashlib
from typing import Set
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

logger = setup_logger(__name__)


class Deduplicator:
    """Removes duplicate reviews from dataset"""
    
    def __init__(self):
        self.seen_hashes: Set[str] = set()
        self.duplicate_count = 0
        
    def _generate_content_hash(self, text: str) -> str:
        """
        Generate hash of review content
        
        Args:
            text: Review text
            
        Returns:
            MD5 hash of normalized text
        """
        # Normalize text (lowercase, strip whitespace)
        normalized = str(text).lower().strip()
        # Generate hash
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def deduplicate_dataframe(self, df: pd.DataFrame, content_column: str = 'content') -> pd.DataFrame:
        """
        Remove duplicate reviews from DataFrame
        
        Args:
            df: DataFrame to deduplicate
            content_column: Name of column containing review content
            
        Returns:
            Deduplicated DataFrame
        """
        logger.info(f"Deduplicating {len(df)} reviews...")
        
        self.seen_hashes = set()
        self.duplicate_count = 0
        unique_rows = []
        
        for idx, row in df.iterrows():
            content = row[content_column]
            content_hash = self._generate_content_hash(content)
            
            if content_hash not in self.seen_hashes:
                self.seen_hashes.add(content_hash)
                unique_rows.append(row)
            else:
                self.duplicate_count += 1
        
        deduplicated_df = pd.DataFrame(unique_rows)
        
        logger.info(f"Deduplication complete: Removed {self.duplicate_count} duplicates, {len(deduplicated_df)} unique reviews remain")
        
        return deduplicated_df
    
    def get_statistics(self) -> dict:
        """Get deduplication statistics"""
        return {
            'unique_reviews': len(self.seen_hashes),
            'duplicates_removed': self.duplicate_count
        }


def deduplicate_csv(input_path: str, output_path: str, content_column: str = 'content'):
    """
    Deduplicate reviews in CSV file
    
    Args:
        input_path: Path to input CSV
        output_path: Path to output CSV
        content_column: Name of content column
    """
    logger.info(f"Loading reviews from {input_path}")
    df = pd.read_csv(input_path)
    
    deduplicator = Deduplicator()
    deduplicated_df = deduplicator.deduplicate_dataframe(df, content_column)
    
    deduplicated_df.to_csv(output_path, index=False)
    logger.info(f"Saved deduplicated reviews to {output_path}")
    
    stats = deduplicator.get_statistics()
    return stats


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python deduplicator.py <input_csv> <output_csv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    stats = deduplicate_csv(input_file, output_file)
    print(f"\nDeduplication complete!")
    print(f"Unique reviews: {stats['unique_reviews']}")
    print(f"Duplicates removed: {stats['duplicates_removed']}")
