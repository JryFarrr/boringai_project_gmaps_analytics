from flask import request, jsonify, current_app
from flasgger import swag_from
from src.utils.response_utils import error_response
from src.utils.validation_utils import validate_search_payload
from src.services.search_service import (
    collect_place_ids,
    create_search_response,
    create_target_reached_response
)
from src.docs.search import search_dict

@swag_from(search_dict)
def search_route():
    """
    Handle the search task endpoint with improved lead collection strategy
    
    This endpoint searches for businesses based on business type and location.
    It efficiently collects multiple place IDs at once to reduce API calls,
    and manages pagination for larger result sets.
    
    Scenarios:
    1. Target leads already reached - End workflow
    2. Collect place IDs (using remaining IDs, next page token, or new search)
    3. Send first place ID for scraping, store the rest for later use
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return error_response("Invalid JSON payload")

        # Validate required fields
        validation_error = validate_search_payload(data)
        if validation_error:
            return error_response(validation_error)

        # Extract data from request
        business_type = data["business_type"]
        location = data["location"]
        search_offset = data["searchOffset"]
        number_of_leads = data["numberOfLeads"]
        next_page_token = data.get("nextPageToken")
        lead_count = data.get("leadCount", 0)
        skipped_count = data.get("skippedCount", 0)
        remaining_place_ids = data.get("remainingPlaceIds", [])

        try:
            # Determine how many more leads are needed
            remaining_leads_needed = number_of_leads - lead_count
            
            # If target already reached, end workflow
            if remaining_leads_needed <= 0:
                current_app.logger.info(f"Lead target of {number_of_leads} already met with {lead_count} leads. Finishing workflow.")
                return jsonify(create_target_reached_response()), 200
                
            # Total needed including compensation for potentially skipped places
            total_needed = remaining_leads_needed + skipped_count
            current_app.logger.info(f"Need {remaining_leads_needed} more leads. Including {skipped_count} skipped, total needed: {total_needed}")

            # Collect all place_ids needed to fulfill the request
            result = collect_place_ids(
                business_type=business_type,
                location=location,
                total_needed=total_needed,
                remaining_place_ids=remaining_place_ids,
                next_page_token=next_page_token
            )
            
            if not result["place_ids"]:
                return error_response("No businesses found", 404)

            # Create and return response
            response = create_search_response(
                place_ids=result["place_ids"],
                next_page_token=result["next_page_token"],
                search_offset=search_offset,
                lead_count=lead_count,
                skipped_count=skipped_count,
                business_type=business_type,
                location=location,
                number_of_leads=number_of_leads
            )
            
            return jsonify(response), 200
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            current_app.logger.error(f"Search failed: {str(e)}\n{error_details}")
            return error_response(f"Search failed: {str(e)}", 500)
    except Exception as e:
        current_app.logger.error(f"Search route failed: {str(e)}")
        return error_response(f"Search route failed: {str(e)}", 500)