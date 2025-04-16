def map_price_level(price_level):
    """
    Maps price level integers to dollar symbols
    
    Args:
        price_level (int or str): The price level value
    
    Returns:
        str: Dollar symbols representing the price level
    """
    price_range_map = {
        0: "",     # No price (empty)
        1: "$",    # Inexpensive
        2: "$$",   # Moderate
        3: "$$$",  # Expensive
        4: "$$$$"  # Very expensive
    }
    
    if price_level == '':
        return ""
        
    return price_range_map.get(price_level, "")

def format_place_data(place_details):
    """
    Formats raw place details into a consistent data structure
    
    Args:
        place_details (dict): Raw place details from Google Maps API
    
    Returns:
        dict: Formatted place data with consistent structure and default values
    """
    # Map price_level to dollar symbols
    price_level = place_details.get('price_level', '')
    price_range = map_price_level(price_level)
    
    # Create consistent data structure with default values
    return {
        "placeName": place_details.get('name', 'Unknown'),
        "contact": {
            "phone": place_details.get('formatted_phone_number', 'N/A'),
            "website": place_details.get('website', 'N/A')
        },
        "address": place_details.get('formatted_address', 'N/A'),
        "location": place_details.get('geometry', {}).get('location', {}),
        "rating": place_details.get('rating', 0.0),
        "totalRatings": place_details.get('user_ratings_total', 0),
        "businessHours": place_details.get('opening_hours', {}).get('weekday_text', []),
        "businessType": place_details.get('types', []),
        "priceRange": price_range,
        "positiveReviews": [
            r['text'] for r in place_details.get('reviews', []) if r.get('rating', 0) >= 4
        ],
        "negativeReviews": [
            r['text'] for r in place_details.get('reviews', []) if r.get('rating', 0) < 4
        ]
    }