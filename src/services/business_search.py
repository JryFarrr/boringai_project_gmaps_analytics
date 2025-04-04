"""
Module for searching businesses based on parameters (Codebase)
"""

from services.places_api import text_search, get_place_details
from utils.business_matcher import (
    match_price_range, 
    check_business_hours, 
    search_reviews_for_keywords, 
    calculate_match_percentage
)
from config.config import MAX_DETAILED_PLACES


def search_businesses(parameters, api_key=None):
    """
    Search for businesses using Google Places API based on the parameters
    
    Args:
        parameters (dict): Search parameters extracted from the prompt
        api_key (str, optional): Google API key
        
    Returns:
        list: List of businesses matching the criteria
    """
    # First, perform a Text Search to get initial results
    places_found = text_search(parameters['business_type'], parameters['location'], api_key)
    
    # Filter results based on rating and review count
    filtered_places = []
    for place in places_found:
        if 'rating' not in place or 'user_ratings_total' not in place:
            continue
            
        if (place['rating'] >= parameters['min_rating'] and 
            place['user_ratings_total'] >= parameters['min_reviews']):
            filtered_places.append(place)
    
    # Get detailed information for each place
    detailed_places = []
    for place in filtered_places[:MAX_DETAILED_PLACES]:  # Limit to avoid excessive API calls
        place_details = get_place_details(place['place_id'], api_key)
        
        # Check price level if required
        if parameters['price_range'] and 'price_level' in place_details:
            price_symbols = '$' * place_details['price_level']
            if not match_price_range(price_symbols, parameters['price_range']):
                continue
        
        # Check business hours if required
        if parameters['business_hours'] and parameters['business_hours'] != 'anytime':
            if not check_business_hours(place_details, parameters['business_hours']):
                continue
        
        # Check for keywords in reviews if specified
        if parameters['keywords']:
            place_details['keyword_matches'] = search_reviews_for_keywords(
                place_details, parameters['keywords']
            )
            
            # Skip if no keyword matches found (optional, based on requirements)
            # if not place_details['keyword_matches']:
            #     continue
        
        # Add match percentages
        place_details['match_percentage'] = calculate_match_percentage(place_details, parameters)
        
        detailed_places.append(place_details)
    
    # Sort by match percentage
    return sorted(detailed_places, key=lambda x: x.get('match_percentage', 0), reverse=True)