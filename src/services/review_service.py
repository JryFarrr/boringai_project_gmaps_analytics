from src.services.api_clients.factory import create_client
from src.utils.business_matcher import extract_key_themes
from flask import current_app
from src.services.google_maps_service import get_place_reviews

def generate_review_summaries(positive_reviews, negative_reviews, keywords=""):
    """
    Generates summaries for both positive and negative reviews
    
    Args:
        positive_reviews (list): List of positive review texts
        negative_reviews (list): List of negative review texts
        keywords (str): Optional keywords to count in reviews
        
    Returns:
        dict: Dictionary containing positive and negative summaries and keyword match
    """
    # Tambahkan log di awal fungsi
    current_app.logger.info(f"generate_review_summaries called with keywords: '{keywords}'")
    current_app.logger.info(f"Number of reviews: positive={len(positive_reviews)}, negative={len(negative_reviews)}")
    
    result = {}
    
    # Get positive review summary
    if positive_reviews:
        result["positive"] = generate_review_summary(positive_reviews, "positive")
    
    # Get negative review summary
    if negative_reviews:
        result["negative"] = generate_review_summary(negative_reviews, "negative")
    
    # Calculate keyword match regardless of whether explicit keywords are provided
    # This ensures keywordMatch is always in the result
    all_reviews = []
    all_reviews.extend(positive_reviews)
    all_reviews.extend(negative_reviews)
    review_count = len(all_reviews)
    
    if keywords:
        # Tambahkan log sebelum mencari keywords
        current_app.logger.info(f"Searching for keywords: '{keywords}'")
        
        # Count keywords and add to result
        result["keywordMatch"] = count_keywords_in_reviews(all_reviews, keywords)
        
        # Tambahkan log setelah menghitung keywords
        current_app.logger.info(f"Keyword match result: {result.get('keywordMatch', 'Not found')}")
    else:
        # Provide default value when no keywords specified
        current_app.logger.warning("No keywords provided, adding default keywordMatch")
        result["keywordMatch"] = f"Keywords not found"
    
    # Fallback mechanism in case count_keywords_in_reviews fails
    if "keywordMatch" not in result:
        current_app.logger.warning("keywordMatch missing, adding fallback calculation")
        keyword_count = 0
        
        if keywords and review_count > 0:
            # Split keywords if multiple (comma separated)
            keyword_list = [k.strip().lower() for k in keywords.split(',')]
            current_app.logger.info(f"Fallback - Keyword list: {keyword_list}")
            
            # Search in all reviews
            for review in all_reviews:
                current_app.logger.debug(f"Checking review: {review[:50]}...")
                for keyword in keyword_list:
                    if keyword.lower() in review.lower():  # Case insensitive search
                        keyword_count += 1
                        current_app.logger.debug(f"Found keyword '{keyword}' in review")
        
        result["keywordMatch"] = f"{keyword_count} keywords found from {review_count} reviews"
    
    # Tambahkan log untuk hasil akhir
    current_app.logger.info(f"Final review summary result keys: {result.keys()}")
    current_app.logger.info(f"Final keywordMatch: {result.get('keywordMatch', 'Still missing!')}")
    
    return result

def count_keywords_in_reviews(reviews, keywords):
    """
    Counts how many reviews contain the specified keywords
    
    Args:
        reviews (list): List of review texts
        keywords (str): Comma-separated keywords to search for
        
    Returns:
        str: String describing the keyword match
    """
    keyword_count = 0
    review_count = len(reviews)
    
    # Split keywords if multiple (comma separated)
    keyword_list = [k.strip().lower() for k in keywords.split(',')]
    current_app.logger.info(f"Keyword list for counting: {keyword_list}")
    
    # Add detailed logging for each review and keyword
    for i, review in enumerate(reviews):
        review_matched = False
        current_app.logger.debug(f"Checking review #{i+1}: {review[:50]}...")
        
        for keyword in keyword_list:
            if keyword.lower() in review.lower():  # Case insensitive search
                keyword_count += 1
                review_matched = True
                current_app.logger.debug(f"Found keyword '{keyword}' in review #{i+1}")
                break  # Count each review only once
        
        if review_matched:
            current_app.logger.debug(f"Review #{i+1} matched at least one keyword")
    
    result = f"{keyword_count} keywords found from {review_count} reviews"
    current_app.logger.info(f"Keyword count result: {result}")
    return result

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

def get_reviews_for_place(place_id, max_reviews=100):
    """
    Get reviews for a place using SearchAPI.io
    
    Args:
        place_id (str): Google Place ID
        max_reviews (int): Maximum number of reviews to fetch (default: 100)
        
    Returns:
        dict: Dictionary with positive_reviews and negative_reviews separated
    """
    # Get reviews using SearchAPI.io
    all_reviews = get_place_reviews(place_id, max_reviews)
    
    # Separate into positive and negative reviews
    positive_reviews = [r['text'] for r in all_reviews if r.get('rating', 0) >= 4]
    negative_reviews = [r['text'] for r in all_reviews if r.get('rating', 0) < 4]
    
    return {
        "positive_reviews": positive_reviews,
        "negative_reviews": negative_reviews,
        "all_reviews": all_reviews
    }