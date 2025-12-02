"""
Layer 2: HDBSCAN clustering for theme extraction
Clusters review embeddings into natural groups
"""
import numpy as np
import pandas as pd
import hdbscan
from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class HDBSCANClustering:
    """Clusters review embeddings using HDBSCAN algorithm"""
    
    def __init__(self, min_cluster_size: int = None, min_samples: int = None):
        """
        Initialize HDBSCAN clusterer
        
        Args:
            min_cluster_size: Minimum size of clusters
            min_samples: Minimum samples in neighborhood
        """
        self.min_cluster_size = min_cluster_size or config.MIN_CLUSTER_SIZE
        self.min_samples = min_samples or config.MIN_SAMPLES
        self.clusterer = None
        self.labels = None
        self.probabilities = None
        
    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Fit HDBSCAN and predict cluster labels
        
        Args:
            embeddings: NumPy array of embeddings
            
        Returns:
            Array of cluster labels (-1 for noise)
        """
        logger.info(f"Clustering {len(embeddings)} embeddings with HDBSCAN...")
        logger.info(f"Parameters: min_cluster_size={self.min_cluster_size}, min_samples={self.min_samples}")
        
        self.clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric='euclidean',
            cluster_selection_method='eom'  # Excess of Mass
        )
        
        self.labels = self.clusterer.fit_predict(embeddings)
        self.probabilities = self.clusterer.probabilities_
        
        # Get cluster statistics
        unique_labels = set(self.labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = list(self.labels).count(-1)
        
        logger.info(f"Clustering complete: Found {n_clusters} clusters, {n_noise} noise points")
        
        return self.labels
    
    def get_cluster_info(self) -> Dict:
        """
        Get information about clusters
        
        Returns:
            Dictionary with cluster statistics
        """
        if self.labels is None:
            return {}
        
        unique_labels = set(self.labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = list(self.labels).count(-1)
        
        cluster_sizes = {}
        for label in unique_labels:
            if label != -1:
                cluster_sizes[f"cluster_{label}"] = list(self.labels).count(label)
        
        return {
            'n_clusters': n_clusters,
            'n_noise': n_noise,
            'cluster_sizes': cluster_sizes,
            'total_points': len(self.labels)
        }
    
    def assign_to_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assign cluster labels to DataFrame
        
        Args:
            df: DataFrame to add cluster labels to
            
        Returns:
            DataFrame with cluster_label column
        """
        if self.labels is None:
            raise ValueError("Must call fit_predict first")
        
        df_with_clusters = df.copy()
        df_with_clusters['cluster_label'] = self.labels
        df_with_clusters['cluster_probability'] = self.probabilities
        
        return df_with_clusters
    
    def get_cluster_samples(self, df: pd.DataFrame, cluster_label: int, n_samples: int = 5) -> pd.DataFrame:
        """
        Get sample reviews from a specific cluster
        
        Args:
            df: DataFrame with cluster labels
            cluster_label: Cluster to sample from
            n_samples: Number of samples to return
            
        Returns:
            DataFrame with sample reviews
        """
        cluster_df = df[df['cluster_label'] == cluster_label]
        
        # Sort by probability (most representative first)
        cluster_df = cluster_df.sort_values('cluster_probability', ascending=False)
        
        return cluster_df.head(n_samples)


def cluster_reviews(embeddings_path: str, csv_path: str, output_path: str):
    """
    Cluster reviews and save results
    
    Args:
        embeddings_path: Path to embeddings file
        csv_path: Path to reviews CSV
        output_path: Path to save clustered reviews
    """
    # Load embeddings
    logger.info(f"Loading embeddings from {embeddings_path}")
    import pickle
    with open(embeddings_path, 'rb') as f:
        embeddings = pickle.load(f)
    
    # Load reviews
    logger.info(f"Loading reviews from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Cluster
    clusterer = HDBSCANClustering()
    labels = clusterer.fit_predict(embeddings)
    
    # Assign to DataFrame
    df_clustered = clusterer.assign_to_dataframe(df)
    
    # Save
    df_clustered.to_csv(output_path, index=False)
    logger.info(f"Saved clustered reviews to {output_path}")
    
    # Print statistics
    info = clusterer.get_cluster_info()
    print(f"\nClustering Statistics:")
    print(f"Total reviews: {info['total_points']}")
    print(f"Number of clusters: {info['n_clusters']}")
    print(f"Noise points: {info['n_noise']}")
    print(f"\nCluster sizes:")
    for cluster, size in info['cluster_sizes'].items():
        print(f"  {cluster}: {size} reviews")
    
    return df_clustered, info


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python clustering.py <embeddings_file> <reviews_csv> <output_csv>")
        sys.exit(1)
    
    embeddings_file = sys.argv[1]
    reviews_file = sys.argv[2]
    output_file = sys.argv[3]
    
    cluster_reviews(embeddings_file, reviews_file, output_file)
