"""
Layer 1: Schema validator for review data
Ensures all required fields are present and valid
"""
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

logger = setup_logger(__name__)


class SchemaValidator:
    """Validates review data schema and quality"""
    
    REQUIRED_FIELDS = ['review_id', 'content', 'score', 'date']
    OPTIONAL_FIELDS = ['thumbs_up_count']
    
    def __init__(self):
        self.validation_errors = []
        
    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Validate DataFrame schema and data quality
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (validated DataFrame, list of error messages)
        """
        logger.info(f"Validating {len(df)} reviews...")
        self.validation_errors = []
        
        # Check required fields
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in df.columns]
        if missing_fields:
            error = f"Missing required fields: {missing_fields}"
            logger.error(error)
            self.validation_errors.append(error)
            return df, self.validation_errors
        
        # Validate each row
        valid_rows = []
        for idx, row in df.iterrows():
            if self._validate_row(row, idx):
                valid_rows.append(row)
        
        validated_df = pd.DataFrame(valid_rows)
        
        logger.info(f"Validation complete: {len(validated_df)}/{len(df)} reviews passed")
        if self.validation_errors:
            logger.warning(f"Found {len(self.validation_errors)} validation errors")
        
        return validated_df, self.validation_errors
    
    def _validate_row(self, row: pd.Series, idx: int) -> bool:
        """
        Validate a single row
        
        Args:
            row: Row to validate
            idx: Row index
            
        Returns:
            True if valid, False otherwise
        """
        # Check for empty content
        if pd.isna(row['content']) or str(row['content']).strip() == '':
            self.validation_errors.append(f"Row {idx}: Empty content")
            return False
        
        # Validate score (should be 1-5)
        try:
            score = int(row['score'])
            if score < 1 or score > 5:
                self.validation_errors.append(f"Row {idx}: Invalid score {score} (must be 1-5)")
                return False
        except (ValueError, TypeError):
            self.validation_errors.append(f"Row {idx}: Invalid score format")
            return False
        
        # Validate date
        if pd.isna(row['date']):
            self.validation_errors.append(f"Row {idx}: Missing date")
            return False
        
        # Check content length (too short reviews are likely spam)
        if len(str(row['content'])) < 10:
            self.validation_errors.append(f"Row {idx}: Content too short (likely spam)")
            return False
        
        return True
    
    def filter_by_date_range(self, df: pd.DataFrame, weeks_back: int = 12) -> pd.DataFrame:
        """
        Filter reviews by date range
        
        Args:
            df: DataFrame to filter
            weeks_back: Number of weeks to go back
            
        Returns:
            Filtered DataFrame
        """
        cutoff_date = datetime.now() - pd.Timedelta(weeks=weeks_back)
        
        # Convert date column to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        filtered_df = df[df['date'] >= cutoff_date].copy()
        
        logger.info(f"Filtered to {len(filtered_df)}/{len(df)} reviews from last {weeks_back} weeks")
        return filtered_df


def validate_csv(input_path: str, output_path: str = None, weeks_back: int = 12) -> pd.DataFrame:
    """
    Validate CSV file and optionally save cleaned version
    
    Args:
        input_path: Path to input CSV
        output_path: Optional path to save validated CSV
        weeks_back: Number of weeks for date filtering
        
    Returns:
        Validated DataFrame
    """
    logger.info(f"Loading reviews from {input_path}")
    df = pd.read_csv(input_path)
    
    validator = SchemaValidator()
    validated_df, errors = validator.validate_dataframe(df)
    
    # Filter by date range
    validated_df = validator.filter_by_date_range(validated_df, weeks_back)
    
    if output_path:
        validated_df.to_csv(output_path, index=False)
        logger.info(f"Saved validated reviews to {output_path}")
    
    return validated_df


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python validator.py <input_csv> [output_csv]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    df = validate_csv(input_file, output_file)
    print(f"\nValidation complete: {len(df)} valid reviews")
