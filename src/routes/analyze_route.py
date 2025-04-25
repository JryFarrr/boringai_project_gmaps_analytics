from flask import request, jsonify, current_app
from flasgger import swag_from
from src.utils.response_utils import error_response
from src.services.match_services import check_place_constraints
from src.services.review_service import generate_review_summaries, extract_key_themes_from_reviews
from src.services.insight_service import generate_business_insights

@swag_from({
    'tags': ['Task'],
    'summary': 'Analyze and generate business insights',
    'description': 'Analyze business information, match percentage, and generate insights using OpenAI',
    'parameters': [
        {
            'name': 'data',
            'in': 'body',
            'description': 'Details for analysis and lead handling',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'placeDetails': {
                        'type': 'object',
                        'properties': {
                            'placeName': {'type': 'string', 'example': 'Cafe Delight'},
                            'contact': {
                                'type': 'object',
                                'properties': {
                                    'phone': {'type': 'string', 'example': '123-456-7890'},
                                    'website': {'type': 'string', 'example': 'https://cafedelight.com'}
                                }
                            },
                            'priceRange': {'type': 'string', 'example': '$$'},
                            'positiveReviews': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'example': ['Great vibe']
                            },
                            'negativeReviews': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'example': ['Crowded']
                            }
                        }
                    },
                    'leadCount': {'type': 'integer', 'example': 0}
                },
                'required': ['placeDetails', 'leadCount']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Successful analysis and insights',
            'schema': {
                'type': 'object',
                'properties': {
                    'placeName': {'type': 'string'},
                    'matchPercentage': {'type': 'number'},
                    'strengths': {'type': 'array', 'items': {'type': 'string'}},
                    'weaknesses': {'type': 'array', 'items': {'type': 'string'}},
                    'fitScore': {'type': 'number'},
                    'fitReason': {'type': 'string'}
                }
            }
        },
        '500': {
            'description': 'Internal server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'state': {'type': 'object'},
                    'result': {'type': 'object'},
                    'next': {
                        'type': 'object',
                        'properties': {
                            'key': {'type': 'string'},
                            'payload': {'type': 'object'}
                        }
                    },
                    'done': {'type': 'boolean'},
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def analyze_route():
    """
    Handle the analyze task endpoint
    - Processes place details and constraints
    - Calculates match percentage based on various criteria
    - Uses OpenAI to generate insightful review summaries
    - Returns formatted response with match results
    """
    try:
        data = request.get_json()
        if not data or "placeDetails" not in data or "leadCount" not in data:
            return error_response("Missing required fields: placeDetails or leadCount")

        place_details = data["placeDetails"]
        lead_count = data["leadCount"]
        constraints = data.get("constraints", {})
        skipped_count = data.get("skippedCount", 0)
        
        # Check if place meets constraints
        meets_constraints, match_percentage, match_analysis = check_place_constraints(place_details, constraints)
        
        # If constraints not met, return skip response
        if not meets_constraints:
            response = create_skip_response(lead_count, skipped_count)
            return jsonify(response), 200
        
        # Process reviews and generate summaries
        positive_reviews = place_details.get("positiveReviews", [])
        negative_reviews = place_details.get("negativeReviews", [])
        all_reviews = positive_reviews + negative_reviews
        
        # Get summaries and key themes
        summaries = generate_review_summaries(positive_reviews, negative_reviews)
        key_themes = extract_key_themes_from_reviews(all_reviews)
        
        # Generate business insights
        insights = generate_business_insights(place_details, match_percentage, match_analysis)
        
        # Create and return response
        result = create_result_object(place_details, match_percentage, match_analysis, 
                                      summaries, key_themes, insights)
        
        response = {
            "state": {
                "leadCount": lead_count + 1,
                "skippedCount": skipped_count
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
                    "business_type": "$state.business_type",
                    "location": "$state.location",
                    "skippedCount": "$state.skippedCount"
                }
            },
            "done": False,
            "error": None
        }
        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Analyze route failed: {str(e)}")
        return error_response(f"Analyze route failed: {str(e)}", 500)

def create_skip_response(lead_count, skipped_count):
    """
    Creates a response object for skipping a place that doesn't meet constraints
    
    Args:
        lead_count (int): Current count of leads
        skipped_count (int): Current count of skipped places
        
    Returns:
        dict: Response object with skip signal
    """
    return {
        "state": {
            "leadCount": lead_count,
            "skippedConstraints": True,
            "skippedCount": skipped_count + 1
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
                "business_type": "$state.business_type",
                "location": "$state.location",
                "skippedConstraints": True,
                "skippedCount": "$state.skippedCount"
            }
        },
        "done": False,
        "error": None
    }

def create_result_object(place_details, match_percentage, match_analysis, summaries, key_themes, insights):
    """
    Creates the result object with all business analysis data
    
    Args:
        place_details (dict): Details about the business
        match_percentage (float): Match percentage calculated
        match_analysis (dict): Analysis of the match percentage
        summaries (dict): Summaries of positive and negative reviews
        key_themes (list): Key themes extracted from reviews
        insights (dict): Business insights and recommendations
        
    Returns:
        dict: Formatted result object
    """
    result = {
        "placeName": place_details["placeName"],
        "matchPercentage": match_percentage,
        "business_type": place_details.get("business_type", []),
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
    if "positive" in summaries and summaries["positive"]:
        result["summaryPositiveReviews"] = summaries["positive"]
    if "negative" in summaries and summaries["negative"]:
        result["summaryNegativeReviews"] = summaries["negative"]
    
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
        
    return result