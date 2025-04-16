from src.utils.business_matcher import (
    match_price_range, 
    check_business_hours,
    search_reviews_for_keywords,
    calculate_match_percentage,
    calculate_match_percentage_with_ai
)

def check_place_constraints(place_details, constraints):
    """
    Checks if a place meets the specified constraints and calculates the match percentage
    
    Args:
        place_details (dict): Details about the business
        constraints (dict): Constraints specified by the user
        
    Returns:
        tuple: (meets_constraints, match_percentage, match_analysis)
            - meets_constraints (bool): Whether the place meets all hard constraints
            - match_percentage (float): Match percentage calculated
            - match_analysis (dict): Analysis of the match percentage
    """
    # Extract required parameters from constraints with defaults
    parameters = {
        "min_rating": constraints.get("min_rating", 0),
        "min_reviews": constraints.get("min_reviews", 0),
        "price_range": constraints.get("price_range", ""),
        "business_hours": constraints.get("business_hours", "anytime"),
        "keywords": constraints.get("keywords", ""),
        "topPlaces": constraints.get("topPlaces", 5)
    }
    
    # Create a place object compatible with calculate_match_percentage
    place = {
        "name": place_details["placeName"],
        "rating": place_details.get("rating", 0),
        "user_ratings_total": place_details.get("totalRatings", 0),
    }
    
    # Flag to track if place meets all hard constraints
    meets_constraints = True
    
    # Check if rating meets minimum required rating (HARD CONSTRAINT)
    if parameters["min_rating"] > 0 and place["rating"] < parameters["min_rating"]:
        meets_constraints = False
    
    # Check if total reviews meets minimum required (HARD CONSTRAINT)
    if parameters["min_reviews"] > 0 and place["user_ratings_total"] < parameters["min_reviews"]:
        meets_constraints = False
    
    # Add price level if available
    if "priceRange" in place_details:
        # Convert $ symbols to numeric price_level
        price_level = len(place_details["priceRange"])
        place["price_level"] = price_level
        
        # Check if price range matches the required price range (HARD CONSTRAINT if specified)
        if parameters["price_range"]:
            price_match = match_price_range(place_details["priceRange"], parameters["price_range"])
            place["price_match"] = price_match
            if not price_match:
                meets_constraints = False
    
    # Check if business hours match the required hours (SOFT CONSTRAINT)
    if parameters["business_hours"] != "anytime" and "businessHours" in place_details:
        # Format place_details to match the expected structure for check_business_hours
        hours_details = {
            "opening_hours": {
                "weekday_text": place_details["businessHours"] if isinstance(place_details["businessHours"], list) else []
            }
        }
        
        # If "open_now" key is present in the data, add it to the structure
        if "open_now" in place_details:
            hours_details["opening_hours"]["open_now"] = place_details["open_now"]
            
        hours_match = check_business_hours(hours_details, parameters["business_hours"])
        place["hours_match"] = hours_match
    
    # Process reviews to find keywords if specified (SOFT CONSTRAINT)
    if parameters["keywords"]:
        # Create a format that matches the business_matcher expectations
        place_details_for_reviews = {
            "name": place_details["placeName"],
            "types": place_details.get("businessType", []),
            "reviews": []
        }
        
        # Format reviews to match expected structure
        for review in place_details.get("positiveReviews", []):
            place_details_for_reviews["reviews"].append({"text": review})
        for review in place_details.get("negativeReviews", []):
            place_details_for_reviews["reviews"].append({"text": review})
            
        # Find keyword matches
        keyword_matches = search_reviews_for_keywords(place_details_for_reviews, parameters["keywords"])
        place["keyword_matches"] = keyword_matches
    
    # Collect all reviews for AI analysis
    all_reviews = []
    all_reviews.extend(place_details.get("positiveReviews", []))
    all_reviews.extend(place_details.get("negativeReviews", []))
    
    # Calculate match percentage using OpenAI
    try:
        # Add business type to place info
        place["types"] = place_details.get("businessType", [])
        
        # Use OpenAI to calculate match percentage
        match_percentage, match_analysis = calculate_match_percentage_with_ai(place, parameters, all_reviews)
    except Exception as e:
        print(f"Error using AI to calculate match percentage: {str(e)}")
        # Fallback to traditional calculation if OpenAI fails
        match_percentage = calculate_match_percentage(place, parameters)
        match_analysis = {
            "reasoning": "Calculated using traditional algorithm due to AI service unavailability."
        }
    
    return meets_constraints, match_percentage, match_analysis