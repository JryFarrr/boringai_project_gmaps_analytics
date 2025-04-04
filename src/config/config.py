"""
Configuration module for API keys and settings
"""

# API Keys
GOOGLE_API_KEY = "AIzaSyAw0cQAr5B_o-XI1iI7mPJRV88U0J6BTX0"
OPENROUTER_API_KEY = "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"

# Default settings
DEFAULT_REFERER_URL = "https://your-website.com"
DEFAULT_SITE_NAME = "Map Leads AI"

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

OPENAI_API_KEY="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"
DEFAULT_API_PROVIDER = "openai"  # Can be "openai" or "openrouter"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-4o-mini"