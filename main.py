"""
Main orchestrator for IND Money Review Analyzer
Runs the complete 4-layer pipeline
"""
import asyncio
import os
import sys
from datetime import datetime
import argparse

# Add src to path
sys.path.append(os.path.dirname(__file__))

from utils.logger import setup_logger
import config

# Layer 1 imports
from src.layer1_import.scraper import PlaywrightScraper
from src.layer1_import.validator import SchemaValidator
from src.layer1_import.pii_detector import PIIDetector
from src.layer1_import.deduplicator import Deduplicator

# Layer 2 imports
from src.layer2_themes.embeddings import EmbeddingGenerator
from src.layer2_themes.clustering import HDBSCANClustering
from src.layer2_themes.theme_labeler import ThemeLabeler
from src.layer2_themes.theme_enforcer import ThemeEnforcer

# Layer 3 imports
from src.layer3_generation.quote_extractor import QuoteExtractor
from src.layer3_generation.action_generator import ActionGenerator
from src.layer3_generation.pulse_assembler import PulseAssembler

# Layer 4 imports
from src.layer4_distribution.email_drafter import EmailDrafter

logger = setup_logger(__name__, log_file=os.path.join(config.OUTPUT_DIR, 'pipeline.log'))


class ReviewAnalyzerPipeline:
    """Complete 4-layer pipeline for review analysis"""
    
    def __init__(self, output_dir: str = None):
        """Initialize pipeline"""
        self.output_dir = output_dir or config.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    async def run_layer1(self) -> str:
        """Run Layer 1: Data Import & Validation"""
        logger.info("="*60)
        logger.info("LAYER 1: DATA IMPORT & VALIDATION")
        logger.info("="*60)
        
        # Step 1: Scrape reviews
        logger.info("Step 1/4: Scraping reviews...")
        scraper = PlaywrightScraper(config.APP_URL, config.WEEKS_BACK)
        await scraper.scrape_reviews(max_scrolls=30)
        
        raw_csv = os.path.join(self.output_dir, f'reviews_raw_{self.timestamp}.csv')
        scraper.save_to_csv(raw_csv)
        
        # Step 2: Validate schema
        logger.info("Step 2/4: Validating schema...")
        validator = SchemaValidator()
        import pandas as pd
        df = pd.read_csv(raw_csv)
        validated_df, errors = validator.validate_dataframe(df)
        validated_df = validator.filter_by_date_range(validated_df, config.WEEKS_BACK)
        
        validated_csv = os.path.join(self.output_dir, f'reviews_validated_{self.timestamp}.csv')
        validated_df.to_csv(validated_csv, index=False)
        
        # Step 3: Detect and remove PII
        logger.info("Step 3/4: Detecting and anonymizing PII...")
        pii_detector = PIIDetector()
        anonymized_df = pii_detector.process_dataframe(validated_df)
        
        anonymized_csv = os.path.join(self.output_dir, f'reviews_anonymized_{self.timestamp}.csv')
        anonymized_df.to_csv(anonymized_csv, index=False)
        
        # Step 4: Deduplicate
        logger.info("Step 4/4: Deduplicating reviews...")
        deduplicator = Deduplicator()
        final_df = deduplicator.deduplicate_dataframe(anonymized_df)
        
        final_csv = os.path.join(self.output_dir, f'reviews_clean_{self.timestamp}.csv')
        final_df.to_csv(final_csv, index=False)
        
        logger.info(f"Layer 1 complete: {len(final_df)} clean reviews")
        return final_csv
    
    def run_layer2(self, reviews_csv: str) -> str:
        """Run Layer 2: Theme Extraction & Classification"""
        logger.info("="*60)
        logger.info("LAYER 2: THEME EXTRACTION & CLASSIFICATION")
        logger.info("="*60)
        
        import pandas as pd
        import pickle
        
        # Step 1: Generate embeddings
        logger.info("Step 1/4: Generating embeddings...")
        embedding_gen = EmbeddingGenerator()
        df = pd.read_csv(reviews_csv)
        embeddings = embedding_gen.process_dataframe(df)
        
        embeddings_file = os.path.join(self.output_dir, f'embeddings_{self.timestamp}.pkl')
        with open(embeddings_file, 'wb') as f:
            pickle.dump(embeddings, f)
        
        # Step 2: Cluster with HDBSCAN
        logger.info("Step 2/4: Clustering reviews...")
        clusterer = HDBSCANClustering()
        labels = clusterer.fit_predict(embeddings)
        df_clustered = clusterer.assign_to_dataframe(df)
        
        clustered_csv = os.path.join(self.output_dir, f'reviews_clustered_{self.timestamp}.csv')
        df_clustered.to_csv(clustered_csv, index=False)
        
        # Step 3: Label themes
        logger.info("Step 3/4: Labeling themes...")
        labeler = ThemeLabeler()
        cluster_themes = labeler.label_all_clusters(df_clustered)
        df_themed = labeler.assign_themes_to_dataframe(df_clustered, cluster_themes)
        
        themed_csv = os.path.join(self.output_dir, f'reviews_themed_{self.timestamp}.csv')
        df_themed.to_csv(themed_csv, index=False)
        
        # Step 4: Enforce theme limit
        logger.info("Step 4/4: Enforcing theme limit...")
        enforcer = ThemeEnforcer()
        df_final, final_themes = enforcer.enforce_theme_limit(df_themed, cluster_themes)
        
        final_csv = os.path.join(self.output_dir, f'reviews_final_{self.timestamp}.csv')
        df_final.to_csv(final_csv, index=False)
        
        logger.info(f"Layer 2 complete: {len(set(final_themes.values()))} themes")
        return final_csv
    
    def run_layer3(self, themed_csv: str) -> str:
        """Run Layer 3: Content Generation"""
        logger.info("="*60)
        logger.info("LAYER 3: CONTENT GENERATION")
        logger.info("="*60)
        
        import pandas as pd
        import json
        
        df = pd.read_csv(themed_csv)
        
        # Step 1: Extract quotes
        logger.info("Step 1/3: Extracting quotes...")
        quote_extractor = QuoteExtractor()
        quotes = quote_extractor.extract_top_quotes(df, num_quotes=3)
        
        # Step 2: Generate actions
        logger.info("Step 2/3: Generating action items...")
        themes = df['theme_name'].value_counts().head(5).index.tolist()
        action_gen = ActionGenerator()
        actions = action_gen.generate_actions(themes, quotes, num_actions=3)
        
        # Step 3: Assemble pulse
        logger.info("Step 3/3: Assembling weekly pulse...")
        theme_counts = df['theme_name'].value_counts().to_dict()
        assembler = PulseAssembler()
        pulse = assembler.assemble_pulse(themes, theme_counts, quotes, actions)
        
        pulse_md = os.path.join(self.output_dir, f'weekly_pulse_{self.timestamp}.md')
        assembler.save_pulse(pulse, pulse_md)
        
        logger.info("Layer 3 complete: Weekly pulse generated")
        return pulse_md
    
    def run_layer4(self, pulse_md: str):
        """Run Layer 4: Distribution"""
        logger.info("="*60)
        logger.info("LAYER 4: DISTRIBUTION")
        logger.info("="*60)
        
        # Draft email
        logger.info("Drafting email...")
        with open(pulse_md, 'r') as f:
            pulse_content = f.read()
        
        drafter = EmailDrafter()
        email = drafter.draft_email(pulse_content)
        
        email_txt = os.path.join(self.output_dir, f'email_draft_{self.timestamp}.txt')
        drafter.save_draft(email, email_txt)
        
        logger.info("Layer 4 complete: Email draft created")
        return email_txt
    
    async def run_full_pipeline(self):
        """Run complete 4-layer pipeline"""
        logger.info("\n" + "="*60)
        logger.info("IND MONEY REVIEW ANALYZER - FULL PIPELINE")
        logger.info("="*60 + "\n")
        
        start_time = datetime.now()
        
        try:
            # Layer 1
            reviews_csv = await self.run_layer1()
            
            # Layer 2
            themed_csv = self.run_layer2(reviews_csv)
            
            # Layer 3
            pulse_md = self.run_layer3(themed_csv)
            
            # Layer 4
            email_txt = self.run_layer4(pulse_md)
            
            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("\n" + "="*60)
            logger.info("PIPELINE COMPLETE!")
            logger.info("="*60)
            logger.info(f"Duration: {duration:.1f} seconds")
            logger.info(f"Output directory: {self.output_dir}")
            logger.info(f"\nKey outputs:")
            logger.info(f"  - Weekly Pulse: {pulse_md}")
            logger.info(f"  - Email Draft: {email_txt}")
            logger.info(f"  - Themed Reviews: {themed_csv}")
            
            print(f"\n✅ Pipeline complete! Check {self.output_dir} for outputs.")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='IND Money Review Analyzer')
    parser.add_argument('--output-dir', default=config.OUTPUT_DIR, help='Output directory')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode with limited data')
    
    args = parser.parse_args()
    
    pipeline = ReviewAnalyzerPipeline(output_dir=args.output_dir)
    await pipeline.run_full_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
