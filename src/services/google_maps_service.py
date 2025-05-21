import requests
import time
import openai
import json
from src.config import config
from datetime import datetime

# === GLOBAL API KEYS ===
api_key = None
openai_api_key = None
search_api_key = None 

# === INIT API KEYS ===
def init_api_key(key=None):
    """Initialize the Google Maps API key"""
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
    params = {'key': get_api_key()}

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
    google_api_key = get_api_key()  # Ensure we have an API key

    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": google_api_key
    }
    if fields:
        params["fields"] = ",".join(fields)

    try:
        print(f"Fetching place details for place_id: {place_id}")
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] != "OK":
            print(f"API error for place_id {place_id}: {data.get('error_message', data['status'])}")
            raise Exception(f"API error: {data.get('error_message', data['status'])}")
        
        # Get the basic place details
        place_details = data.get("result", {})
        place_details["placeId"] = place_id
        # Add reviews from SearchAPI.io
        place_details["reviews"] = get_place_reviews(place_id)
        
        return place_details
    except requests.RequestException as e:
        print(f"Request error for place_id {place_id}: {str(e)}")
        raise Exception(f"Failed to call Google Maps API: {str(e)}")


# === GET REVIEWS FOR A PLACE ===
def get_place_reviews(place_id, max_reviews=60):
    """
    Get reviews using SearchAPI.io with pagination to overcome the 20 review limit
    
    Args:
        place_id (str): Google place_id for the business
        max_reviews (int): Maximum number of reviews to retrieve (default: 100)
        
    Returns:
        list: List of reviews from SearchAPI.io
    """
    try:
        url = "https://www.searchapi.io/api/v1/search"
        all_reviews = []
        next_page_token = None
        
        # Get the SearchAPI.io API key
        api_key_searchapi = get_search_api_key()
        
        print(f"Starting to fetch reviews for place_id: {place_id}")
        
        # Continue fetching until we have enough reviews or no more pages
        attempts = 0
        while len(all_reviews) < max_reviews and attempts < 5:  # Limit to 5 attempts to prevent infinite loops
            attempts += 1
            
            # Set up parameters for the API request
            params = {
                "engine": "google_maps_reviews",
                "place_id": place_id,
                "api_key": api_key_searchapi,
                # Don't set num higher than 20 or omit to use API default
            }
            
            # Add next_page_token if we have one from a previous request
            if next_page_token:
                params["next_page_token"] = next_page_token
            
            print(f"Fetching reviews for place_id {place_id} from SearchAPI.io... (Attempt {attempts})")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                print(f"Error fetching reviews from SearchAPI.io: {response.status_code}")
                print(f"Response: {response.text}")
                return all_reviews  # Return what we've collected so far
                
            data = response.json()
            
            # Extract reviews from the response
            reviews = data.get('reviews', [])
            
            # If no reviews were returned, break the loop
            if not reviews:
                print(f"No reviews found for place_id {place_id} on this page")
                break
            
            # Add the reviews to our collection
            all_reviews.extend(reviews)
            
            # Get the next page token for pagination
            next_page_token = data.get("pagination", {}).get("next_page_token")
            
            # If there's no next page token, we've reached the end
            if not next_page_token:
                print(f"No more pages of reviews available for place_id {place_id}")
                break
            
            print(f"Fetched {len(reviews)} reviews. Total so far: {len(all_reviews)}")
            
            # Small delay between requests
            time.sleep(1)
        
        # Format reviews to match Google Maps API format
        formatted_reviews = []
        for review in all_reviews[:max_reviews]:
            formatted_review = {
                'author_name': review.get('user', {}).get('name', 'Anonymous'),
                'rating': review.get('rating', 0),
                'text': review.get('text', ''),
                'time': datetime.strptime(review.get('iso_date', datetime.now().isoformat()), "%Y-%m-%dT%H:%M:%SZ").timestamp() if 'iso_date' in review else time.time(),
                'relative_time_description': review.get('date', 'recently')
            }
            formatted_reviews.append(formatted_review)
        
        print(f"Retrieved {len(formatted_reviews)} reviews from SearchAPI.io for place_id {place_id}")
        return formatted_reviews
        
    except Exception as e:
        print(f"Error fetching reviews from SearchAPI.io for place_id {place_id}: {str(e)}")
        return []


# === SEARCH VIA SEARCHAPI.IO (replacing SerpAPI) ===
def search_business_with_search_api(keyword, location="Indonesia", max_results=5):
    # Get the SearchAPI.io key
    api_key_searchapi = get_search_api_key()
    
    # SearchAPI.io endpoint for Google Maps
    search_url = "https://www.searchapi.io/api/v1/search"
    
    params = {
        "engine": "google_maps",
        "q": keyword,
        "location": location,
        "api_key": api_key_searchapi,
        "num": max_results  # Number of results to return
    }

    try:
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
                "google_maps_url": biz.get("link")
            })

        return businesses

    except Exception as e:
        raise RuntimeError(f"SearchAPI.io request failed: {str(e)}")


# === OPENAI: SUMMARIZE & EXTRACT KEYWORDS ===
def summarize_and_extract_keywords(reviews):
    # Initialize OpenAI API key if not already done
    global openai_api_key
    if not openai_api_key:
        openai_api_key = init_openai_key()
        if not openai_api_key:
            raise ValueError("OpenAI API key not found in config")
    
    openai.api_key = openai_api_key

    review_texts = [r.get("text", "") for r in reviews if r.get("text")]
    joined_reviews = "\n".join(review_texts[:30])

    prompt = f"""
    I have the following customer reviews:\n{joined_reviews}\n
    Please provide:
    1. A concise summary of overall customer sentiment and experiences.
    2. A list of key topics and keywords mentioned by customers.
    Format your response in JSON with 'summary' and 'keywords' keys.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a helpful business analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )

        result_text = response['choices'][0]['message']['content']
        return json.loads(result_text)
    except Exception as e:
        raise RuntimeError(f"OpenAI request failed: {str(e)}")


# === MAIN SCRAPE TASK ===
def scrape_business_data_by_keyword(keyword, location="Indonesia", max_results=5):
    """
    Scrapes business data by keyword using SearchAPI.io
    
    Args:
        keyword (str): The keyword to search for
        location (str): The location to search in
        max_results (int): Maximum number of results to return
        
    Returns:
        list: List of businesses with place_id and other basic info
    """
    print(f"Searching for businesses with keyword: '{keyword}' in {location}")
    # Search for businesses using SearchAPI.io
    businesses = search_business_with_search_api(keyword, location=location, max_results=max_results)
    print(f"Found {len(businesses)} businesses matching the keyword")
    return businesses
