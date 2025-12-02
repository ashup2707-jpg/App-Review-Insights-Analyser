"""
Layer 2: Embedding generation using Sentence Transformers
Converts review text into vector embeddings for clustering
"""
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List
import sys
import os
import pickle

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

logger = setup_logger(__name__)


class EmbeddingGenerator:
    """Generates embeddings for review text using Sentence Transformers"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embedding model
        
        Args:
            model_name: Name of Sentence Transformer model
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        logger.info("Embedding model loaded successfully")
        
    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for list of texts
        
        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
            
        Returns:
            NumPy array of embeddings
        """
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings
    
    def process_dataframe(self, df: pd.DataFrame, content_column: str = 'content') -> np.ndarray:
        """
        Generate embeddings for DataFrame content column
        
        Args:
            df: DataFrame containing reviews
            content_column: Name of column with text content
            
        Returns:
            NumPy array of embeddings
        """
        texts = df[content_column].tolist()
        return self.generate_embeddings(texts)
    
    def save_embeddings(self, embeddings: np.ndarray, output_path: str):
        """
        Save embeddings to file
        
        Args:
            embeddings: NumPy array of embeddings
            output_path: Path to save embeddings
        """
        with open(output_path, 'wb') as f:
            pickle.dump(embeddings, f)
        logger.info(f"Saved embeddings to {output_path}")
    
    def load_embeddings(self, input_path: str) -> np.ndarray:
        """
        Load embeddings from file
        
        Args:
            input_path: Path to embeddings file
            
        Returns:
            NumPy array of embeddings
        """
        with open(input_path, 'rb') as f:
            embeddings = pickle.load(f)
        logger.info(f"Loaded embeddings from {input_path} with shape: {embeddings.shape}")
        return embeddings


def generate_and_save_embeddings(csv_path: str, output_path: str, content_column: str = 'content'):
    """
    Generate embeddings from CSV and save to file
    
    Args:
        csv_path: Path to input CSV file
        output_path: Path to save embeddings
        content_column: Name of content column
    """
    logger.info(f"Loading reviews from {csv_path}")
    df = pd.read_csv(csv_path)
    
    generator = EmbeddingGenerator()
    embeddings = generator.process_dataframe(df, content_column)
    generator.save_embeddings(embeddings, output_path)
    
    return embeddings


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python embeddings.py <input_csv> <output_embeddings>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    embeddings = generate_and_save_embeddings(input_file, output_file)
    print(f"\nEmbedding generation complete!")
    print(f"Shape: {embeddings.shape}")
