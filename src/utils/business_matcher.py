from datetime import datetime
import re
import json
from src.services.api_clients.factory import create_client
from flask import current_app

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

def check_business_hours(place_hours, business_hours_constraint):
    """
    Check if place business hours fully contain the constraint using AI
    
    Args:
        place_hours (list): List of daily business hours (e.g., ["Monday: 8:00 AM - 10:00 PM", ...])
        business_hours_constraint (str): Business hours constraint (e.g., "6 pagi - 7 pagi", "6 AM - 7 AM", 
                                        or "12:00 WIB - 22:00 WIB")
    
    Returns:
        bool: True if the business is open during the entire constraint time range on at least one day, False otherwise
    """
    if not business_hours_constraint: 
        return True  # Default to True if no constraint

    try:
        # Create client for OpenAI
        client, headers, provider = create_client()

        # Prepare few-shot prompt for OpenAI
        prompt = f"""
        You are an assistant that checks if a given business hours constraint is FULLY contained within a provided business hours schedule.
        The constraint is a time range in either Indonesian, English, or 24-hour format with WIB (Indonesian Western Time).
        The schedule is a list of daily business hours in English format "Day: Start Time - End Time" (e.g., "Monday: 8:00 AM - 10:00 PM").
        
        Return "True" ONLY if the business is open for the ENTIRE constraint time range on at least one day in the schedule.
        Return "False" if any part of the constraint time range falls outside the business hours on all days.

        To compare times:
        1. Parse the constraint which may be in various formats:
           - For Indonesian: "pagi" = AM, "malam" = PM, "siang" = afternoon (typically 12:00 PM - 6:00 PM), "tengah malam" = 12:00 AM.
           - For English: Recognize "AM" and "PM" directly.
           - For 24-hour format with WIB: Convert directly (e.g., "12:00 WIB" = 12:00 PM = 12:00, "22:00 WIB" = 10:00 PM = 22:00).
           - Examples: "6 pagi" = 6:00 AM, "7 malam" = 7:00 PM, "9 AM" = 9:00 AM, "10 PM" = 10:00 PM, "14:00 WIB" = 2:00 PM.
        2. Convert all times (constraint and schedule) to 24-hour format for comparison.
        3. Check for FULL containment: The constraint range (start_constraint, end_constraint) is fully contained within the schedule range (start_schedule, end_schedule) if:
           - start_schedule <= start_constraint AND end_constraint <= end_schedule.
        4. Return "True" if at least one day's hours fully contain the constraint, otherwise "False".

        Examples:
        Constraint: "6 pagi - 7 pagi"
        Schedule: [
            "Monday: 8:00 AM - 10:00 PM",
            "Tuesday: 8:00 AM - 10:00 PM",
            "Wednesday: 8:00 AM - 10:00 PM",
            "Thursday: 8:00 AM - 10:00 PM",
            "Friday: 8:00 AM - 10:00 PM",
            "Saturday: 8:00 AM - 10:00 PM",
            "Sunday: 8:00 AM - 10:00 PM"
        ]
        Result: False
        Explanation: 6:00 AM - 7:00 AM (06:00 - 07:00) is not contained within 8:00 AM - 10:00 PM (08:00 - 22:00) for any day.

        Constraint: "9 AM - 10 AM"
        Schedule: [
            "Monday: 8:00 AM - 11:00 AM",
            "Tuesday: 8:00 AM - 10:00 PM",
            "Wednesday: 8:00 AM - 10:00 PM",
            "Thursday: 8:00 AM - 10:00 PM",
            "Friday: 8:00 AM - 10:00 PM",
            "Saturday: 8:00 AM - 10:00 PM",
            "Sunday: 8:00 AM - 10:00 PM"
        ]
        Result: True
        Explanation: 9:00 AM - 10:00 AM (09:00 - 10:00) is fully contained within 8:00 AM - 11:00 AM (08:00 - 11:00) on Monday and 8:00 AM - 10:00 PM (08:00 - 22:00) on other days.

        Constraint: "1 siang - 10 malam"
        Schedule: [
            "Monday: 8:00 AM - 10:00 PM",
            "Tuesday: 8:00 AM - 10:00 PM",
            "Wednesday: 8:00 AM - 10:00 PM",
            "Thursday: 8:00 AM - 10:00 PM",
            "Friday: 8:00 AM - 10:00 PM",
            "Saturday: 8:00 AM - 10:00 PM",
            "Sunday: 8:00 AM - 10:00 PM"
        ]
        Result: True
        Explanation: 1:00 PM (13:00) - 10:00 PM (22:00) is fully contained within 8:00 AM (08:00) - 10:00 PM (22:00) for all days.

        Constraint: "1 siang - 11 malam"
        Schedule: [
            "Monday: 8:00 AM - 10:00 PM",
            "Tuesday: 8:00 AM - 10:00 PM",
            "Wednesday: 8:00 AM - 10:00 PM",
            "Thursday: 8:00 AM - 10:00 PM",
            "Friday: 8:00 AM - 10:00 PM",
            "Saturday: 8:00 AM - 10:00 PM",
            "Sunday: 8:00 AM - 10:00 PM"
        ]
        Result: False
        Explanation: 1:00 PM - 11:00 PM (13:00 - 23:00) is not fully contained within 8:00 AM - 10:00 PM (08:00 - 22:00) for any day because the constraint extends past 10:00 PM.

        Constraint: "12:00 WIB - 22:00 WIB"
        Schedule: [
            "Monday: 8:00 AM - 10:00 PM",
            "Tuesday: 8:00 AM - 10:00 PM",
            "Wednesday: 8:00 AM - 10:00 PM",
            "Thursday: 8:00 AM - 10:00 PM",
            "Friday: 8:00 AM - 10:00 PM",
            "Saturday: 8:00 AM - 10:00 PM",
            "Sunday: 8:00 AM - 10:00 PM"
        ]
        Result: True
        Explanation: 12:00 WIB (12:00) - 22:00 WIB (22:00) is fully contained within 8:00 AM (08:00) - 10:00 PM (22:00) for all days.

        Constraint: "09:00 WIB - 21:00 WIB"
        Schedule: [
            "Monday: 8:00 AM - 10:00 PM",
            "Tuesday: 8:00 AM - 10:00 PM",
            "Wednesday: 8:00 AM - 10:00 PM",
            "Thursday: 8:00 AM - 10:00 PM",
            "Friday: 8:00 AM - 10:00 PM",
            "Saturday: 8:00 AM - 10:00 PM",
            "Sunday: 8:00 AM - 10:00 PM"
        ]
        Result: True
        Explanation: 09:00 WIB (09:00) - 21:00 WIB (21:00) is fully contained within 8:00 AM (08:00) - 10:00 PM (22:00) for all days.

        Constraint: "08:00 WIB - 23:00 WIB"
        Schedule: [
            "Monday: 8:00 AM - 10:00 PM",
            "Tuesday: 8:00 AM - 10:00 PM",
            "Wednesday: 8:00 AM - 10:00 PM",
            "Thursday: 8:00 AM - 10:00 PM",
            "Friday: 8:00 AM - 10:00 PM",
            "Saturday: 8:00 AM - 10:00 PM",
            "Sunday: 8:00 AM - 10:00 PM"
        ]
        Result: False
        Explanation: 08:00 WIB (08:00) - 23:00 WIB (23:00) is not fully contained within 8:00 AM (08:00) - 10:00 PM (22:00) for any day because the constraint extends past 10:00 PM (22:00).
        
        Constraint: "{business_hours_constraint}"
        Schedule: {json.dumps(place_hours)}
        Result:
        """

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that checks if business hours constraints are fully contained within business schedules in English and Indonesian."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1
        )

        # Extract and parse the result
        result = response.choices[0].message.content.strip()
        return result.lower() == "true"
    except Exception as e:
        current_app.logger.error(f"Error checking business hours: {str(e)}")
        return False  # Default to False if AI call fails


# Enhanced function with semantic matching capability
def search_reviews_for_keywords(place, keywords):
    """
    Search reviews for specified keywords with semantic matching capability
    
    Args:
        place (dict): Dictionary containing place details with reviews
        keywords (str): Comma-separated keywords to search for
        
    Returns:
        dict: Dictionary with keyword counts and detailed matches
    """
    # First, check if keywords are provided
    if not keywords:
        return {"match_percentage": 0, "matched_keywords": []}
    
    # Check if reviews exist in place object
    reviews = []
    
    # Look for reviews in different possible locations
    if "reviews" in place:
        reviews = place["reviews"]
    elif "positiveReviews" in place:
        reviews.extend(place.get("positiveReviews", []))
        reviews.extend(place.get("negativeReviews", []))
    
    # If no reviews found, return zero match
    if not reviews:
        return {"match_percentage": 0, "matched_keywords": []}

    keywords_list = [k.strip().lower() for k in keywords.split(",")]
    matches = []

    # First attempt exact matching
    for review in reviews:
        # Handle both string reviews and dictionary reviews
        review_text = ""
        if isinstance(review, str):
            review_text = review.lower()
        elif isinstance(review, dict) and "text" in review:
            review_text = review.get("text", "").lower()
        
        for keyword in keywords_list:
            if keyword in review_text and keyword not in matches:
                matches.append(keyword)
    
    # If we haven't matched all keywords, try semantic matching with AI
    unmatched_keywords = [k for k in keywords_list if k not in matches]
    
    if unmatched_keywords and reviews:
        try:
            # Create client for OpenAI
            client, headers, provider = create_client()
            
            # Prepare the reviews as text (limit to avoid token limits)
            reviews_text = "\n".join([
                isinstance(r, str) and r or r.get("text", "") 
                for r in reviews
            ])
            
            # Prepare prompt for semantic matching
            prompt = f"""
            I need to determine if these business reviews mention any concepts similar to these keywords: {', '.join(unmatched_keywords)}
            
            For example, if the keywords include "study friendly", I should match phrases like:
            - "suitable for study"
            - "good place to study"
            - "great for studying"
            - "perfect spot for students"
            - "ideal for working on assignments"
            
            Or if looking for "quiet atmosphere", I should match:
            - "peaceful environment"
            - "not noisy"
            - "calm ambiance" 
            - "serene setting"
            
            Please analyze the reviews below and return a JSON object in this format:
            {{
                "semantic_matches": [
                    {{
                        "keyword": "original_keyword",
                        "found": true/false,
                        "similar_phrases": ["phrase found in review"]
                    }}
                ]
            }}
            
            Reviews:
            {reviews_text}
            """
            
            # Call OpenAI API with JSON mode enabled
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that analyzes business reviews for semantic keyword matches."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=500
            )
            
            # Extract and parse semantic matches
            semantic_matches = json.loads(response.choices[0].message.content)
            
            # Add semantic matches to our matches list
            for match in semantic_matches.get("semantic_matches", []):
                if match.get("found", False) and match.get("keyword") not in matches:
                    matches.append(match.get("keyword"))
                    # Optional: store the similar phrases found for reference
                    if not hasattr(place, "semantic_keyword_details"):
                        place["semantic_keyword_details"] = {}
                    place["semantic_keyword_details"][match.get("keyword")] = match.get("similar_phrases", [])
                    
        except Exception as e:
            current_app.logger.error(f"Error in semantic keyword matching: {str(e)}")
            # Continue with exact matches only if semantic matching fails
    
    # Calculate match as discrete fraction: matched/total keywords
    total_keywords = len(keywords_list)
    matched_keywords = len(matches)
    
    if matched_keywords == 0:
        match_percentage = 0
    # Otherwise calculate based on matches/total
    elif total_keywords > 0:
        # Each keyword represents a discrete fraction of 100%
        match_percentage = (matched_keywords / total_keywords) * 100
    else:
        match_percentage = 0

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
        client, headers, provider = create_client()
        
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
    
def calculate_match_percentage(place, parameters):
    """
    Calculate match percentage based on various parameters including address
    
    Args:
        place (dict): Place object with relevant data
        parameters (dict): Parameters for matching
    
    Returns:
        float: Match percentage (0-100)
    """
    # Start with base score of 100
    score = 100
    
    # Define weights for different factors (total should be 100%)
    weights = {
        "rating": 25,
        "reviews": 20,
        "price_range": 15,
        "business_hours": 15,
        "keywords": 15,
        "address": 10
    }
    
    # CRITICAL CHECK: If keywords were specified but none found, return 0% immediately
    if parameters.get("keywords", ""):
        keyword_match_found = False
        
        # Check in keyword_matches dictionary
        if "keyword_matches" in place:
            if place["keyword_matches"].get("matched_keywords", []):
                keyword_match_found = True
        
        # Check in keywordMatch string
        elif "keywordMatch" in place:
            if "0 keywords found" not in place["keywordMatch"]:
                keyword_match_found = True
        
        # If keywords were specified and NONE found, return 0%
        if not keyword_match_found:
            return 0.0  # Return exactly 0%
    
    # [Rest of the function remains the same...]
    
    # Adjust score based on rating (weight: 25%)
    max_rating = 5.0
    min_required_rating = parameters.get("min_rating", 0)
    if min_required_rating > 0:
        place_rating = place.get("rating", 0)
        if place_rating < min_required_rating:
            score -= weights["rating"]  # Full penalty if below minimum
        else:
            rating_factor = min(1.0, place_rating / max_rating)
            score -= (1 - rating_factor) * weights["rating"]
    
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
            score -= (1 - review_factor) * weights["reviews"]
        else:
            score -= weights["reviews"]  # Full penalty for 0 reviews
    
    # Adjust score based on price level match (weight: 15%)
    if parameters.get("price_range", "") and "price_match" in place:
        if not place["price_match"]:
            score -= weights["price_range"]
    
    # Adjust score based on business hours match (weight: 15%)
    if parameters.get("business_hours", "") != "anytime" and "hours_match" in place:
        if not place["hours_match"]:
            score -= weights["business_hours"]
    
    # Adjust score based on keyword matches (weight: 15%)
    # We already checked this above and returned 0 if no matches
    # So here we handle partial matches only
    if parameters.get("keywords", ""):
        keyword_match_percentage = 0
        
        if "keyword_matches" in place:
            keyword_match_percentage = place["keyword_matches"].get("match_percentage", 0)
        elif "keywordMatch" in place and "0 keywords found" not in place["keywordMatch"]:
            import re
            match = re.search(r'(\d+)%', place["keywordMatch"])
            if match:
                keyword_match_percentage = int(match.group(1))
        
        score -= (1 - (keyword_match_percentage / 100)) * weights["keywords"]
    
    # Adjust score based on address match (weight: 10%)
    if parameters.get("address", "") and place.get("address", ""):
        # Simple match check - can be enhanced with more sophisticated address matching
        address_match_factor = 0
        
        # Check if the parameter address is contained within the place address
        if parameters["address"].lower() in place["address"].lower():
            address_match_factor = 1.0  # Full match
        else:
            # Partial matching using address components
            param_address_parts = set([part.lower() for part in parameters["address"].split() if len(part) > 2])
            place_address_parts = set([part.lower() for part in place["address"].split() if len(part) > 2])
            
            # Calculate overlap ratio
            if param_address_parts:
                common_parts = param_address_parts.intersection(place_address_parts)
                address_match_factor = len(common_parts) / len(param_address_parts)
        
        score -= (1 - address_match_factor) * weights["address"]
    
    return max(0, min(100, score))