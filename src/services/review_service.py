from src.services.api_clients.factory import create_client
from src.utils.business_matcher import extract_key_themes
from flask import current_app
def generate_review_summaries(positive_reviews, negative_reviews, keywords=""):
    """
    Processes reviews to provide keyword match information and separate positive/negative reviews.
    Review summarization is explicitly excluded.
    
    Args:
        positive_reviews (list): List of positive review texts (already filtered by keywords if provided).
        negative_reviews (list): List of negative review texts (already filtered by keywords if provided).
        keywords (str): Keywords used to filter reviews directly via the API.
                        This parameter is used to determine the 'keywordMatch' message.
        
    Returns:
        dict: Dictionary containing separated positive and negative review lists,
              and keyword match information.
    """
    current_app.logger.info(f"generate_review_summaries called with keywords: '{keywords}' (no summarization requested)")
    current_app.logger.info(f"Number of reviews received: positive={len(positive_reviews)}, negative={len(negative_reviews)}")
    
    result = {}
    
    # Directly include the separated positive and negative reviews
    result["positive_reviews"] = positive_reviews
    result["negative_reviews"] = negative_reviews
    
    # Determine keywordMatch based on whether keywords were provided
    # and implicitly, whether the API call used search_query.
    all_filtered_reviews_count = len(positive_reviews) + len(negative_reviews)

    if keywords:
        # If keywords were provided, we assume get_reviews_for_place already filtered by them.
        # The count reflects how many reviews were returned by the API for that search_query.
        if all_filtered_reviews_count > 0:
            result["keywordMatch"] = f"{all_filtered_reviews_count} reviews found containing '{keywords}' (filtered by API)."
        else:
            # If keywords were given but the API returned no reviews, it means "not found"
            result["keywordMatch"] = f"keyword not found"
    else:
        # If no keywords were provided, the keywordMatch is explicitly "not found"
        result["keywordMatch"] = "keyword not found"

    current_app.logger.info(f"Final review processing result: {result.keys()}")
    return result

# --- The `count_keywords_in_reviews` function is no longer used by generate_review_summaries,
#     but it's included below in case it's used elsewhere or for local debugging. ---

def count_keywords_in_reviews(reviews, keywords):
    """
    Counts how many reviews contain the specified keywords locally.
    This function is kept for completeness but is not the primary method
    for keyword matching when using SearchAPI.io's `search_query`.
    """
    matching_reviews_count = 0
    review_count = len(reviews)
    
    if not keywords: # If no keywords, nothing to count
        return "keyword not found"

    keyword_list = [k.strip().lower() for k in keywords.split(',')]
    current_app.logger.info(f"Local keyword counting initiated for: {keyword_list}")
    
    for i, review in enumerate(reviews):
        review_matched = False
        current_app.logger.debug(f"Checking review #{i+1}: {review[:50]}...")
        
        for keyword in keyword_list:
            if keyword.lower() in review.lower():
                matching_reviews_count += 1
                review_matched = True
                current_app.logger.debug(f"Found keyword '{keyword}' in review #{i+1}")
                break
        
        if review_matched:
            current_app.logger.debug(f"Review #{i+1} matched at least one keyword locally.")
    
    if matching_reviews_count > 0:
        result = f"{matching_reviews_count} reviews contain keywords out of {review_count} total reviews (local count)."
    else:
        result = "keyword not found"
    
    current_app.logger.info(f"Local keyword count result: {result}")
    return result

# --- The `generate_review_summary` function is REMOVED as per your request. ---

def extract_key_themes_from_reviews(reviews):
    """
    Extracts key themes from a list of review texts.
    
    Args:
        reviews (list): List of review texts.
        
    Returns:
        list: List of key themes extracted from reviews.
    """
    if not reviews:
        return []
    
    # Assuming extract_key_themes handles an empty list gracefully.
    return extract_key_themes(reviews)