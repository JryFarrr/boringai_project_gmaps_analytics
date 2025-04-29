from src.utils.business_matcher import (
    check_business_hours,
    match_price_range, 
    search_reviews_for_keywords,
    calculate_match_percentage,
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
        "max_reviews": constraints.get("max_reviews", None),
        "price_range": constraints.get("price_range", ""),
        "business_hours": constraints.get("business_hours", "anytime"),
        "keywords": constraints.get("keywords", ""),
        "address": constraints.get("address", "")
    }
    
    # Create a place object compatible with calculate_match_percentage
    place = {
        "name": place_details["placeName"],
        "rating": place_details.get("rating", 0),
        "user_ratings_total": place_details.get("totalRatings", 0),
        "address": place_details.get("address", ""), 
    }
    
    # Flag to track if place meets all hard constraints
    meets_constraints = True
    
    # Check if rating meets minimum required rating (HARD CONSTRAINT)
    if parameters["min_rating"] > 0 and place["rating"] < parameters["min_rating"]:
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

    if parameters["business_hours"] != "anytime" and "businessHours" in place_details:
        hours_match = check_business_hours(place_details, parameters["business_hours"])
        place["hours_match"] = hours_match
        if not hours_match:
            meets_constraints = False
    
    # Process reviews to find keywords if specified (SOFT CONSTRAINT)
    if parameters["keywords"]:

        keyword_matches = search_reviews_for_keywords(place_details, parameters["keywords"])
        place["keyword_matches"] = keyword_matches
    
    # Collect all reviews for AI analysis
    all_reviews = []
    all_reviews.extend(place_details.get("positiveReviews", []))
    all_reviews.extend(place_details.get("negativeReviews", []))
    
    # Calculate match percentage using OpenAI
    place["types"] = place_details.get("businessType", [])

    # Calculate match percentage
    match_percentage = calculate_match_percentage(place, parameters)

    # Create match analysis with reasoning
    match_analysis = {
        "reasoning": create_match_reasoning(place, parameters, match_percentage),
        "analysis": create_factor_analysis(place, parameters)
    }

    return meets_constraints, match_percentage, match_analysis

def create_match_reasoning(place, parameters, match_percentage):

    reasoning = f"This business matches {match_percentage:.1f}% of your criteria. "

    # Add rating explanation
    if parameters["min_rating"] > 0:
        if place["rating"] >= parameters["min_rating"]:
            reasoning += f"It has a good rating of {place['rating']}/5.0. "
        else:
            reasoning += f"Its rating of {place['rating']}/5.0 is below your minimum of {parameters['min_rating']}. "

    # Add review count explanation
    if parameters["min_reviews"] > 0:
        if place["user_ratings_total"] >= parameters["min_reviews"]:
            reasoning += f"It has {place['user_ratings_total']} reviews, meeting your minimum requirement. "
        else:
            reasoning += f"It only has {place['user_ratings_total']} reviews, below your minimum of {parameters['min_reviews']}. "

    # Add price range explanation
    if parameters["price_range"] and "price_match" in place:
        if place["price_match"]:
            reasoning += f"Its price range ({place.get('price_level', 0) * '$'}) matches your criteria. "
        else:
            reasoning += f"Its price range ({place.get('price_level', 0) * '$'}) doesn't match your criteria. "

    # Add business hours explanation
    if parameters["business_hours"] != "anytime" and "hours_match" in place:
        if place["hours_match"]:
            reasoning += f"Its business hours match your {parameters['business_hours']} requirement. "
        else:
            reasoning += f"Its business hours don't match your {parameters['business_hours']} requirement. "

    # Add address match explanation if address parameter is provided
    if parameters["address"] and place.get("address"):
        # Simple substring match for address - could be more sophisticated
        if parameters["address"].lower() in place["address"].lower():
            reasoning += f"The address matches your criteria. "
        else:
            reasoning += f"The address doesn't exactly match your criteria. "
    

    return reasoning

    


def create_factor_analysis(place, parameters):
    """
    Creates a detailed analysis of different matching factors
    
    Args:
        place (dict): Place object with match data
        parameters (dict): Parameters used for matching
        
    Returns:
        dict: Factor-by-factor analysis
    """
    analysis = {}

    # Rating factor
    if parameters["min_rating"] > 0:
        rating_score = min(100, (place["rating"] / parameters["min_rating"]) * 100) if parameters["min_rating"] > 0 else 100
        analysis["rating"] = {
            "score": rating_score,
            "details": f"{place['rating']}/5.0 vs minimum {parameters['min_rating']}/5.0"
        }

    # Review count factor
    if parameters["min_reviews"] > 0:
        review_score = min(100, (place["user_ratings_total"] / parameters["min_reviews"]) * 100) if parameters["min_reviews"] > 0 else 100
        analysis["review_count"] = {
            "score": review_score,
            "details": f"{place['user_ratings_total']} reviews vs minimum {parameters['min_reviews']}"
        }

    # Price range factor
    if parameters["price_range"] and "price_match" in place:
        price_score = 100 if place["price_match"] else 0
        analysis["price_range"] = {
            "score": price_score,
            "details": "Matches your price range criteria" if place["price_match"] else "Does not match your price range criteria"
        }

    # Business hours factor
    if parameters["business_hours"] != "anytime" and "hours_match" in place:
        hours_score = 100 if place["hours_match"] else 0
        analysis["business_hours"] = {
            "score": hours_score,
            "details": f"Matches your {parameters['business_hours']} requirement" if place["hours_match"] else f"Does not match your {parameters['business_hours']} requirement"
        }

    # Keyword match factor
    if parameters["keywords"] and "keyword_matches" in place:
        keyword_score = place["keyword_matches"].get("match_percentage", 0)
        matches = place["keyword_matches"].get("matched_keywords", [])
        analysis["keywords"] = {
            "score": keyword_score,
            "details": f"Found {len(matches)}/{len(parameters['keywords'].split(','))} keywords: {', '.join(matches)}" if matches else "No keywords found"
        }

    # Address match factor
    if parameters["address"] and place.get("address"):
        # Simple substring match - could be more sophisticated
        address_match = parameters["address"].lower() in place["address"].lower()
        address_score = 100 if address_match else 50  # Give partial score even if not exact match
        analysis["address"] = {
            "score": address_score,
            "details": "Address matches your criteria" if address_match else "Address doesn't exactly match your criteria"
        }
