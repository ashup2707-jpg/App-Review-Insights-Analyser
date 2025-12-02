"""
Layer 1: PII Detector using Presidio
Detects and redacts personally identifiable information from reviews
"""
import pandas as pd
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

logger = setup_logger(__name__)


class PIIDetector:
    """Detects and anonymizes PII in review content"""
    
    def __init__(self):
        """Initialize Presidio analyzer and anonymizer"""
        logger.info("Initializing PII detector...")
        
        # Configure to use smaller spaCy model
        from presidio_analyzer.nlp_engine import NlpEngineProvider
        
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
        
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        self.anonymizer = AnonymizerEngine()
        
        # PII entities to detect
        self.entities = [
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "CREDIT_CARD",
            "IBAN_CODE",
            "IP_ADDRESS",
            "URL",
            "US_SSN",
            "US_DRIVER_LICENSE"
        ]
        
    def detect_pii(self, text: str) -> List[Dict]:
        """
        Detect PII in text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected PII entities
        """
        results = self.analyzer.analyze(
            text=text,
            entities=self.entities,
            language='en'
        )
        return results
    
    def anonymize_text(self, text: str) -> str:
        """
        Anonymize PII in text
        
        Args:
            text: Text to anonymize
            
        Returns:
            Anonymized text
        """
        if not text or pd.isna(text):
            return text
        
        # Detect PII
        results = self.detect_pii(str(text))
        
        if not results:
            return text
        
        # Anonymize
        anonymized_result = self.anonymizer.anonymize(
            text=str(text),
            analyzer_results=results
        )
        
        return anonymized_result.text
    
    def process_dataframe(self, df: pd.DataFrame, content_column: str = 'content') -> pd.DataFrame:
        """
        Process DataFrame to anonymize PII in content column
        
        Args:
            df: DataFrame to process
            content_column: Name of column containing text content
            
        Returns:
            DataFrame with anonymized content
        """
        logger.info(f"Processing {len(df)} reviews for PII detection...")
        
        pii_count = 0
        anonymized_df = df.copy()
        
        for idx, row in anonymized_df.iterrows():
            original_text = row[content_column]
            anonymized_text = self.anonymize_text(original_text)
            
            if original_text != anonymized_text:
                pii_count += 1
                anonymized_df.at[idx, content_column] = anonymized_text
        
        logger.info(f"PII detection complete: Found and anonymized PII in {pii_count}/{len(df)} reviews")
        
        return anonymized_df


def anonymize_csv(input_path: str, output_path: str, content_column: str = 'content'):
    """
    Anonymize PII in CSV file
    
    Args:
        input_path: Path to input CSV
        output_path: Path to output CSV
        content_column: Name of content column
    """
    logger.info(f"Loading reviews from {input_path}")
    df = pd.read_csv(input_path)
    
    detector = PIIDetector()
    anonymized_df = detector.process_dataframe(df, content_column)
    
    anonymized_df.to_csv(output_path, index=False)
    logger.info(f"Saved anonymized reviews to {output_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python pii_detector.py <input_csv> <output_csv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    anonymize_csv(input_file, output_file)
    print(f"\nAnonymization complete!")
