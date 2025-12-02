"""
Layer 2: Theme enforcer to limit themes to maximum of 5
Merges similar themes if too many are detected
"""
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Dict, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class ThemeEnforcer:
    """Ensures maximum of 5 themes by merging similar ones"""
    
    def __init__(self, max_themes: int = None, api_key: str = None):
        """
        Initialize theme enforcer
        
        Args:
            max_themes: Maximum number of themes allowed
            api_key: Google API key
        """
        self.max_themes = max_themes or config.MAX_THEMES
        api_key = api_key or config.GOOGLE_API_KEY
        
        if api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=api_key,
                temperature=0.3
            )
        else:
            self.llm = None
            logger.warning("No API key provided, theme merging will use simple heuristics")
        
    def enforce_theme_limit(self, df: pd.DataFrame, cluster_themes: Dict[int, str]) -> Tuple[pd.DataFrame, Dict[int, str]]:
        """
        Enforce maximum theme limit by merging similar themes
        
        Args:
            df: DataFrame with cluster_label and theme_name columns
            cluster_themes: Dictionary mapping cluster IDs to theme names
            
        Returns:
            Tuple of (updated DataFrame, updated cluster_themes dict)
        """
        # Count unique themes (excluding Miscellaneous)
        unique_themes = set(theme for theme in cluster_themes.values() if theme != "Miscellaneous")
        n_themes = len(unique_themes)
        
        logger.info(f"Current number of themes: {n_themes}")
        
        if n_themes <= self.max_themes:
            logger.info(f"Theme count within limit ({self.max_themes}), no merging needed")
            return df, cluster_themes
        
        logger.info(f"Merging themes to reduce from {n_themes} to {self.max_themes}...")
        
        # Get theme sizes
        theme_sizes = self._get_theme_sizes(df)
        
        # Merge smallest themes or similar themes
        merged_themes = self._merge_themes(cluster_themes, theme_sizes)
        
        # Update DataFrame
        updated_df = self._update_dataframe_themes(df, merged_themes)
        
        logger.info(f"Theme merging complete: {len(set(merged_themes.values()))} themes remain")
        
        return updated_df, merged_themes
    
    def _get_theme_sizes(self, df: pd.DataFrame) -> Dict[str, int]:
        """Get count of reviews per theme"""
        theme_counts = df['theme_name'].value_counts().to_dict()
        return theme_counts
    
    def _merge_themes(self, cluster_themes: Dict[int, str], theme_sizes: Dict[str, int]) -> Dict[int, str]:
        """
        Merge themes to meet maximum limit
        
        Args:
            cluster_themes: Original cluster to theme mapping
            theme_sizes: Count of reviews per theme
            
        Returns:
            Updated cluster to theme mapping
        """
        # Sort themes by size (largest first)
        sorted_themes = sorted(theme_sizes.items(), key=lambda x: x[1], reverse=True)
        
        # Keep top N-1 themes, merge rest into "Other"
        keep_themes = set([theme for theme, _ in sorted_themes[:self.max_themes-1]])
        
        # Create new mapping
        merged_mapping = {}
        for cluster_id, theme_name in cluster_themes.items():
            if theme_name in keep_themes or theme_name == "Miscellaneous":
                merged_mapping[cluster_id] = theme_name
            else:
                merged_mapping[cluster_id] = "Other Issues"
        
        return merged_mapping
    
    def _update_dataframe_themes(self, df: pd.DataFrame, merged_themes: Dict[int, str]) -> pd.DataFrame:
        """Update DataFrame with merged theme names"""
        df_updated = df.copy()
        df_updated['theme_name'] = df_updated['cluster_label'].map(merged_themes)
        return df_updated


def enforce_themes(csv_path: str, output_path: str):
    """
    Enforce theme limit on themed reviews CSV
    
    Args:
        csv_path: Path to themed reviews CSV
        output_path: Path to save enforced themes CSV
    """
    logger.info(f"Loading themed reviews from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Reconstruct cluster_themes dict
    cluster_themes = df.groupby('cluster_label')['theme_name'].first().to_dict()
    
    enforcer = ThemeEnforcer()
    df_enforced, enforced_themes = enforcer.enforce_theme_limit(df, cluster_themes)
    
    df_enforced.to_csv(output_path, index=False)
    logger.info(f"Saved enforced themes to {output_path}")
    
    # Print final themes
    final_themes = df_enforced['theme_name'].value_counts()
    print(f"\nFinal Themes ({len(final_themes)}):")
    for theme, count in final_themes.items():
        print(f"  {theme}: {count} reviews")
    
    return df_enforced


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python theme_enforcer.py <themed_csv> <output_csv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    enforce_themes(input_file, output_file)
