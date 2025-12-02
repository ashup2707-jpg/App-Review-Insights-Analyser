"""
Layer 3: Action idea generator using chain-of-thought prompting
Generates actionable recommendations based on review themes
"""
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from typing import List, Dict
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class ActionGenerator:
    """Generates actionable recommendations from review insights"""
    
    def __init__(self, api_key: str = None, num_actions: int = None):
        """Initialize action generator"""
        api_key = api_key or config.GOOGLE_API_KEY
        self.num_actions = num_actions or config.MAX_ACTION_ITEMS
        
        if not api_key:
            raise ValueError("Google API key required")
        
        logger.info("Initializing LLM for action generation...")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key,
            temperature=0.4
        )
        
        self.prompt_template = PromptTemplate(
            input_variables=["num_actions", "themes", "quotes"],
            template=config.ACTION_GENERATION_PROMPT
        )
        
    def generate_actions(self, themes: List[str], quotes: List[str], num_actions: int = None) -> List[str]:
        """
        Generate action items based on themes and quotes
        
        Args:
            themes: List of theme names
            quotes: List of representative quotes
            num_actions: Number of actions to generate
            
        Returns:
            List of action items
        """
        num_actions = num_actions or self.num_actions
        
        # Format themes and quotes
        themes_text = "\n".join([f"- {theme}" for theme in themes])
        quotes_text = "\n".join([f'- "{quote}"' for quote in quotes])
        
        # Create prompt
        prompt = self.prompt_template.format(
            num_actions=num_actions,
            themes=themes_text,
            quotes=quotes_text
        )
        
        try:
            response = self.llm.invoke(prompt)
            actions_text = response.content.strip()
            
            # Parse actions
            actions = [a.strip().lstrip('-').lstrip('•').lstrip('*').lstrip('1234567890.').strip() 
                      for a in actions_text.split('\n') if a.strip()]
            
            actions = actions[:num_actions]
            
            logger.info(f"Generated {len(actions)} action items")
            return actions
            
        except Exception as e:
            logger.error(f"Error generating actions: {e}")
            return ["Review and prioritize user feedback", 
                   "Improve app performance and stability",
                   "Enhance customer support response time"]


def generate_actions_from_data(themes_csv: str, quotes_json: str, output_json: str, num_actions: int = 3):
    """Generate actions from themes and quotes"""
    
    # Load themes
    df = pd.read_csv(themes_csv)
    themes = df['theme_name'].value_counts().head(5).index.tolist()
    
    # Load quotes
    with open(quotes_json, 'r') as f:
        quotes_data = json.load(f)
    quotes = quotes_data.get('top_quotes', [])
    
    # Generate actions
    generator = ActionGenerator(num_actions=num_actions)
    actions = generator.generate_actions(themes, quotes, num_actions)
    
    # Save
    with open(output_json, 'w') as f:
        json.dump({'actions': actions}, f, indent=2)
    
    logger.info(f"Saved actions to {output_json}")
    
    print(f"\nGenerated Action Items:")
    for i, action in enumerate(actions, 1):
        print(f"{i}. {action}")
    
    return actions


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python action_generator.py <themes_csv> <quotes_json> <output_json> [num_actions]")
        sys.exit(1)
    
    themes_file = sys.argv[1]
    quotes_file = sys.argv[2]
    output_file = sys.argv[3]
    num_actions = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    
    generate_actions_from_data(themes_file, quotes_file, output_file, num_actions)
