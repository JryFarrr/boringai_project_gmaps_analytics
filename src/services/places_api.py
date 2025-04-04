"""
Module for interacting with Google Places API (Codebase)
"""

import requests
import time
from config.config import GOOGLE_API_KEY, MAX_SEARCH_PAGES


def text_search(business_type, location, api_key=GOOGLE_API_KEY):
    """
    Perform text search with Google Places API
    
    Args:
        business_type (str): Type of business to search for
        location (str): Location to search in
        api_key (str): Google API key
        
    Returns:
        list: List of places found
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    # Combine business type and location for search
    query = f"{business_type} in {location}"
    
    params = {
        "query": query,
        "key": api_key
    }
    
    response = requests.get(url, params=params)
    result = response.json()
    
    if result['status'] != 'OK':
        print(f"Error in text search: {result.get('status')}")
        if 'error_message' in result:
            print(f"Error message: {result['error_message']}")
        return []
    
    # Check for next page token to get more results if needed
    places = result.get('results', [])
    next_page_token = result.get('next_page_token')
    
    # Get a few more pages of results if available
    pages_fetched = 1
    
    while next_page_token and pages_fetched < MAX_SEARCH_PAGES:
        # Google requires a delay before using the next_page_token
        time.sleep(2)
        
        params = {
            "pagetoken": next_page_token,
            "key": api_key
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if result['status'] == 'OK':
            places.extend(result.get('results', []))
            next_page_token = result.get('next_page_token')
            pages_fetched += 1
        else:
            break
            
    return places


def get_place_details(place_id, api_key=GOOGLE_API_KEY):
    """
    Get detailed information about a place using its place_id
    
    Args:
        place_id (str): Google Place ID
        api_key (str): Google API key
        
    Returns:
        dict: Place details
    """
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    
    params = {
        "place_id": place_id,
        "fields": "name,place_id,formatted_address,geometry,rating,user_ratings_total,reviews,price_level,opening_hours,website,formatted_phone_number,types",
        "language": "en",  # Set language to ensure consistent parsing
        "key": api_key
    }
    
    response = requests.get(url, params=params)
    result = response.json()
    
    if result['status'] != 'OK':
        print(f"Error in place details: {result.get('status')}")
        if 'error_message' in result:
            print(f"Error message: {result['error_message']}")
        return {}
    
    return result.get('result', {})