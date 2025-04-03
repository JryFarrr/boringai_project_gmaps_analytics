import requests

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
    Direct API call to Google Maps Places API Text Search
    """
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "key": get_api_key()
    }
    
    if page_token:
        params["pagetoken"] = page_token
    elif query:
        params["query"] = query
    else:
        raise ValueError("Either query or page_token must be provided")

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Lempar error jika bukan 200
        data = response.json()

        if data["status"] not in ["OK", "ZERO_RESULTS"]:
            raise Exception(f"API error: {data.get('error_message', data['status'])}")

        return {
            "results": data.get("results", []),
            "next_page_token": data.get("next_page_token")
        }
    except requests.RequestException as e:
        raise Exception(f"Failed to call Google Maps API: {str(e)}")

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