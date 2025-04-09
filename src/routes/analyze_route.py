from flask import request, jsonify
from src.utils.response_utils import error_response
from src.utils.business_matcher import (
    match_price_range, 
    check_business_hours,
    search_reviews_for_keywords,
    calculate_match_percentage
)
from src.services.api_clients.factory import create_client

def generate_review_summary(reviews, review_type="positive", max_length=150):
    """
    Generate a concise summary of reviews using OpenAI
    
    Args:
        reviews (list): List of review texts
        review_type (str): Type of reviews ("positive" or "negative")
        max_length (int): Maximum length of the summary
    
    Returns:
        str: Concise summary of the reviews
    """
    if not reviews:
        return ""
    
    # Limit to first 5 reviews to keep token count reasonable
    reviews_text = "\n\n".join(reviews[:5])
    
    try:
        # Create client for OpenAI
        client, headers, provider = create_client(provider="openai")
        
        # Prepare prompt for OpenAI
        prompt = f"""Summarize the following {review_type} reviews for a business.
        Focus on extracting the key points, recurring themes, and specific elements that customers mention.
        Keep your summary concise (maximum {max_length} characters) and focus on actionable insights.
        
        Reviews:
        {reviews_text}
        """
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes business reviews concisely."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100  # Limit token count for concise response
        )
        
        # Extract and return the summary
        summary = response.choices[0].message.content.strip()
        
        # Ensure summary is within the max length
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
            
        return summary
        
    except Exception as e:
        print(f"Error generating review summary: {str(e)}")
        
        # Fallback to basic summarization if API call fails
        summary_items = []
        for i, review in enumerate(reviews[:3]):
            summary_items.append(review[:100] + ("..." if len(review) > 100 else ""))
        return " | ".join(summary_items)

# Modified analyze_route.py
def analyze_route():
    """
    Handle the analyze task endpoint
    - Processes place details and constraints
    - Calculates match percentage based on various criteria
    - Uses OpenAI to generate insightful review summaries
    - Returns formatted response with match results
    """
    data = request.get_json()
    if not data or "placeDetails" not in data or "leadCount" not in data:
        return error_response("Missing required fields: placeDetails or leadCount")

    place_details = data["placeDetails"]
    lead_count = data["leadCount"]
    constraints = data.get("constraints", {})
    skipped_count = data.get("skippedCount", 0)  # Get skipped count with default 0
    
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
    
    # Calculate match percentage
    match_percentage = calculate_match_percentage(place, parameters)
    
    # Apply multipliers for price and business hours matches
    # If price doesn't match and it was specified, reduce match percentage
    if parameters["price_range"] and place.get("price_match") is False:
        match_percentage *= 0.7  # Reduce by 30%
        
    # If business hours don't match and they were specified, reduce match percentage
    if parameters["business_hours"] != "anytime" and place.get("hours_match") is False:
        match_percentage *= 0.7  # Reduce by 30%
        
    # Ensure match percentage is between 0-100 and rounded
    match_percentage = round(max(0, min(100, match_percentage)), 2)
    
    # If place doesn't meet hard constraints, signal control to find another place
    if not meets_constraints:
        # Return a special signal to control to skip this place and move to next
        response = {
            "state": {
                "leadCount": lead_count,  # Don't increment lead count for skipped places
                "skippedConstraints": True,  # Signal that we're skipping due to constraints
                "skippedCount": skipped_count + 1  # Increment skipped count
            },
            "result": None,
            "next": {
                "key": "control",
                "payload": {
                    "leadCount": "$state.leadCount",
                    "numberOfLeads": "$state.numberOfLeads",
                    "remainingPlaceIds": "$state.remainingPlaceIds",
                    "searchOffset": "$state.searchOffset",
                    "nextPageToken": "$state.nextPageToken",
                    "businessType": "$state.businessType",
                    "location": "$state.location",
                    "skippedConstraints": True,
                    "skippedCount": "$state.skippedCount"  # Pass skipped count
                }
            },
            "done": False,
            "error": None
        }
        return jsonify(response), 200
    
    # If meets constraints, continue normal processing
    # Use OpenAI to generate review summaries
    positive_reviews = place_details.get("positiveReviews", [])
    negative_reviews = place_details.get("negativeReviews", [])
    
    # Get summaries using OpenAI
    summary_positive = generate_review_summary(positive_reviews, "positive") if positive_reviews else ""
    summary_negative = generate_review_summary(negative_reviews, "negative") if negative_reviews else ""
    
    # Prepare the result object
    result = {
        "placeName": place_details["placeName"],
        "matchPercentage": match_percentage
    }
    
    # Add summaries if they exist
    if summary_positive:
        result["summaryPositiveReviews"] = summary_positive
    if summary_negative:
        result["summaryNegativeReviews"] = summary_negative
        
    # Add contact information if available
    if "contact" in place_details:
        result["contact"] = place_details["contact"]
        
    # Add address if available
    if "address" in place_details:
        result["address"] = place_details["address"]
    
    # Format the response according to the unified contract
    response = {
        "state": {
            "leadCount": lead_count + 1,
            "skippedCount": skipped_count  # Preserve skipped count in state
        },
        "result": result,
        "next": {
            "key": "control",
            "payload": {
                "leadCount": "$state.leadCount",
                "numberOfLeads": "$state.numberOfLeads",
                "remainingPlaceIds": "$state.remainingPlaceIds",
                "searchOffset": "$state.searchOffset",
                "nextPageToken": "$state.nextPageToken",
                "businessType": "$state.businessType",
                "location": "$state.location",
                "skippedCount": "$state.skippedCount"  # Pass skipped count
            }
        },
        "done": False,
        "error": None
    }
    return jsonify(response), 200