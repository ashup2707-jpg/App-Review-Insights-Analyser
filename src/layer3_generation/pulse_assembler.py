"""
Layer 3: Pulse document assembler
Creates scannable weekly note with themes, quotes, and actions
"""
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class PulseAssembler:
    """Assembles weekly pulse note from themes, quotes, and actions"""
    
    def __init__(self, max_words: int = None):
        """Initialize pulse assembler"""
        self.max_words = max_words or config.MAX_WORD_COUNT
        
    def assemble_pulse(self, themes: List[str], theme_counts: Dict[str, int], 
                      quotes: List[str], actions: List[str], sentiment_stats: Dict = None) -> str:
        """
        Assemble weekly pulse note
        
        Args:
            themes: List of theme names
            theme_counts: Dictionary of theme counts
            quotes: List of quotes
            actions: List of action items
            sentiment_stats: Optional dictionary with sentiment statistics
            
        Returns:
            Formatted pulse note as markdown string
        """
        logger.info("Assembling weekly pulse note...")
        
        # Get current week info
        week_start = datetime.now().strftime("%B %d, %Y")
        
        # Build pulse note
        pulse = f"# IND Money Weekly Review Pulse\n"
        pulse += f"**Week of {week_start}**\n\n"
        
        # Sentiment Overview (New)
        if sentiment_stats:
            pulse += "## 📈 Sentiment Overview\n\n"
            total = sentiment_stats.get('total', 0)
            if total > 0:
                pos = sentiment_stats.get('Positive', 0)
                neu = sentiment_stats.get('Neutral', 0)
                neg = sentiment_stats.get('Negative', 0)
                pulse += f"- **Positive**: {pos} ({int(pos/total*100)}%)\n"
                pulse += f"- **Neutral**: {neu} ({int(neu/total*100)}%)\n"
                pulse += f"- **Negative**: {neg} ({int(neg/total*100)}%)\n\n"
        
        # Top Themes (Hierarchical)
        pulse += "## 📊 Top Themes & Issues\n\n"

        # Reorder themes so that concrete themes come first and catch-all
        # buckets like 'Miscellaneous' or 'Other Issues' appear last.
        primary_themes = [t for t in themes if t not in ("Miscellaneous", "Other Issues")]
        fallback_themes = [t for t in themes if t in ("Miscellaneous", "Other Issues")]
        ordered_themes = primary_themes + fallback_themes

        for i, theme in enumerate(ordered_themes[:5], 1):
            count = theme_counts.get(theme, 0)
            # Format: Category > Issue
            if " > " in theme:
                category, issue = theme.split(" > ", 1)
                display_theme = f"**{category}**: {issue}"
            else:
                display_theme = f"**{theme}**"
                
            pulse += f"{i}. {display_theme} ({count} reviews)\n"
        pulse += "\n"
        
        # User Quotes
        pulse += "## 💬 What Users Are Saying\n\n"
        for i, quote in enumerate(quotes[:3], 1):
            # Truncate long quotes
            display_quote = quote if len(quote) <= 150 else quote[:147] + "..."
            pulse += f"{i}. \"{display_quote}\"\n"
        pulse += "\n"
        
        # Action Items
        pulse += "## 🎯 Action Items\n\n"
        for i, action in enumerate(actions[:3], 1):
            pulse += f"{i}. {action}\n"
        pulse += "\n"
        
        # Check word count
        word_count = len(pulse.split())
        logger.info(f"Pulse note word count: {word_count}/{self.max_words}")
        
        if word_count > self.max_words:
            logger.warning(f"Pulse exceeds word limit ({word_count} > {self.max_words})")
        
        return pulse
    
    def save_pulse(self, pulse: str, output_path: str):
        """Save pulse note to file"""
        with open(output_path, 'w') as f:
            f.write(pulse)
        logger.info(f"Saved pulse note to {output_path}")


def assemble_weekly_pulse(themes_csv: str, quotes_json: str, actions_json: str, output_md: str):
    """Assemble weekly pulse from all components"""
    
    # Load themes
    df = pd.read_csv(themes_csv)
    theme_counts = df['theme_name'].value_counts().to_dict()
    themes = list(theme_counts.keys())[:5]
    
    # Load quotes
    with open(quotes_json, 'r') as f:
        quotes_data = json.load(f)
    quotes = quotes_data.get('top_quotes', [])
    
    # Load actions
    with open(actions_json, 'r') as f:
        actions_data = json.load(f)
    actions = actions_data.get('actions', [])
    
    # Assemble
    assembler = PulseAssembler()
    pulse = assembler.assemble_pulse(themes, theme_counts, quotes, actions)
    assembler.save_pulse(pulse, output_md)
    
    print("\n" + "="*60)
    print(pulse)
    print("="*60)
    
    return pulse


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python pulse_assembler.py <themes_csv> <quotes_json> <actions_json> <output_md>")
        sys.exit(1)
    
    themes_file = sys.argv[1]
    quotes_file = sys.argv[2]
    actions_file = sys.argv[3]
    output_file = sys.argv[4]
    
    assemble_weekly_pulse(themes_file, quotes_file, actions_file, output_file)
