import requests
import time
import openai
import json

# === GLOBAL API KEYS ===
api_key = None
openai_api_key = None


# === INIT API KEYS ===
def init_api_key(key):
    """Initialize the Google Maps API key"""
    global api_key
    api_key = key
    return key


def init_openai_key(key):
    """Initialize OpenAI API key"""
    global openai_api_key
    openai.api_key = key
    return key


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
        raise ValueError("API key not initialized. Call init_api_key first.")
    return api_key


# === GET PLACE DETAILS ===
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


# === GET REVIEWS FOR A PLACE ===
def get_place_reviews(place_id, max_reviews=20):
    fields = ["review", "name", "rating", "user_ratings_total", "formatted_address", "types", "url"]
    place_details = get_place_details(place_id, fields=fields)
    reviews = place_details.get("reviews", [])
    return reviews[:max_reviews]


# === SEARCH VIA SEARCH API (e.g. SerpAPI) ===
def search_business_with_search_api(keyword, api_key_searchapi, location="Indonesia", max_results=5):
    search_url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_maps",
        "q": keyword,
        "type": "search",
        "location": location,
        "api_key": api_key_searchapi
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
                "gps_coordinates": biz.get("gps_coordinates"),
                "rating": biz.get("rating"),
                "reviews_count": biz.get("reviews"),
                "google_maps_url": biz.get("link")
            })

        return businesses

    except Exception as e:
        raise RuntimeError(f"Search API failed: {str(e)}")


# === OPENAI: SUMMARIZE & EXTRACT KEYWORDS ===
def summarize_and_extract_keywords(reviews):
    if not openai.api_key:
        raise ValueError("OpenAI API key not initialized. Call init_openai_key first.")

    review_texts = [r.get("text", "") for r in reviews if r.get("text")]
    joined_reviews = "\n".join(review_texts[:10])

    prompt = f"""
    I have the following customer reviews:\n{joined_reviews}\n
    Please provide:
    1. A concise summary of overall customer sentiment and experiences.
    2. A list of key topics and keywords mentioned by customers.
    Format your response in JSON with 'summary' and 'keywords' keys.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
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
def scrape_business_data_by_keyword(keyword, api_key_searchapi, max_places=5, max_reviews_per_place=10):
    all_data = []
    businesses = search_business_with_search_api(keyword, api_key_searchapi, max_results=max_places)

    for biz in businesses:
        place_id = biz.get("place_id")
        if not place_id:
            continue

        details = get_place_details(place_id, fields=[
            "name", "place_id", "rating", "formatted_address", "types", "url"
        ])
        reviews = get_place_reviews(place_id, max_reviews=max_reviews_per_place)

        try:
            analysis = summarize_and_extract_keywords(reviews)
        except Exception as e:
            analysis = {"summary": None, "keywords": [], "error": str(e)}

        all_data.append({
            "business": details,
            "reviews": reviews,
            "analysis": analysis
        })

    return all_data
