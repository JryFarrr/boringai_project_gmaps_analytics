"""
SEARCH_API client implementation
"""

import os
import requests
from src.config.config import SEARCHAPI_API_KEY

def create_search_api_client(api_key=None, base_url=None):
    """
    Create a SEARCH_API client
    
    Args:
        api_key (str): API key (defaults to SEARCH_API_KEY from config)
        base_url (str): Base URL for the API (defaults to SEARCH_API_BASE_URL from config)
        
    Returns:
        tuple: (client, headers)
    """
    # Use provided API key or fall back to environment/config
    if not api_key:
        api_key = SEARCHAPI_API_KEY or os.getenv("SEARCHAPI_KEY")
    
    # Create headers for API requests
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Simple client object with methods to interact with the API
    class SearchApiClient:
        def __init__(self, base_url, headers):
            self.base_url = base_url
            self.headers = headers
            
        def get_place_details(self, place_id):
            """Get details for a specific place"""
            url = f"{self.base_url}/places/{place_id}"
            response = requests.get(url, headers=self.headers)
            return response.json()
            
        def get_place_reviews(self, place_id, max_reviews=10):
            """Get reviews for a specific place"""
            url = f"{self.base_url}/places/{place_id}/reviews"
            params = {"limit": max_reviews}
            response = requests.get(url, headers=self.headers, params=params)
            data = response.json()
            
            # Process reviews into positive and negative
            reviews = data.get("reviews", [])
            total_reviews = data.get("total", len(reviews))
            
            positive_reviews = []
            negative_reviews = []
            
            for review in reviews:
                review_text = review.get("text", "").strip()
                rating = review.get("rating", 0)
                
                if not review_text:
                    continue
                    
                if rating >= 4:  # Consider 4+ as positive
                    positive_reviews.append(review_text)
                elif rating <= 2:  # Consider 2 or less as negative
                    negative_reviews.append(review_text)
            
            return positive_reviews, negative_reviews, total_reviews
            
        def search_places(self, query, location, **kwargs):
            """Search for places"""
            url = f"{self.base_url}/places/search"
            params = {
                "query": query,
                "location": location,
                **kwargs
            }
            response = requests.get(url, headers=self.headers, params=params)
            return response.json()
    
    client = SearchApiClient(base_url, headers)
    
    return client, headers