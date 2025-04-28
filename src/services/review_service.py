from src.services.api_clients.factory import create_client
from src.utils.business_matcher import extract_key_themes
from flask import current_app
from src.services.google_maps_service import get_place_reviews

def generate_review_summaries(positive_reviews, negative_reviews, keywords=""):
    """
    Generate summaries for positive and negative reviews and count keyword occurrences
    
    Args:
        positive_reviews (list): List of positive review texts
        negative_reviews (list): List of negative review texts
        keywords (str): Keywords to search for in reviews (comma-separated)
        
    Returns:
        dict: Dictionary with positive and negative summaries and keyword match info
    """
    result = {}
    
    try:
        # Validate inputs
        if not isinstance(positive_reviews, list):
            print(f"Warning: positive_reviews is not a list. Type: {type(positive_reviews)}")
            positive_reviews = []
            
        if not isinstance(negative_reviews, list):
            print(f"Warning: negative_reviews is not a list. Type: {type(negative_reviews)}")
            negative_reviews = []
            
        if not isinstance(keywords, str):
            print(f"Warning: keywords is not a string. Type: {type(keywords)}")
            keywords = str(keywords) if keywords else ""
        
        # Generate positive review summary
        try:
            if positive_reviews:
                result["positive"] = generate_review_summary(positive_reviews, "positive")
            else:
                result["positive"] = "No positive reviews available."
        except Exception as e:
            print(f"Error generating positive review summary: {str(e)}")
            result["positive"] = "Error generating positive review summary."
        
        # Generate negative review summary
        try:
            if negative_reviews:
                result["negative"] = generate_review_summary(negative_reviews, "negative")
            else:
                result["negative"] = "No negative reviews available."
        except Exception as e:
            print(f"Error generating negative review summary: {str(e)}")
            result["negative"] = "Error generating negative review summary."
        
        # Count keyword occurrences if keywords are provided
        if keywords:
            try:
                keyword_list = [k.strip().lower() for k in keywords.split(',') if k.strip()]
                if keyword_list:
                    keyword_matches = {}
                    all_reviews = positive_reviews + negative_reviews
                    
                    for keyword in keyword_list:
                        count = 0
                        for review in all_reviews:
                            if not isinstance(review, str):
                                print(f"Warning: review is not a string. Type: {type(review)}")
                                continue
                                
                            if keyword in review.lower():
                                count += 1
                        keyword_matches[keyword] = count
                    
                    # Add keyword match summary
                    result["keywordMatch"] = format_keyword_matches(keyword_matches)
            except Exception as e:
                print(f"Error processing keywords: {str(e)}")
                result["keywordMatch"] = "Error processing keywords."
        
        return result
        
    except Exception as e:
        print(f"Error in generate_review_summaries: {str(e)}")
        return {
            "positive": "Error generating summaries.",
            "negative": "Error generating summaries.",
            "keywordMatch": "Error processing keywords."
        }

def format_keyword_matches(keyword_matches):
    """Format keyword matches into a readable string"""
    try:
        if not keyword_matches:
            return "No keywords specified"
            
        matches = []
        for keyword, count in keyword_matches.items():
            matches.append(f"{keyword}: {count} mentions")
        
        return ", ".join(matches)
    except Exception as e:
        print(f"Error formatting keyword matches: {str(e)}")
        return "Error processing keywords"

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

def extract_reviews_by_sentiment(reviews):
    """
    Separates reviews into positive and negative lists based on their rating.
    
    Args:
        reviews (list): List of review dictionaries
        
    Returns:
        tuple: (positive_reviews, negative_reviews)
    """
    positive_reviews = []
    negative_reviews = []
    
    try:
        # Check if reviews is None or empty
        if not reviews:
            return [], []
        
        # Check if reviews is a list
        if not isinstance(reviews, list):
            print(f"Warning: reviews is not a list. Type: {type(reviews)}")
            return [], []
        
        for i, review in enumerate(reviews):
            try:
                # Skip if review is not a dictionary
                if not isinstance(review, dict):
                    print(f"Warning: review at index {i} is not a dictionary. Type: {type(review)}")
                    continue
                    
                # Extract rating - default to 0 if not found or invalid
                try:
                    rating = float(review.get('rating', 0))
                except (ValueError, TypeError):
                    print(f"Warning: invalid rating in review at index {i}. Using default: 0")
                    rating = 0
                
                # Extract review text
                review_text = review.get('text', '')
                if not isinstance(review_text, str):
                    print(f"Warning: review text at index {i} is not a string. Converting to string.")
                    review_text = str(review_text)
                
                # Typically ratings 4-5 are positive, 1-3 are negative
                if rating >= 4:
                    positive_reviews.append(review_text)
                else:
                    negative_reviews.append(review_text)
                    
            except Exception as e:
                print(f"Error processing review at index {i}: {str(e)}")
                continue
                
        return positive_reviews, negative_reviews
        
    except Exception as e:
        print(f"Error in extract_reviews_by_sentiment: {str(e)}")
        return [], []