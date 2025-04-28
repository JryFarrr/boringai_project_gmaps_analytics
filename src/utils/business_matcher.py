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

def search_reviews_for_keywords(place_details, keywords):
    """
    Search reviews for specified keywords and return detailed results
    
    Args:
        place_details (dict): Dictionary containing place details with reviews
        keywords (str): Comma-separated keywords to search for
        
    Returns:
        dict: Dictionary with keyword counts and detailed matches
    """
    try:
        # Add debugging
        print(f"Searching for keywords: {keywords}")
        
        # Validate inputs
        if not isinstance(place_details, dict):
            print(f"Warning: place_details is not a dictionary. Type: {type(place_details)}")
            return {"matches": {}, "match_percentage": 0, "matched_reviews": []}
            
        if not isinstance(keywords, str):
            print(f"Warning: keywords is not a string. Type: {type(keywords)}")
            keywords = str(keywords) if keywords else ""
        
        # Split keywords and clean them up
        keyword_list = [k.strip().lower() for k in keywords.split(',') if k.strip()]
        if not keyword_list:
            print("No valid keywords found after parsing")
            return {"matches": {}, "match_percentage": 0, "matched_reviews": []}
            
        print(f"Parsed keywords: {keyword_list}")
            
        keyword_matches = {}
        matched_reviews = []
        reviews = place_details.get("reviews", [])
        
        if not isinstance(reviews, list):
            print(f"Warning: reviews is not a list. Type: {type(reviews)}")
            return {"matches": {}, "match_percentage": 0, "matched_reviews": []}
        
        print(f"Total reviews to search: {len(reviews)}")
        
        # Track which reviews match which keywords
        review_keyword_matches = {}
        
        # Improved word matching with word boundaries
        import re
        
        for keyword in keyword_list:
            count = 0
            matching_reviews = []
            # Create a regex pattern that matches the keyword as a whole word
            # This will match "cozy" but not "cozyness" 
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            
            for i, review in enumerate(reviews):
                try:
                    if not isinstance(review, dict):
                        print(f"Warning: review is not a dictionary. Type: {type(review)}")
                        continue
                        
                    review_text = review.get("text", "")
                    if not isinstance(review_text, str):
                        print(f"Warning: review text is not a string. Type: {type(review_text)}")
                        review_text = str(review_text) if review_text else ""
                    
                    # Debug output for the first few reviews
                    if i < 3:  # Just check the first 3 reviews for debugging
                        print(f"Review {i} text: {review_text[:50]}...")  # First 50 chars
                        print(f"Checking for '{keyword}' in review {i}")
                    
                    # Option 1: Simple substring match (case insensitive)
                    # if keyword.lower() in review_text.lower():
                    
                    # Option 2: Regex match with word boundaries (preferred for accurate matching)
                    if pattern.search(review_text):
                        count += 1
                        matching_reviews.append(i)  # Store index of matching review
                        
                        if i < 3:  # Debug
                            print(f"✓ Match found for '{keyword}' in review {i}")
                        
                        # Track this review matched this keyword
                        if i not in review_keyword_matches:
                            review_keyword_matches[i] = []
                        review_keyword_matches[i].append(keyword)
                    elif i < 3:  # Debug
                        print(f"✗ No match for '{keyword}' in review {i}")
                        
                except Exception as e:
                    print(f"Error processing review {i} for keywords: {str(e)}")
                    continue
            
            keyword_matches[keyword] = {
                "count": count,
                "matching_review_indices": matching_reviews
            }
            print(f"Keyword '{keyword}' found in {count} reviews")
        
        # Calculate overall match percentage based on how many reviews matched any keyword
        total_reviews = len(reviews)
        matched_review_count = len(review_keyword_matches)
        match_percentage = (matched_review_count / total_reviews * 100) if total_reviews > 0 else 0
        
        # Create list of matched reviews with their matching keywords
        for review_idx, matched_keywords in review_keyword_matches.items():
            if review_idx < len(reviews):
                review = reviews[review_idx]
                matched_reviews.append({
                    "review_text": review.get("text", ""),
                    "author": review.get("author_name", "Unknown"),
                    "rating": review.get("rating", 0),
                    "date": review.get("time", ""),
                    "matched_keywords": matched_keywords
                })
        
        result = {
            "matches": keyword_matches,
            "match_percentage": round(match_percentage, 2),
            "matched_reviews": matched_reviews
        }
        
        print(f"Final results: {matched_review_count} of {total_reviews} reviews matched keywords ({match_percentage:.2f}%)")
        return result
        
    except Exception as e:
        print(f"Error in search_reviews_for_keywords: {str(e)}")
        return {"matches": {}, "match_percentage": 0, "matched_reviews": []}
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
        "rating": 25,          # Reduced from 30% to make room for address
        "reviews": 20,
        "price_range": 15,
        "business_hours": 15,
        "keywords": 15,        # Reduced from 20% to make room for address
        "address": 10          # New weight for address matching
    }
    
    # Adjust score based on rating (weight: 25%)
    max_rating = 5.0
    min_required_rating = parameters.get("min_rating", 0)
    if place.get("rating", 0) >= min_required_rating:
        rating_factor = min(1.0, place.get("rating", 0) / max_rating)
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
    if parameters.get("keywords", "") and "keyword_matches" in place:
        keyword_match_percentage = place["keyword_matches"].get("match_percentage", 0)
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