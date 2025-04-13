from datetime import datetime
import re
import json
from src.services.api_clients.factory import create_client

# Fungsi-fungsi yang sudah ada tetap dipertahankan
def match_price_range(place_price_range, constraint_price_range):
    """
    Check if place price range matches the constraint price range
    
    Args:
        place_price_range (str): Price range of the place (e.g., "$", "$$", "$$$")
        constraint_price_range (str): Price range constraint (e.g., "$", "$$", "$$$")
    
    Returns:
        bool: True if matches, False otherwise
    """
    if not constraint_price_range:
        return True
    
    # If exact match is required
    if constraint_price_range == place_price_range:
        return True
        
    # If price range is specified as a range (e.g., "$-$$$")
    if "-" in constraint_price_range:
        min_price, max_price = constraint_price_range.split("-")
        
        # Convert price ranges to numeric values for comparison
        place_value = len(place_price_range)
        min_value = len(min_price)
        max_value = len(max_price)
        
        # Check if place value is within the range
        return min_value <= place_value <= max_value
        
    return False

def check_business_hours(place, business_hours_constraint):
    """
    Check if place business hours match the constraint
    
    Args:
        place (dict): Place object with opening_hours
        business_hours_constraint (str): Business hours constraint (e.g., "anytime", "weekdays", "weekends", "24hours")
    
    Returns:
        bool: True if matches, False otherwise
    """
    if business_hours_constraint == "anytime" or not business_hours_constraint:
        return True
        
    # If open_now check is required and available
    if business_hours_constraint == "open_now" and "opening_hours" in place and "open_now" in place["opening_hours"]:
        return place["opening_hours"]["open_now"]
    
    # If no opening hours data available, can't determine match
    if "opening_hours" not in place or "weekday_text" not in place["opening_hours"]:
        return True  # Default to True if no data
    
    weekday_text = place["opening_hours"]["weekday_text"]
    
    if business_hours_constraint == "24hours":
        # Check if all days have "24 hours" or similar wording
        return all("24 hours" in day.lower() or "open 24 hours" in day.lower() for day in weekday_text)
    
    elif business_hours_constraint == "weekdays":
        # Check if Monday to Friday have reasonable business hours
        weekday_pattern = re.compile(r'(monday|tuesday|wednesday|thursday|friday):', re.IGNORECASE)
        weekday_hours = [day for day in weekday_text if weekday_pattern.search(day)]
        return all("closed" not in day.lower() for day in weekday_hours)
    
    elif business_hours_constraint == "weekends":
        # Check if Saturday and Sunday have reasonable business hours
        weekend_pattern = re.compile(r'(saturday|sunday):', re.IGNORECASE)
        weekend_hours = [day for day in weekday_text if weekend_pattern.search(day)]
        return all("closed" not in day.lower() for day in weekend_hours)
    
    elif business_hours_constraint == "evenings":
        # Check if place is open after 5PM
        evening_pattern = re.compile(r'(\d{1,2}):00 PM–\d{1,2}', re.IGNORECASE)
        return any(evening_pattern.search(day) for day in weekday_text)
    
    return True  # Default to True for unknown constraints

def search_reviews_for_keywords(place, keywords):
    """
    Search place reviews for specific keywords
    
    Args:
        place (dict): Place object with reviews
        keywords (str): Keywords to search for, comma-separated
    
    Returns:
        dict: Dictionary with match percentage and matched keywords
    """
    if not keywords or "reviews" not in place or not place["reviews"]:
        return {"match_percentage": 0, "matched_keywords": []}
    
    keywords_list = [k.strip().lower() for k in keywords.split(",")]
    matches = []
    
    for review in place["reviews"]:
        review_text = review.get("text", "").lower()
        
        for keyword in keywords_list:
            if keyword in review_text and keyword not in matches:
                matches.append(keyword)
    
    match_percentage = round((len(matches) / len(keywords_list)) * 100, 2) if keywords_list else 0
    
    return {
        "match_percentage": match_percentage,
        "matched_keywords": matches
    }

def extract_key_themes(reviews, max_themes=5):
    """
    Extract key themes from reviews using OpenAI
    
    Args:
        reviews (list): List of review texts
        max_themes (int): Maximum number of themes to extract
    
    Returns:
        list: List of key themes
    """
    if not reviews:
        return []
    
    # Limit to first 10 reviews to keep token count reasonable
    reviews_text = "\n\n".join(reviews[:10])
    
    try:
        # Create client for OpenAI
        client, headers, provider = create_client(provider="openai")
        
        # Prepare prompt for OpenAI
        prompt = f"""Extract the {max_themes} most important themes or topics from these business reviews.
        Focus on recurring subjects, features, or aspects that customers frequently mention.
        Return ONLY a JSON array of strings, with each string being a key theme. Keep each theme concise (1-5 words).
        
        Reviews:
        {reviews_text}
        """
        
        # Call OpenAI API with JSON mode enabled
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data analyst that extracts key themes from business reviews."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=100
        )
        
        # Extract and return the themes
        themes_json = response.choices[0].message.content.strip()
        themes_data = json.loads(themes_json)
        
        # The API should return a JSON with a 'themes' key
        if isinstance(themes_data, dict) and "themes" in themes_data:
            return themes_data["themes"]
        # If it returns a direct array
        elif isinstance(themes_data, list):
            return themes_data
        # If the structure is different, try to extract anything that looks like themes
        else:
            for key, value in themes_data.items():
                if isinstance(value, list):
                    return value[:max_themes]
            return []
            
    except Exception as e:
        print(f"Error extracting key themes: {str(e)}")
        
        # Fallback if API call fails - simple word frequency analysis
        import re
        from collections import Counter
        
        # Extract words, filtering out common stop words
        stop_words = set(['the', 'and', 'is', 'in', 'it', 'to', 'was', 'for', 'on', 'with', 'at', 'by', 'of', 'this', 'that', 'a', 'an'])
        all_words = []
        
        for review in reviews:
            # Extract words and filter out non-alphanumeric characters
            words = re.findall(r'\b[a-zA-Z]{3,}\b', review.lower())
            # Filter out stop words
            filtered_words = [word for word in words if word not in stop_words]
            all_words.extend(filtered_words)
        
        # Get most common words
        word_counts = Counter(all_words)
        common_words = [word for word, count in word_counts.most_common(max_themes)]
        
        return common_words

def calculate_match_percentage_with_ai(place, parameters, reviews=None):
    """
    Calculate match percentage using OpenAI's analysis with improved error handling
    """
    try:
        # Create client for OpenAI
        client, headers, provider = create_client(provider="openai")
        
        # Simplify place data for OpenAI to reduce complexity
        place_data = {
            "name": place.get("name", ""),
            "rating": place.get("rating", 0),
            "total_reviews": place.get("user_ratings_total", 0),
            "price_level": "$" * place.get("price_level", 0) if "price_level" in place else None,
            "types": place.get("types", [])[:3],  # Limit to first 3 types
        }
        
        # Simplify constraints data
        constraints_data = {
            "min_rating": parameters.get("min_rating", 0),
            "min_reviews": parameters.get("min_reviews", 0),
            "price_range": parameters.get("price_range", ""),
            "business_hours": parameters.get("business_hours", "anytime"),
        }
        
        # Limit sample reviews to reduce token usage
        sample_reviews = ""
        if reviews and len(reviews) > 0:
            # Only use first 2 reviews and limit length
            limited_reviews = [review[:200] + "..." if len(review) > 200 else review for review in reviews[:2]]
            sample_reviews = "\n\n".join(limited_reviews)
        
        # Create a simplified prompt
        prompt = f"""Analyze this business and determine how well it matches the given constraints.
        
        Business: {json.dumps(place_data)}
        
        Constraints: {json.dumps(constraints_data)}
        
        {f'Sample Reviews: {sample_reviews}' if sample_reviews else ''}
        
        Return a JSON object with:
        1. match_percentage: A number from 0-100 indicating match quality
        2. analysis: Object with rating_factor, review_count_factor, price_factor, hours_factor, keyword_factor (all 0-1)
        3. reasoning: Brief explanation of the match percentage
        """
        
        print("Sending request to OpenAI with prompt length:", len(prompt))
        
        # Call OpenAI API with JSON mode enabled
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a business analyst AI that evaluates match percentages."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=500
        )
        
        # Extract and return the analysis
        result_json = response.choices[0].message.content.strip()
        
        # Debug
        print("OpenAI response received. Length:", len(result_json))
        print("First 100 chars of response:", result_json[:100])
        
        try:
            result = json.loads(result_json)
        except json.JSONDecodeError as json_err:
            print(f"JSON parsing error: {str(json_err)}")
            print(f"Raw response: {result_json}")
            raise ValueError(f"Failed to parse OpenAI response as JSON: {str(json_err)}")
            
        # Ensure result has expected structure
        if "match_percentage" not in result:
            print(f"Response missing match_percentage. Keys found: {list(result.keys())}")
            raise ValueError("Missing match_percentage in OpenAI response")
            
        # Ensure match_percentage is within range
        match_percentage = max(0, min(100, float(result["match_percentage"])))
        
        return match_percentage, result
        
    except Exception as e:
        import traceback
        print(f"Error calculating match percentage with AI: {str(e)}")
        print(f"Detailed traceback: {traceback.format_exc()}")
        
        # Fallback to traditional calculation
        match_percentage = calculate_match_percentage(place, parameters)
        fallback_analysis = {
            "match_percentage": match_percentage,
            "analysis": {
                "rating_factor": min(1.0, place.get("rating", 0) / 5.0),
                "review_count_factor": min(1.0, place.get("user_ratings_total", 0) / 100),
                "price_factor": 1.0 if place.get("price_match", True) else 0.0,
                "hours_factor": 1.0 if place.get("hours_match", True) else 0.0,
                "keyword_factor": place.get("keyword_matches", {}).get("match_percentage", 0) / 100
            },
            "reasoning": "Calculated using traditional algorithm due to specific AI service error: " + str(e)
        }
        
        return match_percentage, fallback_analysis
# Versi original yang tetap dipertahankan sebagai fallback
def calculate_match_percentage(place, parameters):
    """
    Calculate match percentage based on various parameters
    
    Args:
        place (dict): Place object with relevant data
        parameters (dict): Parameters for matching
    
    Returns:
        float: Match percentage (0-100)
    """
    # Start with base score of 100
    score = 100
    
    # Adjust score based on rating (weight: 30%)
    max_rating = 5.0
    min_required_rating = parameters.get("min_rating", 0)
    if place.get("rating", 0) >= min_required_rating:
        rating_factor = min(1.0, place.get("rating", 0) / max_rating)
        score -= (1 - rating_factor) * 30
    
    # Adjust score based on review count (weight: 20%)
    min_required_reviews = parameters.get("min_reviews", 0)
    if place.get("user_ratings_total", 0) >= min_required_reviews:
        # Use logarithmic scale to avoid extreme penalties for low review counts
        # but still reward places with more reviews
        import math
        review_count = place.get("user_ratings_total", 0)
        
        # Logarithmic scale: 0 reviews = 0%, 10 reviews = 60%, 100 reviews = 80%, 1000+ reviews = 100%
        if review_count > 0:
            review_factor = min(1.0, math.log10(review_count) / 3)
            score -= (1 - review_factor) * 20
        else:
            score -= 20  # Full penalty for 0 reviews
    
    # Adjust score based on price level match (weight: 15%)
    if parameters.get("price_range", "") and "price_match" in place:
        if not place["price_match"]:
            score -= 15
    
    # Adjust score based on business hours match (weight: 15%)
    if parameters.get("business_hours", "") != "anytime" and "hours_match" in place:
        if not place["hours_match"]:
            score -= 15
    
    # Adjust score based on keyword matches (weight: 20%)
    if parameters.get("keywords", "") and "keyword_matches" in place:
        keyword_match_percentage = place["keyword_matches"].get("match_percentage", 0)
        score -= (1 - (keyword_match_percentage / 100)) * 20
    
    return max(0, min(100, score))
