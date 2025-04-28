from flask import request, jsonify, current_app
from flasgger import swag_from
from src.utils.response_utils import error_response
from src.services.scrape_service import (
    search_and_get_place_id,
    process_place_details,
    create_scrape_response,
)
from src.services.review_service import extract_reviews_by_sentiment
from src.services.match_services import check_place_constraints
from src.services.review_service import generate_review_summaries
from src.docs.scrape import scrape_dict

@swag_from(scrape_dict)
def scrape_route():
    """
    Handle the scrape task endpoint with SearchAPI.io integration
    
    Retrieves business details from Google Maps API using either:
    1. A direct place_id provided in the request
    2. A keyword search that returns a place_id to query
    
    The endpoint retrieves details such as business name, contact info,
    address, ratings, reviews, and business hours.
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("Missing request data")

        # Get state values
        skipped_count = data.get("skippedCount", 0)
        lead_count = data.get("leadCount", 0)
        number_of_leads = data.get("numberOfLeads", 0)

        # Check if we already have a Place ID or need to search by keyword
        place_id = data.get("placeId")
        keyword = data.get("keyword")
        location = data.get("location", "Indonesia")
        business_type = data.get("business_type", "")
        
        # Get constraints for calculating match percentage
        constraints = data.get("constraints", {})
        
        # Extract remaining place IDs if present
        remaining_place_ids = data.get("remainingPlaceIds", [])
        search_offset = data.get("searchOffset", 0)
        next_page_token = data.get("nextPageToken", "")

        # If no placeId is provided, we need a keyword to search
        if not place_id and not keyword and not remaining_place_ids:
            return error_response("Either placeId, keyword, or remainingPlaceIds is required")

        try:
            # If we don't have a place_id but have a keyword, search first
            if not place_id and keyword:
                current_app.logger.info(f"Searching for keyword: {keyword} in {location}")
                place_id = search_and_get_place_id(keyword, location, business_type, search_offset, next_page_token)
                
                if not place_id:
                    return error_response("No valid Place ID found in search results", 404)
                    
                current_app.logger.info(f"Found place ID: {place_id} for keyword '{keyword}'")
            
            # If we have remaining place IDs, use the first one
            elif not place_id and remaining_place_ids:
                place_id = remaining_place_ids[0]
                remaining_place_ids = remaining_place_ids[1:]  # Remove used place ID
                current_app.logger.info(f"Using place ID from remainingPlaceIds: {place_id}")

            # Now we have a place_id, get the details
            current_app.logger.info(f"Scraping place ID: {place_id} (leadCount={lead_count}, skippedCount={skipped_count})")
            
            # Process place details
            place_data = process_place_details(place_id)
            current_app.logger.info(f"Retrieved details for place: {place_data.get('placeName', 'Unknown')}")
            
            # Extract the keywords from constraints
            keywords = constraints.get("keywords", "")
            current_app.logger.info(f"Keywords for analysis: '{keywords}'")
            
            # Separate reviews by sentiment
            all_reviews = place_data.get("reviews", [])
            positive_reviews, negative_reviews = extract_reviews_by_sentiment(all_reviews)
            
            # Add positive and negative reviews to place_data
            place_data["positiveReviews"] = positive_reviews
            place_data["negativeReviews"] = negative_reviews
            
            # Calculate review count
            review_count = len(positive_reviews) + len(negative_reviews)
            place_data["reviewCount"] = review_count
            current_app.logger.info(f"Reviews for analysis: positive={len(positive_reviews)}, negative={len(negative_reviews)}")
            
            # Generate review summaries with keyword count
            current_app.logger.info("Calling generate_review_summaries...")
            review_summaries = generate_review_summaries(positive_reviews, negative_reviews, keywords)
            current_app.logger.info(f"Review summaries result keys: {review_summaries.keys() if review_summaries else 'None'}")
            
            # Add review summaries to place details
            place_data["reviewSummary"] = {
                "positive": review_summaries.get("positive", ""),
                "negative": review_summaries.get("negative", "")
            }
            
            # Add keyword match if available
            if "keywordMatch" in review_summaries:
                place_data["keywordMatch"] = review_summaries["keywordMatch"]
                current_app.logger.info(f"Added keywordMatch to place_details: {place_data['keywordMatch']}")
            else:
                current_app.logger.warning("No keywordMatch in review_summaries!")
                # Provide a default value if keywordMatch is missing
                place_data["keywordMatch"] = "Keywords not found"
                
            

            # Check if we've already reached the target (to handle race conditions)
            if lead_count >= number_of_leads:
                current_app.logger.info(f"Target already reached during scrape! Lead count {lead_count} >= requested {number_of_leads}. Ending workflow.")
                return jsonify({
                    "state": None,
                    "result": None,
                    "next": None,
                    "done": True,
                    "error": None
                }), 200

            # Create response with updated state
            response = create_scrape_response(place_data, lead_count, skipped_count, number_of_leads)
            
            # Update response with remaining place IDs and search parameters
            response["state"]["remainingPlaceIds"] = remaining_place_ids
            response["state"]["searchOffset"] = search_offset
            response["state"]["nextPageToken"] = next_page_token
            response["state"]["business_type"] = business_type
            response["state"]["location"] = location
            
            # Update payload with the same values
            response["next"]["payload"]["remainingPlaceIds"] = "$state.remainingPlaceIds"
            response["next"]["payload"]["searchOffset"] = "$state.searchOffset"
            response["next"]["payload"]["nextPageToken"] = "$state.nextPageToken"
            response["next"]["payload"]["business_type"] = "$state.business_type"
            response["next"]["payload"]["location"] = "$state.location"
            
            return jsonify(response), 200
            
        except Exception as e:
            current_app.logger.error(f"Scrape failed: {str(e)}")
            return error_response(f"Scrape failed: {str(e)}", 500)
    except Exception as e:
        current_app.logger.error(f"Scrape route failed: {str(e)}")
        return error_response(f"Scrape route failed: {str(e)}", 500)