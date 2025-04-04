"""
Module for matching businesses to search criteria (Codebase)
"""

import re
from datetime import datetime
import math
from config.config import MATCH_WEIGHTS


def match_price_range(price_symbols, required_price_range):
    """
    Check if the price level matches the required price range
    
    Args:
        price_symbols (str): Price level symbols (e.g., '$', '$$')
        required_price_range (str): Required price range from search parameters
    
    Returns:
        bool: True if match, False otherwise
    """
    # If no price range requirement, consider it a match
    if not required_price_range:
        return True
        
    # Handle 'rupiah + $$' format
    if 'rupiah' in required_price_range.lower():
        # Extract the $ symbols part
        match = re.search(r'rupiah\s*\+\s*(\$+)', required_price_range)
        if match:
            required_symbols = match.group(1)
            return price_symbols == required_symbols
    
    # Direct comparison for simple cases
    return price_symbols in required_price_range


def check_business_hours(place_details, required_hours):
    """
    Check if the business hours match the required hours
    
    Args:
        place_details (dict): Place details containing opening hours
        required_hours (str): Required hours from search parameters
    
    Returns:
        bool: True if match, False otherwise
    """
    if not required_hours or required_hours.lower() == 'anytime':
        return True
        
    if 'opening_hours' not in place_details:
        return False
        
    # Check for "open now"
    if required_hours.lower() == 'open now' and place_details['opening_hours'].get('open_now', False):
        return True
        
    # Check for "open 24 hours"
    if required_hours.lower() == 'open 24 hours':
        if 'weekday_text' in place_details['opening_hours']:
            for day_hours in place_details['opening_hours']['weekday_text']:
                if '24 hours' in day_hours.lower():
                    return True
        return False
        
    # For "open at [specific time]"
    if required_hours.lower().startswith('open at'):
        time_str = required_hours.lower().replace('open at', '').strip()
        if 'weekday_text' in place_details['opening_hours']:
            current_day = datetime.now().strftime('%A')
            for day_hours in place_details['opening_hours']['weekday_text']:
                if current_day.lower() in day_hours.lower():
                    # Basic check if the time falls within opening hours
                    if time_str in day_hours.lower():
                        return True
        return False
        
    return False  # If we can't determine, default to not matching


def search_reviews_for_keywords(place_details, keywords):
    """
    Search reviews for specific keywords
    
    Args:
        place_details (dict): Place details containing reviews
        keywords (str): Comma-separated list of keywords to search for
        
    Returns:
        list: List of found keywords and their frequency
    """
    if 'reviews' not in place_details:
        return []
        
    keyword_list = [kw.strip().lower() for kw in keywords.split(',')]
    keyword_counts = {kw: 0 for kw in keyword_list}
    
    # Search in reviews
    for review in place_details.get('reviews', []):
        review_text = review.get('text', '').lower()
        
        for keyword in keyword_list:
            if keyword in review_text:
                keyword_counts[keyword] += 1
    
    # Search in business name
    if 'name' in place_details:
        business_text = place_details['name'].lower()
        for keyword in keyword_list:
            if keyword in business_text:
                keyword_counts[keyword] += 2  # Weight more heavily for name matches
    
    # Search in business types
    if 'types' in place_details:
        for business_type in place_details['types']:
            business_type = business_type.lower().replace('_', ' ')
            for keyword in keyword_list:
                if keyword in business_type:
                    keyword_counts[keyword] += 1
                
    # Format results with count
    matches = [f"{kw} ({count})" for kw, count in keyword_counts.items() if count > 0]
    return matches


def calculate_match_percentage(place, parameters):
    """
    Calculate how well a place matches the search parameters
    
    Args:
        place (dict): Place details
        parameters (dict): Search parameters
    
    Returns:
        float: Match percentage (0-100)
    """
    # Use weights from config
    weights = MATCH_WEIGHTS
    
    score = 0
    
    # Rating match (from min_rating to 5.0)
    if 'rating' in place:
        rating_range = 5.0 - parameters['min_rating']
        if rating_range > 0:
            rating_score = min(1.0, (place['rating'] - parameters['min_rating']) / rating_range)
            score += weights['rating'] * rating_score
        else:
            score += weights['rating']  # If min_rating is 5.0, give full score if matched
    
    # Review count match (logarithmic scale since review counts vary widely)
    if 'user_ratings_total' in place:
        min_reviews = parameters['min_reviews']
        if min_reviews > 0:
            review_score = min(1.0, math.log10(place['user_ratings_total'] / min_reviews + 1) / math.log10(11))  # log10(11) ≈ 1.04
            score += weights['reviews'] * review_score
        else:
            score += weights['reviews']
    
    # Price match (exact match gets full score)
    if parameters['price_range'] and 'price_level' in place:
        price_symbols = '$' * place['price_level']
        if match_price_range(price_symbols, parameters['price_range']):
            score += weights['price']
    elif not parameters['price_range']:
        # If no price range specified, give full score
        score += weights['price']
    
    # Keyword matches
    if parameters['keywords'] and 'keyword_matches' in place and place['keyword_matches']:
        keyword_list = [kw.strip().lower() for kw in parameters['keywords'].split(',')]
        if keyword_list:
            # Count actual keywords found (not occurrences)
            found_keywords = set()
            for kw_match in place['keyword_matches']:
                keyword = kw_match.split(' (')[0].lower()
                found_keywords.add(keyword)
            
            match_ratio = len(found_keywords) / len(keyword_list)
            score += weights['keywords'] * match_ratio
    elif not parameters['keywords']:
        # If no keywords specified, give full score
        score += weights['keywords']
    
    return round(score * 100, 2)  # Convert to percentage


def calculate_rating_match_percentage(business, all_businesses):
    """
    Calculate rating match percentage compared to other businesses
    
    Args:
        business (dict): Business details
        all_businesses (list): List of all businesses
    
    Returns:
        float: Rating match percentage (0-100)
    """
    if 'rating' not in business or not all_businesses:
        return 0
        
    # Get min and max ratings across all businesses
    ratings = [b.get('rating', 0) for b in all_businesses if 'rating' in b]
    if not ratings:
        return 0
        
    min_rating = min(ratings)
    max_rating = max(ratings)
    
    # Normalize the rating
    if max_rating == min_rating:
        return 100  # All businesses have the same rating
        
    normalized = (business['rating'] - min_rating) / (max_rating - min_rating) * 100
    return round(normalized, 2)


def calculate_address_match_percentage(business, all_businesses):
    """
    Simple implementation to return match percentage
    
    Args:
        business (dict): Business details
        all_businesses (list): List of all businesses
    
    Returns:
        float: Address match percentage (0-100)
    """
    # Simply return the overall match as address match for now
    return business.get('match_percentage', 0)


def calculate_price_match_percentage(business, all_businesses):
    """
    Simple implementation to return match percentage
    
    Args:
        business (dict): Business details
        all_businesses (list): List of all businesses
    
    Returns:
        float: Price match percentage (0-100)
    """
    # Simply return the overall match as price match for now
    return business.get('match_percentage', 0)