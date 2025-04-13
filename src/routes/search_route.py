# Modified search_route.py
from flask import request, jsonify, current_app
from src.utils.response_utils import error_response
from src.services.google_maps_service import search_places
import traceback
import time

def search_route():
    """Handle the search task endpoint with improved lead collection strategy that collects all needed data at once"""
    data = request.get_json()
    if not data:
        return error_response("Invalid JSON payload")

    # Validate required fields
    required_fields = ["businessType", "location", "searchOffset", "numberOfLeads"]
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")

    # Extract data from request
    business_type = data["businessType"]
    location = data["location"]
    search_offset = data["searchOffset"]
    number_of_leads = data["numberOfLeads"]
    next_page_token = data.get("nextPageToken")
    lead_count = data["leadCount"] if "leadCount" in data else 0
    skipped_count = data.get("skippedCount", 0)  # Get skipped count
    remaining_place_ids = data.get("remainingPlaceIds", [])

    try:
        # Determine how many more leads are needed (including compensation for skipped places)
        remaining_leads_needed = number_of_leads - lead_count
        
        # Jika kita sudah mencapai jumlah lead yang diminta, langsung kembalikan done=True
        if remaining_leads_needed <= 0:
            current_app.logger.info(f"Lead target of {number_of_leads} already met with {lead_count} leads. Finishing workflow.")
            return jsonify({
                "state": None,
                "result": None,
                "next": None,
                "done": True,
                "error": None
            }), 200
            
        # Total yang perlu dicari termasuk cadangan untuk yang mungkin dilewati
        total_needed = remaining_leads_needed + skipped_count
        
        current_app.logger.info(f"Need {remaining_leads_needed} more leads. Including {skipped_count} skipped, total needed: {total_needed}")

        # Collect all place_ids needed to fulfill the request
        all_place_ids = []
        current_next_page_token = next_page_token
        
        # First, use any existing place_ids from previous searches
        if remaining_place_ids:
            current_app.logger.info(f"Using {len(remaining_place_ids)} previously found place IDs")
            all_place_ids.extend(remaining_place_ids)
            # Reset token if we're using existing IDs to prevent issues
            if len(all_place_ids) >= total_needed:
                current_next_page_token = None
        
        # Keep collecting place_ids until we have enough or run out of results
        page_count = 0
        max_pages = 3  # Limit the number of pages we try to fetch to avoid excessive API calls
        
        while len(all_place_ids) < total_needed and page_count < max_pages:
            page_count += 1
            
            try:
                # Call Google Maps API to search for places
                if current_next_page_token:
                    current_app.logger.info(f"Searching with page token (page {page_count}): {current_next_page_token[:30]}...")
                    response = search_places(page_token=current_next_page_token)
                else:
                    query = f"{business_type} in {location}"
                    current_app.logger.info(f"Searching for: {query} (page {page_count})")
                    response = search_places(query=query)
                
                # Extract new place_ids and add to our collection
                new_place_ids = [place['place_id'] for place in response.get('results', [])]
                
                # If we didn't get any new place_ids, exit the loop
                if not new_place_ids:
                    current_app.logger.info(f"No new place IDs found on page {page_count}")
                    break
                    
                current_app.logger.info(f"Found {len(new_place_ids)} new place IDs on page {page_count}")
                all_place_ids.extend(new_place_ids)
                
                # Update next_page_token for potential next iteration
                current_next_page_token = response.get('next_page_token')
                
                # If no nextPageToken or already have enough place_ids, exit loop
                if not current_next_page_token:
                    current_app.logger.info("No next page token available, ending search")
                    break
                
                # Log progress
                current_app.logger.info(f"Collected {len(all_place_ids)} place IDs so far, need {total_needed}")
                
                # Add a delay before the next iteration if we're going to use the page token
                if current_next_page_token and len(all_place_ids) < total_needed:
                    current_app.logger.info("Waiting 2 seconds before fetching next page...")
                    time.sleep(2)
            
            except Exception as search_error:
                current_app.logger.error(f"Error fetching page {page_count}: {str(search_error)}")
                # If we have some results already, continue with what we have
                if all_place_ids:
                    current_app.logger.info(f"Continuing with {len(all_place_ids)} place IDs already collected")
                    current_next_page_token = None
                    break
                else:
                    # Re-raise the exception if we have no results at all
                    raise

        # If we couldn't find any place_ids
        if not all_place_ids:
            return error_response("No businesses found", 404)

        # Limit place_ids based on total needed
        if len(all_place_ids) > total_needed:
            all_place_ids = all_place_ids[:total_needed]

        # Take the first place ID to send to payload
        first_place_id = all_place_ids[0]
        new_remaining = all_place_ids[1:]
        
        # Prepare state object that matches the example format but includes necessary data
        state = {
            "remainingPlaceIds": new_remaining,
            "searchOffset": search_offset + len(all_place_ids),
            "nextPageToken": current_next_page_token,  # Always include nextPageToken, will be null if no token
            "skippedCount": skipped_count,  # Preserve skipped count in state
            "leadCount": lead_count,  # Explicitly set leadCount in state to ensure it's preserved
            "businessType": business_type,
            "location": location,
            "numberOfLeads": number_of_leads
        }
        
        # Prepare response
        response = {
            "state": state,
            "result": None,
            "next": {
                "key": "scrape",
                "payload": {
                    "placeId": first_place_id,
                    "skippedCount": skipped_count,  # Pass skipped count to scrape
                    "leadCount": lead_count,        # Pass lead count to scrape
                    "numberOfLeads": number_of_leads # Pass number of leads to scrape
                }
            },
            "done": False,
            "error": None
        }
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Search failed: {str(e)}\n{error_details}")
        return error_response(f"Search failed: {str(e)}", 500)

    return jsonify(response), 200