"""
Layer 2: LLM-based theme labeler using LangChain
Generates human-readable theme names for clusters
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


class ThemeLabeler:
    """Generates theme labels for review clusters using LLM"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize LLM for theme labeling
        
        Args:
            api_key: Google API key (uses config if not provided)
        """
        api_key = api_key or config.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("Google API key not provided. Set GOOGLE_API_KEY in .env file")
        
        logger.info("Initializing LLM for theme labeling...")
        self.llm = ChatGoogleGenerativeAI(
            model=config.LLM_MODEL,
            google_api_key=api_key,
            temperature=0.3  # Lower temperature for more consistent labeling
        )
        
        self.prompt_template = PromptTemplate(
            input_variables=["categories", "reviews"],
            template=config.THEME_LABELING_PROMPT
        )
        
    def label_cluster(self, sample_reviews: List[str], suggested_categories: List[str] = None) -> str:
        """
        Generate hierarchical theme label for a cluster
        
        Args:
            sample_reviews: List of sample review texts from cluster
            suggested_categories: Optional list of suggested category names
            
        Returns:
            Theme label string (Category > Sub-category)
        """
        categories = suggested_categories or config.THEME_CATEGORIES
        
        # Format reviews for prompt
        reviews_text = "\n".join([f"- {review[:200]}" for review in sample_reviews[:10]])
        
        # Create prompt
        prompt = self.prompt_template.format(
            categories=", ".join(categories),
            reviews=reviews_text
        )
        
        # Get LLM response
        try:
            response = self.llm.invoke(prompt)
            theme_label = response.content.strip()
            # Clean up if LLM adds extra text
            if "\n" in theme_label:
                theme_label = theme_label.split("\n")[0]
            logger.info(f"Generated theme label: {theme_label}")
            return theme_label
        except Exception as e:
            logger.error(f"Error generating theme label: {e}")
            return "Uncategorized > General"
    
    def label_all_clusters(self, df: pd.DataFrame, content_column: str = 'content', n_samples: int = 10) -> Dict[int, str]:
        """
        Generate labels for all clusters in DataFrame
        
        Args:
            df: DataFrame with cluster_label column
            content_column: Name of content column
            n_samples: Number of sample reviews per cluster
            
        Returns:
            Dictionary mapping cluster labels to theme names
        """
        logger.info("Generating theme labels for all clusters...")
        
        cluster_themes = {}
        unique_clusters = df[df['cluster_label'] != -1]['cluster_label'].unique()
        
        for cluster_id in sorted(unique_clusters):
            logger.info(f"Processing cluster {cluster_id}...")
            
            # Get sample reviews from cluster
            cluster_df = df[df['cluster_label'] == cluster_id]
            
            # Sort by probability if available
            if 'cluster_probability' in cluster_df.columns:
                cluster_df = cluster_df.sort_values('cluster_probability', ascending=False)
            
            sample_reviews = cluster_df[content_column].head(n_samples).tolist()
            
            # Generate theme label
            theme_label = self.label_cluster(sample_reviews)
            cluster_themes[cluster_id] = theme_label
        
        # Handle noise points
        if -1 in df['cluster_label'].values:
            cluster_themes[-1] = "Miscellaneous"
        
        logger.info(f"Generated {len(cluster_themes)} theme labels")
        return cluster_themes
    
    def assign_themes_to_dataframe(self, df: pd.DataFrame, cluster_themes: Dict[int, str]) -> pd.DataFrame:
        """
        Assign theme names to DataFrame
        
        Args:
            df: DataFrame with cluster_label column
            cluster_themes: Dictionary mapping cluster IDs to theme names
            
        Returns:
            DataFrame with theme_name column
        """
        df_with_themes = df.copy()
        df_with_themes['theme_name'] = df_with_themes['cluster_label'].map(cluster_themes)
        
        return df_with_themes


def label_themes(csv_path: str, output_path: str, content_column: str = 'content'):
    """
    Label themes in clustered reviews CSV
    
    Args:
        csv_path: Path to clustered reviews CSV
        output_path: Path to save themed reviews
        content_column: Name of content column
    """
    logger.info(f"Loading clustered reviews from {csv_path}")
    df = pd.read_csv(csv_path)
    
    labeler = ThemeLabeler()
    cluster_themes = labeler.label_all_clusters(df, content_column)
    df_themed = labeler.assign_themes_to_dataframe(df, cluster_themes)
    
    df_themed.to_csv(output_path, index=False)
    logger.info(f"Saved themed reviews to {output_path}")
    
    print(f"\nTheme Labels:")
    for cluster_id, theme in cluster_themes.items():
        count = len(df_themed[df_themed['cluster_label'] == cluster_id])
        print(f"  Cluster {cluster_id}: {theme} ({count} reviews)")
    
    return df_themed, cluster_themes


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python theme_labeler.py <clustered_csv> <output_csv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    label_themes(input_file, output_file)
