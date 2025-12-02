"""
Configuration settings for IND Money Review Analyzer
"""
import os
from dotenv import load_dotenv

load_dotenv()

# App Configuration
APP_ID = os.getenv('APP_ID', 'in.indwealth')
APP_URL = f"https://play.google.com/store/apps/details?id={APP_ID}&hl=en_IN"
WEEKS_BACK = int(os.getenv('WEEKS_BACK', 12))
LLM_MODEL = "gemini-2.0-flash"

# API Keys
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Email Configuration
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))

# Output Paths
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
DEMO_DIR = 'demo'

# Theme Configuration
THEME_CATEGORIES = [
    "Features & Functionality",
    "App Updates & Performance",
    "Transactions & Payments",
    "Customer Service & Support",
    "Product Marketing & Communication"
]

MAX_THEMES = 5

# HDBSCAN Parameters
MIN_CLUSTER_SIZE = 5
MIN_SAMPLES = 3

# Content Generation Parameters
MAX_QUOTES = 3
MAX_ACTION_ITEMS = 3
MAX_WORD_COUNT = 250

# LLM Prompts
THEME_LABELING_PROMPT = """
You are analyzing customer reviews for a financial app called IND Money.
Below are sample reviews from a cluster. Generate a concise, human-readable theme name (2-4 words) that captures the main topic.

Suggested categories: {categories}

Reviews:
{reviews}

Theme name:
"""

QUOTE_EXTRACTION_PROMPT = """
From the following reviews, select the {num_quotes} most representative and impactful quotes that illustrate user sentiment.
Choose quotes that are:
1. Clear and specific
2. Represent different perspectives
3. Actionable for product teams

Reviews:
{reviews}

Return only the selected quotes, one per line.
"""

ACTION_GENERATION_PROMPT = """
Based on the following review themes and quotes, generate {num_actions} specific, actionable recommendations for the product team.

Themes:
{themes}

Quotes:
{quotes}

Each action should be:
1. Specific and measurable
2. Prioritized by impact
3. Feasible to implement

Return only the action items, one per line.
"""

SUMMARIZATION_PROMPT = """
Summarize the following reviews for the theme "{theme}" in 1-2 concise sentences.
Focus on the key patterns and user sentiment.

Reviews:
{reviews}

Summary:
"""
