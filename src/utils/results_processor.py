"""
Module for processing and formatting search results (Codebase)
"""

import pandas as pd
from utils.business_matcher import (
    calculate_rating_match_percentage,
    calculate_address_match_percentage,
    calculate_price_match_percentage
)


def sample_reviews(reviews):
    """
    Sample reviews according to the specified rules
    
    Args:
        reviews (list): List of reviews
    
    Returns:
        str: Formatted review text
    """
    num_reviews = len(reviews)
    
    if num_reviews <= 10:
        # Take all reviews
        sample_size = num_reviews
    elif num_reviews <= 100:
        # Take 40%, minimum 5, maximum 30
        sample_size = min(max(int(0.4 * num_reviews), 5), 30)
    else:
        # Take 20%, minimum 25, maximum 50
        sample_size = min(max(int(0.2 * num_reviews), 25), 50)
        
    # Sort reviews by recency (assuming reviews are sorted by recency already)
    sampled_reviews = reviews[:sample_size]
    
    # Format them into a single string
    review_texts = []
    for r in sampled_reviews:
        # Limit review text to 100 characters with ellipsis
        review_text = r.get('text', 'No text')
        truncated_text = review_text[:100] + "..." if len(review_text) > 100 else review_text
        
        review_texts.append(f"{r.get('author_name', 'Anonymous')} ({r.get('rating', 'N/A')}★): {truncated_text}")
                  
    return '\n'.join(review_texts)


def format_hours(opening_hours):
    """
    Format opening hours into readable text
    
    Args:
        opening_hours (dict): Opening hours information
    
    Returns:
        str: Formatted hours text
    """
    if not opening_hours:
        return "Hours not available"
        
    if 'weekday_text' in opening_hours:
        return '\n'.join(opening_hours['weekday_text'])
        
    return "Open now" if opening_hours.get('open_now', False) else "Hours not available"


def process_results(businesses):
    """
    Process and format the search results
    
    Args:
        businesses (list): List of businesses with details
        
    Returns:
        pandas.DataFrame: DataFrame containing processed results
    """
    results = []
    
    for business in businesses:
        # Extract positive and negative reviews based on rating
        positive_reviews = [r for r in business.get('reviews', []) if r.get('rating', 0) >= 4]
        negative_reviews = [r for r in business.get('reviews', []) if r.get('rating', 0) <= 2]
        
        # Apply the review sampling rules
        pos_summary = sample_reviews(positive_reviews)
        neg_summary = sample_reviews(negative_reviews)
        
        # Format business hours
        hours_text = format_hours(business.get('opening_hours', {}))
        
        # Process keywords
        keywords = business.get('keyword_matches', [])
        keywords_text = ', '.join(keywords[:50])  # Limit to 50 keywords
        
        # Calculate individual match percentages
        rating_match = calculate_rating_match_percentage(business, businesses)
        address_match = calculate_address_match_percentage(business, businesses)
        price_match = calculate_price_match_percentage(business, businesses)
        
        # Prepare the result row
        result = {
            'Name': business.get('name', 'N/A'),
            'Address': business.get('formatted_address', 'N/A'),
            'Address_Match': f"{address_match}%",
            'Rating': business.get('rating', 'N/A'),
            'Total_Reviews': business.get('user_ratings_total', 'N/A'),
            'Rating_Review_Match': f"{rating_match}%",
            'Phone': business.get('formatted_phone_number', 'N/A'),
            'Website': business.get('website', 'N/A'),
            'Price_Level': '$' * business.get('price_level', 0) if 'price_level' in business else 'N/A',
            'Price_Match': f"{price_match}%",
            'Hours': hours_text,
            'Keywords': keywords_text,
            'Positive_Reviews': pos_summary,
            'Negative_Reviews': neg_summary,
            'Overall_Match': f"{business.get('match_percentage', 0)}%"
        }
        
        results.append(result)
        
    # Create DataFrame
    return pd.DataFrame(results)