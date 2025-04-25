from flask import request, jsonify, current_app, Blueprint
from flasgger import swag_from
from src.utils.response_utils import error_response
from src.services.match_services import check_place_constraints
from src.services.review_service import generate_review_summaries, extract_key_themes_from_reviews
from src.services.insight_service import generate_business_insights

# Create the blueprint
analyze_bp = Blueprint('analyze', __name__)

@analyze_bp.route('/task/analyze', methods=['POST'])
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
                    'leadCount': {
                        'type': 'integer',
                        'example': 0
                    },
                    'numberOfLeads': {
                        'type': 'integer',
                        'example': 3
                    },
                    'placeDetails': {
                        'type': 'object',
                        'properties': {
                            'placeName': {
                                'type': 'string',
                                'example': 'Demandailing Cafe'
                            },
                            'address': {
                                'type': 'string',
                                'example': 'Jl. Raya Jemursari No.71, Surabaya'
                            },
                            'businessHours': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'example': [
                                    "Monday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
                                    "Tuesday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
                                    "Wednesday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
                                    "Thursday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
                                    "Friday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
                                    "Saturday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM",
                                    "Sunday: 8:00\u202fAM\u2009\u2013\u200910:00\u202fPM"
                                ]
                            },
                            'businessType': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'example': ['cafe', 'restaurant', 'food',]
                            },
                            'contact': {
                                'type': 'object',
                                'properties': {
                                    'phone': {
                                        'type': 'string',
                                        'example': '(031) 8480367'
                                    },
                                    'website': {
                                        'type': 'string',
                                        'example': 'http://instagram.com/demandailingcafe'
                                    }
                                }
                            },
                            'location': {
                                'type': 'object',
                                'properties': {
                                    'lat': {
                                        'type': 'number',
                                        'format': 'float',
                                        'example': -7.3225321
                                    },
                                    'lng': {
                                        'type': 'number',
                                        'format': 'float',
                                        'example': 112.7423232
                                    }
                                }
                            },
                            'positiveReviews': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'example': [ 
                                    "Always like being here...\nA couple years ago, celebrate every moment here with friend, family or coworker\nThe have a wow portion, for 2-3 person per serving\nYou may enjoy it with friends\nMy kids always love their millecrepes and waffles\nOverall about this place is the menu never failed",
                                    "It was my very first visit to Demandailing Cafe. I went here with my friends and their babies, but we didn't reserve for a table. The staffs directly led us to a table with long couches, so the babies can sleep there. Love how attentive they are!\n\nNot to forget the food, it was so yummy. And fit those with big appetite. Overall it's a good place for having a lunch.",
                                    "Good services and kind staff. Nice atmosphere. Located beside main road. Easy to find. Large park. Arabica coffee.",   
                                    "Best pancake I've ever tasted.\nThe place more spaces than Klampis branch had.\nThe services was great. The meals came after waiting Less than 5 minutes."
                                ]
                            },
                            'negativeReviews': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'example': ["The cashier & greater are not friendly.  The smoking area is dirty and smells like a cat's poop."]
                            },
                            'priceRange': {
                                'type': 'string',
                                'example': '$$'
                            },
                            'rating': {
                                'type': 'number',
                                'format': 'float',
                                'example': 4.5
                            },
                            'totalRatings': {
                                'type': 'integer',
                                'example': 4202
                            }
                        }
                    },
                    'skippedCount': {
                        'type': 'integer',
                        'example': 0
                    },
                    'constraints': {
                        'type': 'object',
                        'properties': {
                            'min_rating': {
                                'type': 'number',
                                'format': 'float',
                                'example': 4.0
                            },
                            'min_reviews': {
                                'type': 'integer',
                                'example': 50
                            },
                            'price_range': {
                                'type': 'string',
                                'example': '$$'
                            },
                            'business_hours': {
                                'type': 'string',
                                'example': 'anytime'
                            },
                            'keywords': {
                                'type': 'string',
                                'example': 'cocok buat nugas'
                            }
                        }
                    }
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
    Analyzes a place against the specified constraints and generates insights
    
    Returns:
        dict: Response object with analysis results or next action
    """
    try:
        # Get request data and log it
        data = request.get_json()
        current_app.logger.info(f"Analyze route called with data keys: {data.keys() if data else 'None'}")
        
        if not data or "placeDetails" not in data:
            current_app.logger.error("Missing required field: placeDetails")
            return error_response("Missing required field: placeDetails")

        # Extract required fields with logging
        place_details = data.get("placeDetails", {})
        current_app.logger.info(f"Place details: {place_details.get('placeName', 'Unknown')}")
        
        constraints = data.get("constraints", {})
        current_app.logger.info(f"Constraints received: {constraints}")
        
        lead_count = data.get("leadCount", 0)
        skipped_count = data.get("skippedCount", 0)
        number_of_leads = data.get("numberOfLeads", 0)
        current_app.logger.info(f"Lead count: {lead_count}, Skipped count: {skipped_count}, Target leads: {number_of_leads}")
        
        # Check if place meets constraints
        meets_constraints, match_percentage, match_analysis = check_place_constraints(place_details, constraints)
        current_app.logger.info(f"Constraints check: meets={meets_constraints}, match={match_percentage}%")
        
        # If constraints not met, return skip response
        if not meets_constraints:
            current_app.logger.info(f"Place does not meet constraints, skipping: {place_details.get('placeName', 'Unknown')}")
            response = create_skip_response(lead_count, skipped_count)
            return jsonify(response)
            
        # Extract reviews for summarization
        positive_reviews = place_details.get("positiveReviews", [])
        negative_reviews = place_details.get("negativeReviews", [])
        current_app.logger.info(f"Reviews for analysis: positive={len(positive_reviews)}, negative={len(negative_reviews)}")
        
        # Extract keywords from constraints - LOG THIS TO DEBUG KEYWORD ISSUE
        keywords = constraints.get("keywords", "")
        current_app.logger.info(f"Keywords for analysis: '{keywords}'")
        
        # Generate review summaries with keyword count
        current_app.logger.info("Calling generate_review_summaries...")
        review_summaries = generate_review_summaries(positive_reviews, negative_reviews, keywords)
        current_app.logger.info(f"Review summaries result keys: {review_summaries.keys() if review_summaries else 'None'}")
        
        # Add review summaries to place details
        place_details["reviewSummary"] = {
            "positive": review_summaries.get("positive", ""),
            "negative": review_summaries.get("negative", "")
        }
        
        # Add keyword match if available - THIS IS CRITICAL FOR YOUR ISSUE
        if "keywordMatch" in review_summaries:
            place_details["keywordMatch"] = review_summaries["keywordMatch"]
            current_app.logger.info(f"Added keywordMatch to place_details: {place_details['keywordMatch']}")
        else:
            current_app.logger.warning("No keywordMatch in review_summaries!")
            # Provide a default value if keywordMatch is missing
            place_details["keywordMatch"] = "0 keywords found from 0 reviews"
        
        # Generate business insights
        current_app.logger.info("Generating business insights...")
        insights = generate_business_insights(place_details, match_percentage, match_analysis)
        current_app.logger.info("Business insights generated successfully")
        
        # Increment lead count
        lead_count += 1
        
        # Prepare the result with place details, match percentage, and insights
        result = {
            "placeName": place_details["placeName"],
            "placeId": place_details.get("placeId", ""),
            "address": place_details.get("address", ""),
            "rating": place_details.get("rating", 0),
            "totalRatings": place_details.get("totalRatings", 0),
            "priceRange": place_details.get("priceRange", ""),
            "businessType": place_details.get("businessType", []),
            "matchPercentage": match_percentage,
            "strengths": insights.get("strengths", []),
            "weaknesses": insights.get("weaknesses", []),
            "fitScore": insights.get("fitScore", 0),
            "fitReason": insights.get("fitReason", ""),
            "phone": place_details.get("phone", ""),
            "website": place_details.get("website", ""),
            "businessHours": place_details.get("businessHours", []),
            "coordinates": place_details.get("coordinates", {}),
            "reviewSummary": place_details.get("reviewSummary", {}),
            # Make sure keywordMatch is included in the final result
            "keywordMatch": place_details.get("keywordMatch", "0 keywords found from 0 reviews")
        }
        
        # Log the keywordMatch value in the final result
        current_app.logger.info(f"keywordMatch in final result: {result.get('keywordMatch', 'Not found')}")
        
        # Return response with result and next action
        response = {
            "state": {
                "skippedCount": skipped_count,
                "leadCount": lead_count,
                "numberOfLeads": number_of_leads
            },
            "result": result,
            "next": {
                "key": "control",
                "payload": {
                    "skippedCount": "$state.skippedCount",
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
        
        current_app.logger.info(f"Returning successful analysis for {place_details.get('placeName', 'Unknown')}")
        return jsonify(response)
    except Exception as e:
        current_app.logger.error(f"Analyze route failed: {str(e)}", exc_info=True)  # Add exc_info for full stack trace
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
    
    # Make sure keywordMatch is included
    if "keywordMatch" in place_details:
        result["keywordMatch"] = place_details["keywordMatch"]
    else:
        current_app.logger.warning("keywordMatch not found in place_details during result creation")
        result["keywordMatch"] = "0 keywords found from 0 reviews"
        
    return result