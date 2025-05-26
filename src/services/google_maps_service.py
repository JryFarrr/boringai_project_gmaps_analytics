import requests
import time
import openai # Tetap diimpor karena ada fungsi lain yang menggunakannya, meski tidak di alur utama ini
import json
from src.config import config
from datetime import datetime
from flask import current_app # Import current_app for logging

# === GLOBAL API KEYS ===
api_key = None # For Google Places Text Search and Place Details (googleapis.com)
openai_api_key = None # Kept for other potential uses, not directly used in the main review flow
search_api_key = None # For SearchAPI.io (searchapi.io)

# === INIT API KEYS ===
def init_api_key(key=None):
    """Initialize the Google Maps API key (for Google's direct APIs)"""
    global api_key
    if key:
        api_key = key
    else:
        api_key = config.GOOGLE_API_KEY
    return api_key


def init_openai_key(key=None):
    """Initialize OpenAI API key"""
    global openai_api_key
    if key:
        openai_api_key = key
    else:
        openai_api_key = config.OPENAI_API_KEY
    return openai_api_key


def init_search_api_key(key=None):
    """Initialize SearchAPI.io API key"""
    global search_api_key
    if key:
        search_api_key = key
    else:
        search_api_key = config.SEARCHAPI_API_KEY
    return search_api_key


# === GOOGLE PLACES TEXT SEARCH ===
def search_places(query=None, page_token=None):
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {'key': get_api_key()} # Uses the Google Maps API key

    if page_token is not None:
        params['pagetoken'] = page_token
    elif query is not None:
        params['query'] = query
    else:
        raise ValueError("Either query or page_token must be provided")

    try:
        max_attempts = 3
        for attempt in range(max_attempts):
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if data['status'] == 'INVALID_REQUEST' and page_token and attempt < max_attempts - 1:
                time.sleep(2 * (attempt + 1))
                continue

            if data['status'] not in ('OK', 'ZERO_RESULTS'):
                if data['status'] == 'INVALID_REQUEST' and page_token and attempt == max_attempts - 1:
                    return {'results': [], 'next_page_token': None}
                raise ValueError(f"API Error: {data['status']}")

            return {'results': data.get('results', []), 'next_page_token': data.get('next_page_token')}
    except requests.RequestException as e:
        current_app.logger.error(f"Google Places Text Search failed: {str(e)}") # Added logging
        raise Exception(f"Request failed: {str(e)}")


# === GET GOOGLE API KEY ===
def get_api_key():
    global api_key
    if api_key is None:
        # Initialize the API key if not already done
        api_key = init_api_key()
        if not api_key:
            raise ValueError("Google Maps API key not found. Make sure it's set in your config.")
    return api_key


# === GET SEARCH API KEY ===
def get_search_api_key():
    global search_api_key
    if search_api_key is None:
        # Initialize the API key if not already done
        search_api_key = init_search_api_key()
        if not search_api_key:
            raise ValueError("SearchAPI.io key not found. Make sure it's set in your config.")
    return search_api_key


# === GET PLACE DETAILS ===
def get_place_details(place_id, fields=None):
    google_api_key = get_api_key()  # Ensure we have a Google Maps API key for Place Details

    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": google_api_key
    }
    if fields:
        params["fields"] = ",".join(fields)

    try:
        current_app.logger.info(f"Fetching place details for place_id: {place_id}")
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] != "OK":
            current_app.logger.error(f"API error for place_id {place_id}: {data.get('error_message', data['status'])}")
            raise Exception(f"API error: {data.get('error_message', data['status'])}")
        
        # Get the basic place details
        place_details = data.get("result", {})
        place_details["place_id"] = place_id
        # Note: get_place_reviews is called here without a search_query,
        # meaning it will fetch general reviews for displaying basic place details.
        # Specific keyword-filtered reviews will be fetched by the generate_review_summaries/get_reviews_for_place flow.
        place_details["reviews"] = get_place_reviews(place_id) 
        
        return place_details
    except requests.RequestException as e:
        current_app.logger.error(f"Request error for place_id {place_id}: {str(e)}")
        raise Exception(f"Failed to call Google Maps API: {str(e)}")


def get_place_reviews(place_id, max_reviews=100, search_query=None):
    """
    Fetches reviews for a given place_id using SearchAPI.io, with optional keyword filtering.
    """
    api_key_searchapi = get_search_api_key() # Get the SearchAPI.io key
    url = "https://api.searchapi.io/api/v1/search"

    params = {
        "engine": "Maps_reviews", # Ensure this is correct as per SearchAPI.io docs (case-sensitive)
        "place_id": place_id,
        "num": min(max_reviews, 100), # max 100 per page for SearchAPI.io's 'num' parameter
        "api_key": api_key_searchapi
    }

    if search_query:
        params["search_query"] = search_query
        current_app.logger.info(f"SearchAPI.io: Fetching reviews for place_id '{place_id}' with search_query: '{search_query}'")
    else:
        current_app.logger.info(f"SearchAPI.io: Fetching all reviews for place_id '{place_id}' (no search_query)")


    all_reviews = []

    while True:
        try:
            response = requests.get(url, params=params)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            if response.status_code != 200:
                current_app.logger.error(f"Error fetching reviews from SearchAPI.io for place_id {place_id}: {data.get('error', 'Unknown error')}")
                break

            reviews_on_page = data.get('reviews', [])
            all_reviews.extend(reviews_on_page)

            # Handle pagination
            next_page_token = data.get('serpapi_pagination', {}).get('next_page_token')
            if next_page_token and len(all_reviews) < max_reviews:
                params['next_page_token'] = next_page_token
                # It's generally safe to keep 'num' as the API will still respect the max 100 per page.
            else:
                break # No more pages or max_reviews reached

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Network or API request error while fetching reviews for place_id {place_id}: {str(e)}")
            break # Exit loop on request error
        except json.JSONDecodeError:
            current_app.logger.error(f"Failed to decode JSON response from SearchAPI.io for place_id {place_id}")
            break # Exit loop if JSON is invalid

    current_app.logger.info(f"Fetched {len(all_reviews)} reviews for place_id {place_id}.")
    return all_reviews[:max_reviews] # Ensure we don't return more than max_reviews


# === SEARCH VIA SEARCHAPI.IO (replacing SerpAPI) ===
def search_business_with_search_api(keyword, location="Indonesia", max_results=5):
    """
    Searches for businesses by keyword using SearchAPI.io (Google Maps engine).
    """
    api_key_searchapi = get_search_api_key()
    
    search_url = "https://api.searchapi.io/api/v1/search"
    
    params = {
        "engine": "Maps", # Changed from 'Maps' to 'Maps' as per SearchAPI.io's documentation or common practice
        "q": keyword,
        "location": location,
        "api_key": api_key_searchapi,
        "num": max_results
    }

    try:
        current_app.logger.info(f"SearchAPI.io: Searching for businesses with keyword: '{keyword}' in {location}")
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        results = response.json()

        businesses = []
        for biz in results.get("local_results", [])[:max_results]:
            businesses.append({
                "title": biz.get("title"),
                "address": biz.get("address"),
                "place_id": biz.get("place_id"),
                "gps_coordinates": biz.get("gps_coordinates", {}),
                "rating": biz.get("rating"),
                "reviews_count": biz.get("reviews"),
                "Maps_url": biz.get("link") # Changed from 'Maps_url' to 'Maps_url' for consistency
            })
        current_app.logger.info(f"SearchAPI.io: Found {len(businesses)} businesses matching '{keyword}'.")
        return businesses

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"SearchAPI.io business search failed: {str(e)}")
        raise RuntimeError(f"SearchAPI.io request failed: {str(e)}")
    except json.JSONDecodeError:
        current_app.logger.error(f"SearchAPI.io: Failed to decode JSON response for business search.")
        raise RuntimeError("SearchAPI.io request failed: Invalid JSON response.")


# === OpenAI related functions are REMOVED as per the new requirement ===
# If 'src.utils.business_matcher.extract_key_themes' also relies on OpenAI,
# you might need to remove that dependency or this file won't compile without 'create_client'.
# For now, I'm assuming 'create_client' is only for OpenAI here and will be removed.

# If create_client is *only* for OpenAI, and you don't want to use OpenAI at all:
# from src.utils.business_matcher import extract_key_themes # Keep this if it's not OpenAI-dependent
# You would need to remove the 'from src.services.api_clients.factory import create_client' line
# if create_client is solely for OpenAI and no other API clients are used.

# Removing OpenAI-related functions and imports if they are truly not needed elsewhere in this file.
# Assuming 'extract_key_themes' will be handled separately or removed if it was OpenAI-dependent.

# The original 'summarize_and_extract_keywords' function is removed:
# def summarize_and_extract_keywords(reviews): ...


# === MAIN SCRAPE TASK (renamed for clarity, it primarily searches) ===
def scrape_business_data_by_keyword(keyword, location="Indonesia", max_results=5):
    """
    Searches for businesses by keyword using SearchAPI.io and returns basic info.
    
    Args:
        keyword (str): The keyword to search for
        location (str): The location to search in
        max_results (int): Maximum number of results to return
        
    Returns:
        list: List of businesses with place_id and other basic info
    """
    current_app.logger.info(f"Searching for businesses with keyword: '{keyword}' in {location}")
    businesses = search_business_with_search_api(keyword, location=location, max_results=max_results)
    current_app.logger.info(f"Found {len(businesses)} businesses matching the keyword.")
    return businesses