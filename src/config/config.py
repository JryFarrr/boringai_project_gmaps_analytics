"""
Configuration module for API keys and settings
"""

from dotenv import load_dotenv
import os

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEARCHAPI_API_KEY = os.getenv("SEARCHAPI_API_KEY")

# Default settings
DEFAULT_REFERER_URL = os.getenv("DEFAULT_REFERER_URL")
DEFAULT_SITE_NAME = os.getenv("DEFAULT_SITE_NAME")

# Default search parameters
DEFAULT_SEARCH_PARAMS = {
    'business_type': "",
    'location': "",
    'min_rating': 0.0,
    'min_reviews': 0,
    'price_range': "",
    'business_hours': "anytime",
    'keywords': ""
}

# Match criteria weights
MATCH_WEIGHTS = {
    'rating': 0.25,
    'reviews': 0.20,
    'price': 0.15,
    'keywords': 0.40
}

# Maximum number of places to process in detail
MAX_DETAILED_PLACES = 20

# Maximum number of pages to fetch in text search
MAX_SEARCH_PAGES = 3

DEFAULT_API_PROVIDER = os.getenv("DEFAULT_API_PROVIDER")
DEFAULT_OPENAI_MODEL = os.getenv("DEFAULT_OPENAI_MODEL")
DEFAULT_OPENROUTER_MODEL = os.getenv("DEFAULT_OPENROUTER_MODEL")