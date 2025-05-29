from flask import request, jsonify, current_app, Blueprint
from flasgger import swag_from
from src.utils.response_utils import error_response
from src.services.match_services import check_place_constraints
# Updated import: review_service now returns a dict with numeric counts
from src.services.review_service import generate_review_summaries 
from src.services.insight_service import generate_business_insights
from src.docs.analyze import analyze_dict
# Removed import re as it's no longer needed for string parsing

# Create the blueprint
analyze_bp = Blueprint("analyze", __name__)

@analyze_bp.route("/task/analyze", methods=["POST"])
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

        # --- Extract place_id --- 
        place_id = place_details.get("placeId") # Assuming placeId is available in placeDetails
        if not place_id:
             current_app.logger.warning("placeId not found in placeDetails. Keyword search via SearchAPI might fail.")
        # --- End Extract --- 

        constraints = data.get("constraints", {})
        current_app.logger.info(f"Constraints received: {constraints}")

        lead_count = data.get("leadCount", 0)
        skipped_count = data.get("skippedCount", 0)
        number_of_leads = data.get("numberOfLeads", 0)
        current_app.logger.info(f"Lead count: {lead_count}, Skipped count: {skipped_count}, Target leads: {number_of_leads}")

        # Extract reviews for summarization (scraping part remains)
        positive_reviews = place_details.get("positiveReviews", [])
        negative_reviews = place_details.get("negativeReviews", [])
        current_app.logger.info(f"Reviews for summarization: positive={len(positive_reviews)}, negative={len(negative_reviews)}")

        # Extract keywords from constraints
        keywords = constraints.get("keywords", "")
        current_app.logger.info(f"Keywords for analysis: '{keywords}'")

        # Generate review summaries and keyword count using SearchAPI
        current_app.logger.info("Calling generate_review_summaries...")
        # review_summaries is now a dict including numeric counts
        review_summaries = generate_review_summaries(positive_reviews, negative_reviews, keywords, place_id)
        current_app.logger.info(f"Review summaries result keys: {review_summaries.keys() if review_summaries else 'None'}")

        # Add review summaries to place details
        place_details["reviewSummary"] = {
            "positive": review_summaries.get("positive", ""),
            "negative": review_summaries.get("negative", "")
        }

        # Add keyword match string (for display/info) and numeric counts
        keyword_match_result_string = review_summaries.get("keywordMatch", "keyword match information unavailable")
        keyword_count_n = review_summaries.get("keywordCountN", -1) # Get numeric count n, default to -1 if missing
        keyword_total_b = review_summaries.get("keywordTotalB", -1) # Get numeric count b, default to -1 if missing
        
        place_details["keywordMatch"] = keyword_match_result_string # Store the display string
        current_app.logger.info(f"Received keyword match data: n={keyword_count_n}, b={keyword_total_b}, string='{keyword_match_result_string}'")

        # --- REVISED LOGIC: Determine keyword_not_found based ONLY on numeric count n --- 
        keyword_not_found = True # Default to True (not found)
        if keyword_count_n > 0:
            keyword_not_found = False # Set to False ONLY if count n is greater than 0
            current_app.logger.info(f"Keyword count n={keyword_count_n}. Keywords FOUND.")
        elif keyword_count_n == 0:
             current_app.logger.warning(f"Keyword count n=0. Keywords considered NOT FOUND.")
        else: # keyword_count_n is likely -1, indicating an error or missing data
             current_app.logger.error(f"Keyword count n={keyword_count_n} (error or unavailable). Keywords considered NOT FOUND.")
        # --- END REVISED LOGIC --- 

        # Check if place meets constraints (using existing logic, but influenced by keyword_not_found)
        meets_constraints, match_percentage, match_analysis = check_place_constraints(place_details, constraints)
        current_app.logger.info(f"Initial constraints check: meets={meets_constraints}, match={match_percentage}%")

        # CRITICAL CHANGE: Force skip if keywords not found based on numeric count n
        if keyword_not_found:
            # Check if it already failed constraints for other reasons
            if meets_constraints: 
                current_app.logger.warning(f"Forcing meets_constraints=False and match_percentage=0 because keywords were not found (n={keyword_count_n})")
                meets_constraints = False
                match_percentage = 0
                # Update match_analysis reasoning to reflect keyword issue
                reason = f"Keyword match issue (n={keyword_count_n}, result: '{keyword_match_result_string}')."
                if match_analysis and "reasoning" in match_analysis:
                    match_analysis["reasoning"] = reason + " " + match_analysis["reasoning"]
                elif match_analysis:
                    match_analysis["reasoning"] = reason
                else:
                    match_analysis = {"reasoning": reason}
            else:
                 current_app.logger.info(f"Place already failed constraints. Keyword issue noted (n={keyword_count_n}) but decision unchanged.")

        current_app.logger.info(f"Final constraints check: meets={meets_constraints}, match={match_percentage}%")

        # Generate business insights
        current_app.logger.info("Generating business insights...")
        insights = generate_business_insights(place_details, match_percentage, match_analysis)
        current_app.logger.info("Business insights generated successfully")

        # Prepare the result with place details, match percentage, and insights
        # Pass the original review_summaries dict which now contains n and b
        result = create_result_object(place_details, match_percentage, match_analysis, review_summaries, [], insights)

        current_app.logger.info(f"Total scraped reviews analyzed for summary: {result.get('reviewCount', 0)}")
        current_app.logger.info(f"Keyword match based on SearchAPI: {result.get('keywordMatch', 'N/A')} (n={result.get('keywordCountN', 'N/A')}, b={result.get('keywordTotalB', 'N/A')})")

        # Log final decision factors
        current_app.logger.info(f"FINAL DECISION - meets_constraints: {meets_constraints}")

        # If constraints not met, return skip response
        if not meets_constraints:
            current_app.logger.info(f"Place does not meet constraints, skipping: {place_details.get('placeName', 'Unknown')}")
            response = create_skip_response(lead_count, skipped_count, result)
            return jsonify(response)

        # Only increment lead count for places we keep
        lead_count += 1

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
                    # Pass necessary state items forward
                    "skippedCount": "$state.skippedCount",
                    "leadCount": "$state.leadCount",
                    "numberOfLeads": "$state.numberOfLeads",
                    "remainingPlaceIds": "$state.remainingPlaceIds",
                    "searchOffset": "$state.searchOffset",
                    "nextPageToken": "$state.nextPageToken",
                    "business_type": "$state.business_type",
                    "location": "$state.location"
                }
            },
            "done": False,
            "error": None
        }

        current_app.logger.info(f"Returning successful analysis for {place_details.get('placeName', 'Unknown')}")
        return jsonify(response)
    except Exception as e:
        current_app.logger.error(f"Analyze route failed: {str(e)}", exc_info=True)
        return error_response(f"Analyze route failed: {str(e)}", 500)

def create_skip_response(lead_count, skipped_count, result):
    """
    Creates a response object for skipping a place that doesn't meet constraints

    Args:
        lead_count (int): Current count of leads
        skipped_count (int): Current count of skipped places
        result (dict): The analysis result for the skipped place (now includes n, b)

    Returns:
        dict: Response object with skip signal
    """
    return {
        "state": {
            "leadCount": lead_count,
            "skippedConstraints": True,
            "skippedCount": skipped_count + 1
        },
        "result": result, # Include the analysis result even when skipping
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
        summaries (dict): Dict containing summaries and keyword counts (n, b)
        key_themes (list): Key themes extracted from reviews (if used)
        insights (dict): Business insights and recommendations

    Returns:
        dict: Formatted result object
    """
    # Calculate review count from scraped reviews used for summarization
    scraped_review_count = len(place_details.get("positiveReviews", [])) + len(place_details.get("negativeReviews", []))

    result = {
        "placeName": place_details.get("placeName", "Unknown"),
        "address": place_details.get("address", ""),
        "rating": place_details.get("rating", 0),
        "totalRatings": place_details.get("totalRatings", 0), # This might differ from SearchAPI total
        "priceRange": place_details.get("priceRange", ""),
        "businessType": place_details.get("businessType", []),
        "matchPercentage": match_percentage,
        "matchReasoning": match_analysis.get("reasoning", ""),
        "strengths": insights.get("strengths", []),
        "weaknesses": insights.get("weaknesses", []),
        "phone": place_details.get("contact", {}).get("phone", ""),
        "website": place_details.get("contact", {}).get("website", ""),
        "businessHours": place_details.get("businessHours", []),
        "coordinates": place_details.get("coordinates", {}),
        "reviewSummary": place_details.get("reviewSummary", {}),
        "keywordMatch": summaries.get("keywordMatch", "keyword match information unavailable"), # Display string
        "keywordCountN": summaries.get("keywordCountN", -1), # Numeric count n
        "keywordTotalB": summaries.get("keywordTotalB", -1), # Numeric count b
        "reviewCount": scraped_review_count # Count of reviews used for summarization
    }

    # Add detailed factor scores if available
    if match_analysis and "analysis" in match_analysis:
        result["matchFactors"] = match_analysis["analysis"]

    # Add summaries if they exist
    if "positive" in summaries and summaries["positive"]:
        result["summaryPositiveReviews"] = summaries["positive"]
    if "negative" in summaries and summaries["negative"]:
        result["summaryNegativeReviews"] = summaries["negative"]

    # Add key themes if generated and available
    # if key_themes:
    #     result["keyThemes"] = key_themes

    return result

