from src.services.api_clients.factory import create_client
from src.utils.business_matcher import extract_key_themes
from flask import current_app
from src.services.google_maps_service import get_place_reviews # Assuming this fetches reviews, but we need total count and keyword search separately
import requests
import os
from src.config.config import SEARCHAPI_API_KEY # Import API Key

def get_keyword_match_count_from_searchapi(place_id, keywords, api_key):
    """
    Uses SearchApi.io to find the count of reviews matching keywords and the total review count.

    Args:
        place_id (str): Google Place ID.
        keywords (str): Comma-separated keywords to search for.
        api_key (str): SearchApi.io API key.

    Returns:
        tuple: (matching_review_count, total_review_count)
               Returns (-1, -1) if an error occurs. Returns (0, 0) if keywords/place_id missing.
    """
    if not keywords or not place_id:
        current_app.logger.warning("Keywords or Place ID missing for SearchAPI keyword search.")
        return 0, 0 # Return 0, 0 if no keywords or place_id

    search_query = keywords.split(",")[0].strip()
    current_app.logger.info(f"Using SearchAPI with place_id: {place_id}, search_query: ")

    base_url = "https://www.searchapi.io/api/v1/search"
    params = {
        "api_key": api_key,
        "engine": "google_maps_reviews",
        "place_id": place_id,
        "search_query": search_query,
        "hl": "en",
        "num": 20 # Fetch up to 20 matching reviews to determine n
    }

    try:
        response = requests.get(base_url, params=params, timeout=45)
        response.raise_for_status()
        data = response.json()

        matching_review_count = len(data.get("reviews", [])) # n
        total_review_count = data.get("place_result", {}).get("reviews", -1) # b, use -1 if unavailable

        # Handle case where place_result might be missing entirely
        if total_review_count == -1 and "place_result" not in data:
             current_app.logger.warning(f"SearchAPI did not return place_result for {place_id}")

        current_app.logger.info(f"SearchAPI Result: n={matching_review_count}, b={total_review_count}")
        return matching_review_count, total_review_count

    except requests.exceptions.Timeout:
        current_app.logger.error(f"SearchApi.io request timed out for place_id: {place_id}")
        return -1, -1 # Indicate error with -1
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"SearchApi.io request failed for place_id {place_id}: {e}")
        return -1, -1 # Indicate error with -1
    except Exception as e:
        current_app.logger.error(f"Error processing SearchApi.io response for place_id {place_id}: {e}")
        return -1, -1 # Indicate error with -1

def generate_review_summaries(positive_reviews, negative_reviews, keywords="", place_id=None):
    """
    Generates summaries for reviews and gets keyword match data using SearchApi.io.

    Args:
        positive_reviews (list): List of positive review texts.
        negative_reviews (list): List of negative review texts.
        keywords (str): Optional keywords to count in reviews.
        place_id (str): Optional Google Place ID required for keyword search via SearchApi.io.

    Returns:
        dict: Dictionary containing:
              - positive (str): Summary of positive reviews.
              - negative (str): Summary of negative reviews.
              - keywordMatch (str): Formatted string describing keyword match.
              - keywordCountN (int): Number of reviews matching keyword (-1 on error).
              - keywordTotalB (int): Total reviews for the place (-1 if unavailable/error).
    """
    current_app.logger.info(f"generate_review_summaries called with keywords: ")
    current_app.logger.info(f"Number of scraped reviews: positive={len(positive_reviews)}, negative={len(negative_reviews)}")

    result = {
        "positive": "",
        "negative": "",
        "keywordMatch": "keyword match information unavailable", # Default string
        "keywordCountN": 0, # Default count n
        "keywordTotalB": 0  # Default count b
    }

    # Get positive review summary
    if positive_reviews:
        result["positive"] = generate_review_summary(positive_reviews, "positive")

    # Get negative review summary
    if negative_reviews:
        result["negative"] = generate_review_summary(negative_reviews, "negative")

    # --- REVISED Keyword Match Logic --- 
    n = 0
    b = 0
    keyword_match_status = "unavailable"

    if keywords and place_id:
        current_app.logger.info(f"Attempting keyword match via SearchAPI for place_id: {place_id} with keywords: ")
        api_key = SEARCHAPI_API_KEY or os.getenv("SEARCHAPI_KEY")
        if not api_key:
            current_app.logger.error("SearchAPI API Key is not configured!")
            keyword_match_status = "API key missing"
            n = -1 # Indicate error
            b = -1
        else:
            n, b = get_keyword_match_count_from_searchapi(place_id, keywords, api_key)
            if n == -1: # Check if SearchAPI call failed
                keyword_match_status = "SearchAPI error"
            elif b == -1:
                 keyword_match_status = "total count unavailable"
            else:
                 keyword_match_status = "success"
    elif not keywords:
        current_app.logger.warning("No keywords provided for keyword match.")
        keyword_match_status = "keywords not specified"
    elif not place_id:
        current_app.logger.warning("No place_id provided for SearchAPI keyword match.")
        keyword_match_status = "place_id missing"

    # Store numeric results directly
    result["keywordCountN"] = n
    result["keywordTotalB"] = b

    # Format the keywordMatch string based on n, b, and status
    if keyword_match_status == "success":
        if b > 0:
            result["keywordMatch"] = f"{n} reviews contain keywords out of {b} total reviews" if n > 0 else f"keyword not found in {b} total reviews"
        else: # Should ideally not happen if status is success, but handle defensively
             result["keywordMatch"] = f"{n} reviews contain keywords (total count unavailable)" if n > 0 else f"keyword not found (total count unavailable)"
    elif keyword_match_status == "total count unavailable":
         result["keywordMatch"] = f"{n} reviews contain keywords (total count unavailable)" if n > 0 else f"keyword not found (total count unavailable)"
    else: # Handle errors or missing info
        result["keywordMatch"] = f"keyword search {keyword_match_status}"

    current_app.logger.info(f"Final keyword match data: n={result["keywordCountN"]}, b={result["keywordTotalB"]}, string=")
    # --- END REVISED --- 

    return result

# Removed the old count_keywords_in_reviews function as it's replaced by SearchAPI logic

def generate_review_summary(reviews, review_type="positive", max_length=200):
    """
    Generate a concise summary of reviews using OpenAI

    Args:
        reviews (list): List of review texts
        review_type (str): Type of reviews ("positive" or "negative")
        max_length (int): Maximum length of the summary

    Returns:
        str: Concise summary of the reviews
    """
    if not reviews:
        return ""

    # Limit to first 5 reviews to keep token count reasonable
    reviews_text = "\n\n".join(reviews[:5])

    try:
        # Create client for OpenAI
        client, headers, provider = create_client()

        # Prepare prompt for OpenAI
        prompt = f"""Summarize the following {review_type} reviews for a business.
        Focus on extracting the key points, recurring themes, and specific elements that customers mention.
        Keep your summary concise (maximum {max_length} characters) and focus on actionable insights.

        Reviews:
        {reviews_text}
        """

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes business reviews concisely."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150  # Increased token count for better summaries
        )

        # Extract and return the summary
        summary = response.choices[0].message.content.strip()

        # Ensure summary is within the max length
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."

        return summary

    except Exception as e:
        print(f"Error generating review summary: {str(e)}")

        # Fallback to basic summarization if API call fails
        summary_items = []
        for i, review in enumerate(reviews[:3]):
            summary_items.append(review[:100] + ("..." if len(review) > 100 else ""))
        return " | ".join(summary_items)

def extract_key_themes_from_reviews(reviews):
    """
    Extracts key themes from a list of review texts

    Args:
        reviews (list): List of review texts

    Returns:
        list: List of key themes extracted from reviews
    """
    if not reviews:
        return []

    return extract_key_themes(reviews)

# Note: get_reviews_for_place might still be used elsewhere for scraping, 
# but keyword counting now uses get_keyword_match_count_from_searchapi.
def get_reviews_for_place(place_id, max_reviews=100):
    """
    Get reviews for a place using the configured service (e.g., SearchAPI.io via google_maps_service).
    This function primarily fetches reviews for summarization/scraping purposes.

    Args:
        place_id (str): Google Place ID
        max_reviews (int): Maximum number of reviews to fetch (default: 100)

    Returns:
        dict: Dictionary with positive_reviews, negative_reviews, and all_reviews separated
    """
    # Get reviews using the existing service (likely SearchAPI.io via google_maps_service)
    all_reviews_data = get_place_reviews(place_id, max_reviews) # Assumes this returns a list of review dicts

    # Separate into positive and negative reviews based on rating
    positive_reviews = [r["text"] for r in all_reviews_data if r.get("rating", 0) >= 4 and "text" in r]
    negative_reviews = [r["text"] for r in all_reviews_data if r.get("rating", 0) < 4 and "text" in r]

    return {
        "positive_reviews": positive_reviews,
        "negative_reviews": negative_reviews,
        "all_reviews": all_reviews_data # Return the original structure if needed elsewhere
    }

