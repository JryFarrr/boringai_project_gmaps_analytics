import requests
import pandas as pd
import json
import time
from openai import OpenAI
from datetime import datetime
import re

class MapLeadsAI:
    def __init__(self, google_api_key, openrouter_api_key, referer_url="https://your-website.com", site_name="Map Leads AI"):
        """
        Initialize the MapLeadsAI system
        
        Args:
            google_api_key (str): Google Places API key
            openrouter_api_key (str): OpenRouter API key
            referer_url (str): Website URL for OpenRouter rankings
            site_name (str): Site name for OpenRouter rankings
        """
        self.google_api_key = google_api_key
        self.openrouter_api_key = openrouter_api_key
        self.referer_url = referer_url
        self.site_name = site_name
        
        # Initialize OpenRouter client
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key
        )
        
    def parse_prompt(self, prompt):
        """
        Parse the user prompt using OpenRouter to extract search parameters
        
        Args:
            prompt (str): User prompt in the specified format
            
        Returns:
            dict: Dictionary containing extracted search parameters
        """
        # Improved system prompt with clear structure, examples, and error handling guidance
        system_prompt = """You are an expert system for extracting structured business search parameters from user queries.

Your job is to analyze a search query and extract precise parameters for a business discovery system.

INPUT FORMAT:
The user will provide a query like this:
"Find a {business type or specific category} in {business location} that has a rating of at least {rating} and at least {number of reviews} number of reviews.
Additional Requirements:
- The business must have a price range of {price range}.
- The business operates at {business hours}.
- Business reviews and descriptions must include {specific keywords}."

OUTPUT FORMAT:
You must return ONLY a valid JSON object with these exact fields (no explanations or other text):
{
  "business_type": "The exact business type or category mentioned",
  "location": "The exact location mentioned", 
  "min_rating": float, // The minimum rating as a decimal number (e.g., 4.2)
  "min_reviews": int, // The minimum number of reviews as an integer
  "price_range": "The exact price range mentioned (e.g., '$', '$$', '$$$')",
  "business_hours": "The exact business hours requirement",
  "keywords": "The exact keywords mentioned, comma-separated if multiple"
}

RULES:
1. Return ONLY valid JSON - no explanations, intro text, or markdown
2. Convert text numbers to numeric types (e.g., "four point five" → 4.5)
3. If a parameter is missing, use these defaults:
   - min_rating: 0
   - min_reviews: 0
   - price_range: "" (empty string)
   - business_hours: "anytime"
   - keywords: "" (empty string)
4. For price range with "rupiah" + "$" notation, preserve exactly as written
5. For business hours, preserve the exact wording (e.g., "open now", "open 24 hours")

EXAMPLES:
Input: "Find a cozy café in Seattle that has a rating of at least 4.5 and at least 100 reviews."
Output: {"business_type":"cozy café","location":"Seattle","min_rating":4.5,"min_reviews":100,"price_range":"","business_hours":"anytime","keywords":""}

Input: "Find a salon in Bandung that has a rating of at least 4.2 and at least 50 number of reviews. Additional Requirements: • The business must have a price range of 'rupiah' + '$$'. • The business operates at open now. • Business reviews and descriptions must include 'premium, luxury, service'."
Output: {"business_type":"salon","location":"Bandung","min_rating":4.2,"min_reviews":50,"price_range":"rupiah + $$","business_hours":"open now","keywords":"premium, luxury, service"}
"""

        # First attempt with enhanced parsing using gpt-4o-mini
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": self.referer_url,
                    "X-Title": self.site_name,
                },
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            # Parse the JSON response
            response_text = completion.choices[0].message.content
            parsed_parameters = json.loads(response_text)
            
            # Validate and convert numeric types
            parsed_parameters["min_rating"] = float(parsed_parameters.get("min_rating", 0))
            parsed_parameters["min_reviews"] = int(parsed_parameters.get("min_reviews", 0))
            
            # Set default values for missing parameters
            default_params = {
                "business_type": "",
                "location": "",
                "min_rating": 0.0,
                "min_reviews": 0,
                "price_range": "",
                "business_hours": "anytime",
                "keywords": ""
            }
            
            for key, default_value in default_params.items():
                if key not in parsed_parameters or parsed_parameters[key] is None:
                    parsed_parameters[key] = default_value
                    
            return parsed_parameters
            
        except Exception as e:
            print(f"Error in parsing with gpt-4o-mini: {str(e)}")
            
            # Fallback: Use regex pattern matching
            return self._regex_pattern_parsing(prompt)
    
    def _regex_pattern_parsing(self, prompt):
        """
        Fallback method using regex pattern matching to extract search parameters
        
        Args:
            prompt (str): User prompt
            
        Returns:
            dict: Dictionary with extracted parameters
        """
        # Initialize with default values
        parameters = {
            'business_type': "",
            'location': "",
            'min_rating': 0.0,
            'min_reviews': 0,
            'price_range': "",
            'business_hours': "anytime",
            'keywords': ""
        }
        
        # Extract business type and location
        match = re.search(r"Find a (.*?) in (.*?) that has", prompt, re.IGNORECASE)
        if match:
            parameters['business_type'] = match.group(1).strip()
            parameters['location'] = match.group(2).strip()
        
        # Extract minimum rating
        match = re.search(r"rating of at least ([0-9.]+)", prompt)
        if match:
            parameters['min_rating'] = float(match.group(1))
        
        # Extract minimum number of reviews
        match = re.search(r"at least ([0-9]+) (?:number of )?reviews", prompt)
        if match:
            parameters['min_reviews'] = int(match.group(1))
        
        # Extract price range
        match = re.search(r"price range of [\"']?(.*?)[\"']?\.", prompt)
        if match:
            parameters['price_range'] = match.group(1).strip()
        
        # Extract business hours
        match = re.search(r"operates at ([^\.•]+)", prompt)
        if match:
            parameters['business_hours'] = match.group(1).strip()
        
        # Extract keywords
        match = re.search(r"must include [\"']?(.*?)[\"']?(?:\.|\Z)", prompt)
        if match:
            parameters['keywords'] = match.group(1).strip()
        
        return parameters
        
    def search_businesses(self, parameters):
        """
        Search for businesses using Google Places API based on the parameters
        
        Args:
            parameters (dict): Search parameters extracted from the prompt
            
        Returns:
            list: List of businesses matching the criteria
        """
        # First, perform a Text Search to get initial results
        places_found = self._text_search(parameters['business_type'], parameters['location'])
        
        # Filter results based on rating and review count
        filtered_places = []
        for place in places_found:
            if 'rating' not in place or 'user_ratings_total' not in place:
                continue
                
            if (place['rating'] >= parameters['min_rating'] and 
                place['user_ratings_total'] >= parameters['min_reviews']):
                filtered_places.append(place)
        
        # Get detailed information for each place
        detailed_places = []
        for place in filtered_places[:20]:  # Limit to 20 places to avoid excessive API calls
            place_details = self._get_place_details(place['place_id'])
            
            # Check price level if required
            if parameters['price_range'] and 'price_level' in place_details:
                price_symbols = '$' * place_details['price_level']
                if not self._match_price_range(price_symbols, parameters['price_range']):
                    continue
            
            # Check business hours if required
            if parameters['business_hours'] and parameters['business_hours'] != 'anytime':
                if not self._check_business_hours(place_details, parameters['business_hours']):
                    continue
            
            # Check for keywords in reviews if specified
            if parameters['keywords']:
                place_details['keyword_matches'] = self._search_reviews_for_keywords(
                    place_details, parameters['keywords']
                )
                
                # Skip if no keyword matches found (optional, based on requirements)
                # if not place_details['keyword_matches']:
                #     continue
            
            # Add match percentages
            place_details['match_percentage'] = self._calculate_match_percentage(place_details, parameters)
            
            detailed_places.append(place_details)
        
        # Sort by match percentage
        return sorted(detailed_places, key=lambda x: x.get('match_percentage', 0), reverse=True)
    
    def _text_search(self, business_type, location):
        """Perform text search with Google Places API"""
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        
        # Combine business type and location for search
        query = f"{business_type} in {location}"
        
        params = {
            "query": query,
            "key": self.google_api_key
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if result['status'] != 'OK':
            print(f"Error in text search: {result.get('status')}")
            if 'error_message' in result:
                print(f"Error message: {result['error_message']}")
            return []
        
        # Check for next page token to get more results if needed
        places = result.get('results', [])
        next_page_token = result.get('next_page_token')
        
        # Get a few more pages of results if available (up to 3 pages total)
        pages_fetched = 1
        max_pages = 3
        
        while next_page_token and pages_fetched < max_pages:
            # Google requires a delay before using the next_page_token
            time.sleep(2)
            
            params = {
                "pagetoken": next_page_token,
                "key": self.google_api_key
            }
            
            response = requests.get(url, params=params)
            result = response.json()
            
            if result['status'] == 'OK':
                places.extend(result.get('results', []))
                next_page_token = result.get('next_page_token')
                pages_fetched += 1
            else:
                break
                
        return places
    
    def _get_place_details(self, place_id):
        """Get detailed information about a place using its place_id"""
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        
        params = {
            "place_id": place_id,
            "fields": "name,place_id,formatted_address,geometry,rating,user_ratings_total,reviews,price_level,opening_hours,website,formatted_phone_number,types",
            "language": "en",  # Set language to ensure consistent parsing
            "key": self.google_api_key
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if result['status'] != 'OK':
            print(f"Error in place details: {result.get('status')}")
            if 'error_message' in result:
                print(f"Error message: {result['error_message']}")
            return {}
        
        return result.get('result', {})
    
    def _match_price_range(self, price_symbols, required_price_range):
        """Check if the price level matches the required price range"""
        # If no price range requirement, consider it a match
        if not required_price_range:
            return True
            
        # Handle 'rupiah + $$' format
        if 'rupiah' in required_price_range.lower():
            # Extract the $ symbols part
            match = re.search(r'rupiah\s*\+\s*(\$+)', required_price_range)
            if match:
                required_symbols = match.group(1)
                return price_symbols == required_symbols
        
        # Direct comparison for simple cases
        return price_symbols in required_price_range
    
    def _check_business_hours(self, place_details, required_hours):
        """Check if the business hours match the required hours"""
        if not required_hours or required_hours.lower() == 'anytime':
            return True
            
        if 'opening_hours' not in place_details:
            return False
            
        # Check for "open now"
        if required_hours.lower() == 'open now' and place_details['opening_hours'].get('open_now', False):
            return True
            
        # Check for "open 24 hours"
        if required_hours.lower() == 'open 24 hours':
            if 'weekday_text' in place_details['opening_hours']:
                for day_hours in place_details['opening_hours']['weekday_text']:
                    if '24 hours' in day_hours.lower():
                        return True
            return False
            
        # For "open at [specific time]"
        if required_hours.lower().startswith('open at'):
            time_str = required_hours.lower().replace('open at', '').strip()
            if 'weekday_text' in place_details['opening_hours']:
                current_day = datetime.now().strftime('%A')
                for day_hours in place_details['opening_hours']['weekday_text']:
                    if current_day.lower() in day_hours.lower():
                        # Basic check if the time falls within opening hours
                        if time_str in day_hours.lower():
                            return True
            return False
            
        return False  # If we can't determine, default to not matching
    
    def _search_reviews_for_keywords(self, place_details, keywords):
        """
        Search reviews for specific keywords
        
        Args:
            place_details (dict): Place details containing reviews
            keywords (str): Comma-separated list of keywords to search for
            
        Returns:
            list: List of found keywords and their frequency
        """
        if 'reviews' not in place_details:
            return []
            
        keyword_list = [kw.strip().lower() for kw in keywords.split(',')]
        keyword_counts = {kw: 0 for kw in keyword_list}
        
        # Search in reviews
        for review in place_details.get('reviews', []):
            review_text = review.get('text', '').lower()
            
            for keyword in keyword_list:
                if keyword in review_text:
                    keyword_counts[keyword] += 1
        
        # Search in business name
        if 'name' in place_details:
            business_text = place_details['name'].lower()
            for keyword in keyword_list:
                if keyword in business_text:
                    keyword_counts[keyword] += 2  # Weight more heavily for name matches
        
        # Search in business types
        if 'types' in place_details:
            for business_type in place_details['types']:
                business_type = business_type.lower().replace('_', ' ')
                for keyword in keyword_list:
                    if keyword in business_type:
                        keyword_counts[keyword] += 1
                    
        # Format results with count
        matches = [f"{kw} ({count})" for kw, count in keyword_counts.items() if count > 0]
        return matches
    
    def _calculate_match_percentage(self, place, parameters):
        """Calculate how well a place matches the search parameters"""
        # Define weights for different criteria
        weights = {
            'rating': 0.25,
            'reviews': 0.20,
            'price': 0.15,
            'keywords': 0.40
        }
        
        score = 0
        
        # Rating match (from min_rating to 5.0)
        if 'rating' in place:
            rating_range = 5.0 - parameters['min_rating']
            if rating_range > 0:
                rating_score = min(1.0, (place['rating'] - parameters['min_rating']) / rating_range)
                score += weights['rating'] * rating_score
            else:
                score += weights['rating']  # If min_rating is 5.0, give full score if matched
        
        # Review count match (logarithmic scale since review counts vary widely)
        if 'user_ratings_total' in place:
            min_reviews = parameters['min_reviews']
            if min_reviews > 0:
                import math
                review_score = min(1.0, math.log10(place['user_ratings_total'] / min_reviews + 1) / math.log10(11))  # log10(11) ≈ 1.04
                score += weights['reviews'] * review_score
            else:
                score += weights['reviews']
        
        # Price match (exact match gets full score)
        if parameters['price_range'] and 'price_level' in place:
            price_symbols = '$' * place['price_level']
            if self._match_price_range(price_symbols, parameters['price_range']):
                score += weights['price']
        elif not parameters['price_range']:
            # If no price range specified, give full score
            score += weights['price']
        
        # Keyword matches
        if parameters['keywords'] and 'keyword_matches' in place and place['keyword_matches']:
            keyword_list = [kw.strip().lower() for kw in parameters['keywords'].split(',')]
            if keyword_list:
                # Count actual keywords found (not occurrences)
                found_keywords = set()
                for kw_match in place['keyword_matches']:
                    keyword = kw_match.split(' (')[0].lower()
                    found_keywords.add(keyword)
                
                match_ratio = len(found_keywords) / len(keyword_list)
                score += weights['keywords'] * match_ratio
        elif not parameters['keywords']:
            # If no keywords specified, give full score
            score += weights['keywords']
        
        return round(score * 100, 2)  # Convert to percentage
    
    def process_results(self, businesses, parameters):
        """
        Process and format the search results with dynamic column selection
        
        Args:
            businesses (list): List of businesses with details
            parameters (dict): Search parameters extracted from the prompt
            
        Returns:
            pandas.DataFrame: DataFrame containing processed results with selected columns
        """
        results = []
        
        for business in businesses:
            # Extract positive and negative reviews based on rating
            positive_reviews = [r for r in business.get('reviews', []) if r.get('rating', 0) >= 4]
            negative_reviews = [r for r in business.get('reviews', []) if r.get('rating', 0) <= 2]
            
            # Apply the review sampling rules
            pos_summary = self._sample_reviews(positive_reviews)
            neg_summary = self._sample_reviews(negative_reviews)
            
            # Format business hours
            hours_text = self._format_hours(business.get('opening_hours', {}))
            
            # Process keywords
            keywords = business.get('keyword_matches', [])
            keywords_text = ', '.join(keywords[:50])  # Limit to 50 keywords
            
            # Calculate individual match percentages
            rating_match = self._calculate_rating_match_percentage(business, businesses)
            address_match = self._calculate_address_match_percentage(business, businesses)
            price_match = self._calculate_price_match_percentage(business, businesses)
            
            # Prepare the result row with all possible fields
            result = {
                'Name': business.get('name', 'N/A'),
                'Address': business.get('formatted_address', 'N/A'),
                'Address_Match': f"{address_match}%",
                'Rating': business.get('rating', 'N/A'),
                'Total_Reviews': business.get('user_ratings_total', 'N/A'),
                'Rating_Review_Match': f"{rating_match}%",
                'Phone': business.get('formatted_phone_number', 'N/A'),
                'Website': business.get('website', 'N/A'),
                'Price_Level': '$' * business.get('price_level', 0) if 'price_level' in business else 'N/A',
                'Price_Match': f"{price_match}%",
                'Hours': hours_text,
                'Keywords': keywords_text,
                'Positive_Reviews': pos_summary,
                'Negative_Reviews': neg_summary,
                'Overall_Match': f"{business.get('match_percentage', 0)}%"
            }
            
            results.append(result)
        
        # Create DataFrame with all columns
        full_df = pd.DataFrame(results)
        
        # Dynamically select columns based on parameters
        selected_columns = ['Name']  # Always include the business name
        
        # Add location-related columns if location is specified
        if parameters.get('location'):
            selected_columns.extend(['Address', 'Address_Match'])
        
        # Add rating-related columns if rating is specified
        if parameters.get('min_rating') > 0:
            selected_columns.extend(['Rating', 'Rating_Review_Match'])
        
        # Add review count if specified
        if parameters.get('min_reviews') > 0:
            selected_columns.append('Total_Reviews')
        
        # Add price level if specified
        if parameters.get('price_range'):
            selected_columns.extend(['Price_Level', 'Price_Match'])
        
        # Add business hours if specified
        if parameters.get('business_hours') and parameters.get('business_hours') != 'anytime':
            selected_columns.append('Hours')
        
        # Add keywords if specified
        if parameters.get('keywords'):
            selected_columns.append('Keywords')
            
            # Only include reviews if keywords are specified (since we'd want to see if they appear in reviews)
            selected_columns.extend(['Positive_Reviews', 'Negative_Reviews'])
        
        # Always include overall match percentage
        selected_columns.append('Overall_Match')
        
        # Filter columns that exist in the DataFrame
        available_columns = [col for col in selected_columns if col in full_df.columns]
        
        # Return filtered DataFrame with only the relevant columns
        return full_df[available_columns]
    
    def _calculate_rating_match_percentage(self, business, all_businesses):
        """Calculate rating match percentage compared to other businesses"""
        if 'rating' not in business or not all_businesses:
            return 0
            
        # Get min and max ratings across all businesses
        ratings = [b.get('rating', 0) for b in all_businesses if 'rating' in b]
        if not ratings:
            return 0
            
        min_rating = min(ratings)
        max_rating = max(ratings)
        
        # Normalize the rating
        if max_rating == min_rating:
            return 100  # All businesses have the same rating
            
        normalized = (business['rating'] - min_rating) / (max_rating - min_rating) * 100
        return round(normalized, 2)
    
    def _calculate_address_match_percentage(self, business, all_businesses):
        """Simple implementation to return match percentage"""
        # Simply return the overall match as address match for now
        return business.get('match_percentage', 0)
    
    def _calculate_price_match_percentage(self, business, all_businesses):
        """Simple implementation to return match percentage"""
        # Simply return the overall match as price match for now
        return business.get('match_percentage', 0)
    
    def _sample_reviews(self, reviews):
        """Sample reviews according to the specified rules"""
        num_reviews = len(reviews)
        
        if num_reviews <= 10:
            # Take all reviews
            sample_size = num_reviews
        elif num_reviews <= 100:
            # Take 40%, minimum 5, maximum 30
            sample_size = min(max(int(0.4 * num_reviews), 5), 30)
        else:
            # Take 20%, minimum 25, maximum 50
            sample_size = min(max(int(0.2 * num_reviews), 25), 50)
            
        # Sort reviews by recency (assuming reviews are sorted by recency already)
        sampled_reviews = reviews[:sample_size]
        
        # Format them into a single string
        review_texts = []
        for r in sampled_reviews:
            # Limit review text to 100 characters with ellipsis
            review_text = r.get('text', 'No text')
            truncated_text = review_text[:100] + "..." if len(review_text) > 100 else review_text
            
            review_texts.append(f"{r.get('author_name', 'Anonymous')} ({r.get('rating', 'N/A')}★): {truncated_text}")
                      
        return '\n'.join(review_texts)
    
    def _format_hours(self, opening_hours):
        """Format opening hours into readable text"""
        if not opening_hours:
            return "Hours not available"
            
        if 'weekday_text' in opening_hours:
            return '\n'.join(opening_hours['weekday_text'])
            
        return "Open now" if opening_hours.get('open_now', False) else "Hours not available"
    
    def run_search(self, prompt):
        """
        Run the complete search process
        
        Args:
            prompt (str): User prompt for business search
            
        Returns:
            pandas.DataFrame: Search results
        """
        print("Parsing prompt...")
        parameters = self.parse_prompt(prompt)
        print(f"Search parameters: {json.dumps(parameters, indent=2)}")
        
        print("\nSearching for businesses...")
        businesses = self.search_businesses(parameters)
        print(f"Found {len(businesses)} matching businesses")
        
        print("\nProcessing results...")
        results_df = self.process_results(businesses, parameters)
        
        return results_df