from flask import request, jsonify
from src.utils.response_utils import error_response
from src.utils.business_matcher import (
    match_price_range, 
    check_business_hours,
    search_reviews_for_keywords,
    calculate_match_percentage,
    calculate_match_percentage_with_ai,
    extract_key_themes
)
from src.services.api_clients.factory import create_client

def generate_review_summary(reviews, review_type="positive", max_length=200):
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
            max_tokens=150  # Increased token count for better summaries
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

def generate_business_insights(place_details, match_percentage, match_analysis=None):
    """
    Generate business insights and recommendations using OpenAI
    
    Args:
        place_details (dict): Details about the business
        match_percentage (float): Match percentage calculated
        match_analysis (dict): Analysis of the match percentage
    
    Returns:
        dict: Dictionary containing insights and recommendations
    """
    try:
        # Create client for OpenAI
        client, headers, provider = create_client(provider="openai")
        
        # Extract key information for the prompt
        business_name = place_details.get("placeName", "")
        business_type = place_details.get("businessType", [])
        rating = place_details.get("rating", 0)
        total_ratings = place_details.get("totalRatings", 0)
        price_range = place_details.get("priceRange", "")
        
        # Get positive and negative reviews
        positive_reviews = place_details.get("positiveReviews", [])[:3]  # Limit to first 3
        negative_reviews = place_details.get("negativeReviews", [])[:3]  # Limit to first 3
        
        positive_text = "\n".join(positive_reviews) if positive_reviews else ""
        negative_text = "\n".join(negative_reviews) if negative_reviews else ""
        
        # Include match analysis if available
        analysis_text = ""
        if match_analysis and "reasoning" in match_analysis:
            analysis_text = f"Match Analysis: {match_analysis['reasoning']}"
        
        # Prepare prompt for OpenAI
        prompt = f"""Analyze the following business information and provide insights:

        Business Name: {business_name}
        Business Type: {', '.join(business_type) if isinstance(business_type, list) else business_type}
        Rating: {rating}/5 (from {total_ratings} reviews)
        Price Range: {price_range}
        Match Percentage: {match_percentage}%
        {analysis_text}
        
        Sample Positive Reviews:
        {positive_text}
        
        Sample Negative Reviews:
        {negative_text}
        
        Please provide:
        1. A brief assessment of the business's strengths (2-3 points)
        2. A brief assessment of the business's weaknesses (2-3 points)
        3. Potential fit score (0-100) as a lead and a brief explanation why
        
        Format your response as JSON with the keys: "strengths", "weaknesses", "fitScore", and "fitReason".
        """
        
        # Call OpenAI API with JSON mode enabled
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a business analyst that provides insights in JSON format only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=300
        )
        
        # Extract and return the insights
        insights_json = response.choices[0].message.content.strip()
        import json
        insights = json.loads(insights_json)
        
        return insights
        
    except Exception as e:
        print(f"Error generating business insights: {str(e)}")
        # Fallback to basic insights
        return {
            "strengths": ["Based on available reviews"],
            "weaknesses": ["Insufficient data for detailed analysis"],
            "fitScore": int(match_percentage),
            "fitReason": "Score based on match percentage only"
        }

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
    
    # Apply hard constraints check regardless of calculation method
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
    
    # Extract key themes from reviews (uses business_matcher utility)
    key_themes = []
    if positive_reviews or negative_reviews:
        key_themes = extract_key_themes(all_reviews)
    
    # Generate business insights including the match analysis
    insights = generate_business_insights(place_details, match_percentage, match_analysis)
    
    # Prepare the result object
    result = {
        "placeName": place_details["placeName"],
        "matchPercentage": match_percentage,
        "businessType": place_details.get("businessType", []),
        "rating": place_details.get("rating", 0),
        "totalRatings": place_details.get("totalRatings", 0),
        "priceLevel": place_details.get("priceRange", ""),
    }
    
    # Add match analysis reasoning if available
    if match_analysis and "reasoning" in match_analysis:
        result["matchReasoning"] = match_analysis["reasoning"]
    
    # Add detailed factor scores if available
    if match_analysis and "analysis" in match_analysis:
        result["matchFactors"] = match_analysis["analysis"]
    
    # Add summaries if they exist
    if summary_positive:
        result["summaryPositiveReviews"] = summary_positive
    if summary_negative:
        result["summaryNegativeReviews"] = summary_negative
    
    # Add key themes
    if key_themes:
        result["keyThemes"] = key_themes
    
    # Add insights
    if insights:
        result["strengths"] = insights.get("strengths", [])
        result["weaknesses"] = insights.get("weaknesses", [])
        result["fitScore"] = insights.get("fitScore", match_percentage)
        result["fitReason"] = insights.get("fitReason", "")
        
    # Add contact information if available
    if "contact" in place_details:
        result["contact"] = place_details["contact"]
        
    # Add address if available
    if "address" in place_details:
        result["address"] = place_details["address"]
    
    # Add business hours if available
    if "businessHours" in place_details:
        result["businessHours"] = place_details["businessHours"]
    
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
