from flask import request, jsonify, current_app, Blueprint
from flasgger import swag_from
from src.utils.response_utils import error_response
from src.services.match_services import check_place_constraints
from src.services.review_service import generate_review_summaries
from src.services.insight_service import generate_business_insights
from src.docs.analyze import analyze_dict
# Create the blueprint
analyze_bp = Blueprint('analyze', __name__)

@analyze_bp.route('/task/analyze', methods=['POST'])
@swag_from(analyze_dict)
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

        # Run constraint check to get match_percentage
        meets_constraints, match_percentage, match_analysis = check_place_constraints(place_details, constraints)
        current_app.logger.info(f"Constraints check: meets={meets_constraints}, match={match_percentage}%")
  
        # If constraints not met, return skip response
        if not meets_constraints:
            current_app.logger.info(f"Place does not meet constraints, skipping: {place_details.get('placeName', 'Unknown')}")
            response = create_skip_response(lead_count, skipped_count)
            return jsonify(response)
        
        # The review data and keyword matching are now coming from the scrape_route
        # We just need to focus on additional insights generation
        
        # Generate business insights using the data from scrape
        current_app.logger.info("Generating business insights...")
        insights = generate_business_insights(place_details, match_percentage, match_analysis)
        current_app.logger.info("Business insights generated successfully")
        
        # Increment lead count
        lead_count += 1
        
        # Prepare the result with place details, match percentage, and insights
        result = create_result_object(place_details, match_percentage, match_analysis, insights)
        
        # Log the keywordMatch value in the final result  
        current_app.logger.info(f"keywordMatch in final result: {result.get('keywordMatch', 'Not found')}")
        current_app.logger.info(f"Total reviews analyzed: {result.get('reviewCount', 0)}")
        
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
                    "business_type": "$state.business_type",  # Sesuaikan dari business_type
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
                "businessType": "$state.businessType",  # Sesuaikan dari business_type
                "location": "$state.location",
                "skippedConstraints": True,
                "skippedCount": "$state.skippedCount"
            }
        },
        "done": False,
        "error": None
    }


def create_result_object(place_details, match_percentage, match_analysis, insights):
    """
    Creates the result object with all business analysis data
    
    Args:
        place_details (dict): Details about the business including review summaries
        match_percentage (float): Match percentage calculated
        match_analysis (dict): Analysis of the match percentage  
        insights (dict): Business insights and recommendations
        
    Returns:
        dict: Formatted result object
    """
    result = {
        "placeName": place_details["placeName"],
        "placeId": place_details.get("placeId", ""),
        "address": place_details.get("address", ""),
        "rating": place_details.get("rating", 0),
        "totalRatings": place_details.get("totalRatings", 0),
        "priceRange": place_details.get("priceRange", ""),
        "business_type": place_details.get("business_type", []),
        "location" : place_details.get("location", []),
        "matchPercentage": match_percentage,
        "strengths": insights.get("strengths", []),
        "weaknesses": insights.get("weaknesses", []),
        "matchReasoning": match_analysis.get("reasoning", ""), 
        "phone": place_details.get("phone", ""),
        "website": place_details.get("website", ""),
        "businessHours": place_details.get("businessHours", []),
        "coordinates": place_details.get("coordinates", {}),
        "reviewSummary": place_details.get("reviewSummary", {}),
        "keywordMatch": place_details.get("keywordMatch", "Keywords not found"),
        "reviewCount": place_details.get("reviewCount", 0)
    }
    
    # Add match analysis reasoning if available
    if match_analysis and "analysis" in match_analysis:
        result["matchFactors"] = match_analysis["analysis"]
    # Add insights
    if insights:
        result["strengths"] = insights.get("strengths", [])
        result["weaknesses"] = insights.get("weaknesses", [])
        
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
        result["keywordMatch"] = "Keywords not found"
    
        
    return result

