"""
Layer 2: Sentiment Analysis
Analyzes sentiment of reviews using LLM
"""
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from typing import List, Dict
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class SentimentAnalyzer:
    """Analyzes sentiment of reviews"""
    
    def __init__(self, api_key: str = None):
        """Initialize sentiment analyzer"""
        api_key = api_key or config.GOOGLE_API_KEY
        self.llm = ChatGoogleGenerativeAI(
            model=config.LLM_MODEL,
            google_api_key=api_key,
            temperature=0.1  # Low temperature for consistent classification
        )
        
        self.prompt_template = PromptTemplate(
            input_variables=["reviews"],
            template=config.SENTIMENT_ANALYSIS_PROMPT
        )
        
    def analyze_sentiment_batch(self, reviews: List[str]) -> List[Dict]:
        """
        Analyze sentiment for a batch of reviews
        
        Args:
            reviews: List of review texts
            
        Returns:
            List of dicts with 'sentiment' (Positive/Negative/Neutral) and 'score' (0-10)
        """
        # Format reviews for prompt
        reviews_text = "\n".join([f"{i+1}. {review[:200]}" for i, review in enumerate(reviews)])
        
        prompt = self.prompt_template.format(reviews=reviews_text)
        
        try:
            response = self.llm.invoke(prompt)
            result_text = response.content.strip()
            
            # Parse JSON response
            # Expected format: [{"id": 1, "sentiment": "Negative", "score": 2}, ...]
            # Clean up markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
                
            results = json.loads(result_text)
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            # Fallback
            return [{"sentiment": "Neutral", "score": 5} for _ in reviews]

    def process_dataframe(self, df: pd.DataFrame, content_column: str = 'content', batch_size: int = 10) -> pd.DataFrame:
        """
        Add sentiment analysis to DataFrame
        
        Args:
            df: DataFrame with reviews
            content_column: Content column name
            batch_size: Number of reviews to process at once
            
        Returns:
            DataFrame with sentiment columns
        """
        logger.info(f"Analyzing sentiment for {len(df)} reviews...")
        
        sentiments = []
        scores = []
        
        reviews = df[content_column].tolist()
        
        for i in range(0, len(reviews), batch_size):
            batch = reviews[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(reviews)-1)//batch_size + 1}")
            
            results = self.analyze_sentiment_batch(batch)
            
            # Ensure we have a result for each review in batch
            if len(results) != len(batch):
                logger.warning(f"Batch size mismatch: got {len(results)}, expected {len(batch)}")
                # Pad with neutral
                results.extend([{"sentiment": "Neutral", "score": 5}] * (len(batch) - len(results)))
            
            for res in results:
                sentiments.append(res.get('sentiment', 'Neutral'))
                scores.append(res.get('score', 5))
                
        df_result = df.copy()
        df_result['sentiment'] = sentiments
        df_result['sentiment_score'] = scores
        
        return df_result


def analyze_reviews_sentiment(csv_path: str, output_path: str):
    """Run sentiment analysis on reviews CSV"""
    logger.info(f"Loading reviews from {csv_path}")
    df = pd.read_csv(csv_path)
    
    analyzer = SentimentAnalyzer()
    df_analyzed = analyzer.process_dataframe(df)
    
    df_analyzed.to_csv(output_path, index=False)
    logger.info(f"Saved sentiment analysis to {output_path}")
    
    # Print stats
    print("\nSentiment Distribution:")
    print(df_analyzed['sentiment'].value_counts())
    
    return df_analyzed


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python sentiment.py <input_csv> <output_csv>")
        sys.exit(1)
        
    analyze_reviews_sentiment(sys.argv[1], sys.argv[2])
