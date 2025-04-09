# Modified google_maps_service.py
import requests
import time

# Store API key globally
api_key = None

def init_api_key(key):
    """Initialize the API key for Google Maps API calls"""
    global api_key
    api_key = key
    return api_key

def get_api_key():
    """Get the configured API key"""
    global api_key
    if api_key is None:
        raise ValueError("API key not initialized. Call init_api_key first.")
    return api_key

def search_places(query=None, page_token=None):
    """
    Search for places using Google Maps Places API with pagination support
    
    Args:
        query (str): The search query (e.g., "Restaurants in Surabaya")
        page_token (str): Next page token from previous results
        
    Returns:
        dict: Results and next_page_token if available
    """
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'key': get_api_key()
    }
    
    if page_token is not None:
        # When using page token, we must wait at least 2 seconds
        # as per Google's documentation
        params['pagetoken'] = page_token
    elif query is not None:
        params['query'] = query
    else:
        raise ValueError("Either query or page_token must be provided")

    try:
        # Handle pageToken properly - sometimes it needs a delay
        max_attempts = 3
        for attempt in range(max_attempts):
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Check for valid response
            if data['status'] == 'INVALID_REQUEST' and page_token and attempt < max_attempts - 1:
                # Page token might not be ready yet, wait and retry
                time.sleep(2 * (attempt + 1))  # Increasing delay on each retry
                continue
            
            if data['status'] not in ('OK', 'ZERO_RESULTS'):
                # If this is the last attempt with a page token and we still get INVALID_REQUEST
                # return an empty result set rather than raising an error
                if data['status'] == 'INVALID_REQUEST' and page_token and attempt == max_attempts - 1:
                    return {
                        'results': [],
                        'next_page_token': None
                    }
                raise ValueError(f"API Error: {data['status']}")
            
            return {
                'results': data.get('results', []),
                'next_page_token': data.get('next_page_token')
            }
    except requests.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")

def get_place_details(place_id, fields=None):
    if not api_key:
        raise ValueError("Google Maps API key is not initialized. Call init_api_key first.")
    
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": api_key
    }
    if fields:
        params["fields"] = ",".join(fields)
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data["status"] != "OK":
            raise Exception(f"API error: {data.get('error_message', data['status'])}")
        return data.get("result", {})
    except requests.RequestException as e:
        raise Exception(f"Failed to call Google Maps API: {str(e)}")