from flask import request, jsonify, current_app
from flasgger import swag_from
from src.utils.response_utils import error_response
from src.services.scrape_service import (
    search_and_get_place_id,
    process_place_details,
    create_scrape_response
)

@swag_from({
    'tags': ['Task'],
    'summary': 'Scrape business details using Google Maps API',
    'description': 'Get detailed business information from a Place ID',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['placeId', 'numberOfLeads'],
                'properties': {
                    'placeId': {'type': 'string', 'example': 'ChIJhS6qhGT51y0RUCoksi_dipo'},
                    'numberOfLeads': {'type': 'integer', 'example': 10},
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Successful scrape',
            'schema': {
                'type': 'object',
                'properties': {
                    'state': {'type': 'object', 'nullable': True},
                    'next': {
                        'type': 'object',
                        'properties': {
                            'key': {'type': 'string', 'example': 'analyze'},
                            'payload': {
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
                                    'leadCount': {'type': 'string', 'example': '$state.leadCount'}
                                }
                            }
                        }
                    },
                    'result': {'type': 'object', 'nullable': True},
                    'done': {'type': 'boolean', 'example': False},
                    'error': {'type': 'string', 'nullable': True}
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

        # If no placeId is provided, we need a keyword to search
        if not place_id and not keyword:
            return error_response("Either placeId or keyword is required")

        try:
            # If we don't have a place_id but have a keyword, search first
            if not place_id and keyword:
                current_app.logger.info(f"Searching for keyword: {keyword} in {location}")
                place_id = search_and_get_place_id(keyword, location)
                
                if not place_id:
                    return error_response("No valid Place ID found in search results", 404)
                    
                current_app.logger.info(f"Found place ID: {place_id} for keyword '{keyword}'")

            # Now we have a place_id, get the details
            current_app.logger.info(f"Scraping place ID: {place_id} (leadCount={lead_count}, skippedCount={skipped_count})")
            
            # Process place details
            place_data = process_place_details(place_id)
            current_app.logger.info(f"Retrieved details for place: {place_data.get('placeName', 'Unknown')}")

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

            # Create response
            response = create_scrape_response(place_data, lead_count, skipped_count, number_of_leads)
            return jsonify(response), 200
            
        except Exception as e:
            current_app.logger.error(f"Scrape failed: {str(e)}")
            return error_response(f"Scrape failed: {str(e)}", 500)
    except Exception as e:
        current_app.logger.error(f"Scrape route failed: {str(e)}")
        return error_response(f"Scrape route failed: {str(e)}", 500)