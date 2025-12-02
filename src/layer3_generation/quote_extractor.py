"""
Layer 3: Quote extraction module
Selects representative quotes from reviews using LLM
"""
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class QuoteExtractor:
    """Extracts representative quotes from reviews"""
    
    def __init__(self, api_key: str = None, num_quotes: int = None):
        """
        Initialize quote extractor
        
        Args:
            api_key: Google API key
            num_quotes: Number of quotes to extract
        """
        api_key = api_key or config.GOOGLE_API_KEY
        self.num_quotes = num_quotes or config.MAX_QUOTES
        
        if not api_key:
            raise ValueError("Google API key required for quote extraction")
        
        logger.info("Initializing LLM for quote extraction...")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key,
            temperature=0.2
        )
        
        self.prompt_template = PromptTemplate(
            input_variables=["num_quotes", "reviews"],
            template=config.QUOTE_EXTRACTION_PROMPT
        )
        
    def extract_quotes(self, reviews: List[str], num_quotes: int = None) -> List[str]:
        """
        Extract representative quotes from list of reviews
        
        Args:
            reviews: List of review texts
            num_quotes: Number of quotes to extract (uses default if not provided)
            
        Returns:
            List of selected quotes
        """
        num_quotes = num_quotes or self.num_quotes
        
        # Format reviews for prompt
        reviews_text = "\n".join([f"{i+1}. {review}" for i, review in enumerate(reviews[:50])])
        
        # Create prompt
        prompt = self.prompt_template.format(
            num_quotes=num_quotes,
            reviews=reviews_text
        )
        
        try:
            response = self.llm.invoke(prompt)
            quotes_text = response.content.strip()
            
            # Parse quotes (assuming one per line)
            quotes = [q.strip().lstrip('-').lstrip('•').lstrip('*').strip() 
                     for q in quotes_text.split('\n') if q.strip()]
            
            # Take only requested number
            quotes = quotes[:num_quotes]
            
            logger.info(f"Extracted {len(quotes)} quotes")
            return quotes
            
        except Exception as e:
            logger.error(f"Error extracting quotes: {e}")
            # Fallback: return first few reviews
            return [reviews[i][:200] + "..." for i in range(min(num_quotes, len(reviews)))]
    
    def extract_quotes_by_theme(self, df: pd.DataFrame, content_column: str = 'content') -> Dict[str, List[str]]:
        """
        Extract quotes for each theme
        
        Args:
            df: DataFrame with theme_name column
            content_column: Name of content column
            
        Returns:
            Dictionary mapping theme names to lists of quotes
        """
        logger.info("Extracting quotes for each theme...")
        
        theme_quotes = {}
        themes = df[df['theme_name'] != 'Miscellaneous']['theme_name'].unique()
        
        for theme in themes:
            logger.info(f"Extracting quotes for theme: {theme}")
            theme_reviews = df[df['theme_name'] == theme][content_column].tolist()
            
            # Extract 1-2 quotes per theme
            quotes = self.extract_quotes(theme_reviews, num_quotes=2)
            theme_quotes[theme] = quotes
        
        return theme_quotes
    
    def extract_top_quotes(self, df: pd.DataFrame, content_column: str = 'content', num_quotes: int = None) -> List[str]:
        """
        Extract top quotes across all themes
        
        Args:
            df: DataFrame with reviews
            content_column: Name of content column
            num_quotes: Number of quotes to extract
            
        Returns:
            List of top quotes
        """
        num_quotes = num_quotes or self.num_quotes
        
        logger.info(f"Extracting top {num_quotes} quotes across all themes...")
        
        # Get reviews from top themes (exclude Miscellaneous)
        top_reviews = df[df['theme_name'] != 'Miscellaneous'][content_column].tolist()
        
        quotes = self.extract_quotes(top_reviews, num_quotes)
        
        return quotes


def extract_quotes_from_csv(csv_path: str, output_path: str, num_quotes: int = 3):
    """
    Extract quotes from themed reviews CSV
    
    Args:
        csv_path: Path to themed reviews CSV
        output_path: Path to save quotes JSON
        num_quotes: Number of quotes to extract
    """
    import json
    
    logger.info(f"Loading themed reviews from {csv_path}")
    df = pd.read_csv(csv_path)
    
    extractor = QuoteExtractor(num_quotes=num_quotes)
    
    # Extract top quotes
    top_quotes = extractor.extract_top_quotes(df, num_quotes=num_quotes)
    
    # Extract quotes by theme
    theme_quotes = extractor.extract_quotes_by_theme(df)
    
    # Save to JSON
    quotes_data = {
        'top_quotes': top_quotes,
        'theme_quotes': theme_quotes
    }
    
    with open(output_path, 'w') as f:
        json.dump(quotes_data, f, indent=2)
    
    logger.info(f"Saved quotes to {output_path}")
    
    print(f"\nTop {num_quotes} Quotes:")
    for i, quote in enumerate(top_quotes, 1):
        print(f"{i}. {quote}")
    
    return quotes_data


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python quote_extractor.py <themed_csv> <output_json> [num_quotes]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    num_quotes = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    extract_quotes_from_csv(input_file, output_file, num_quotes)
