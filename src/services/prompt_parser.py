"""
Module for parsing user prompts and extracting search parameters
"""

import json
import re
from src.config.config import DEFAULT_SEARCH_PARAMS
from src.services.api_clients.factory import create_client
from src.utils.response_utils import error_response

def get_system_prompt():
    """
    Get the system prompt for parameter extraction
    
    Returns:
        str: System prompt
    """
    return """You are an expert system for extracting structured business search parameters from user queries.

Your job is to analyze a search query and extract precise parameters for a business discovery system.

PRICE RANGE CLASSIFICATION:
When encountering price information in any currency or format, classify it into standard price level symbols ($, $$, $$$, $$$$) based on relative affordability within the local context.

Follow these guidelines:
1. Analyze the price information relative to the business type and location mentioned
2. Convert any price format (numerical values, ranges, or descriptive terms) into the appropriate price level symbol
3. Consider local economic context when determining affordability
4. For any currency, classify based on relative expense level:
   • $ = Budget/Inexpensive (bottom 25% price range for that business type in that location)
   • $$ = Moderate (25-50% price range)
   • $$$ = Upscale (50-75% price range)
   • $$$$ = Luxury/Premium (top 25% price range)
5. For text descriptions without numbers:
   • Terms like "cheap," "budget," "affordable" → $
   • Terms like "moderate," "standard," "average" → $$
   • Terms like "upscale," "premium," "high-end" → $$$
   • Terms like "luxury," "exclusive," "VIP" → $$$$
6. Always normalize the output to use only standard price level symbols regardless of input format

Examples of price range conversions:
- "Rp5.000" → "$" 
- "Rp10.000 - Rp25.000" → "$"
- "Rp50.000 - Rp100.000" → "$$"
- "Rp200.000+" → "$$$"
- "harga terjangkau" → "$"
- "premium price" → "$$$"
- "200-300 baht" → "$$$" (for Thailand)
- "₹500-₹1000" → "$$" (for India)

INPUT FORMAT:
The user will provide a query like this:
"Find a {business type or specific category} in {location} that has a rating of at least {rating} and at least {number of reviews} number of reviews.
Additional Requirements:
- The business must have a price range of {price range}.
- The business operates at {business hours}.
- Business reviews and descriptions must include {specific keywords}."

OUTPUT FORMAT:
You must return ONLY a valid JSON object with these exact fields (no explanations or other text):
{
  "business_type": "The core business type or category (e.g., 'hotels' instead of 'luxury hotels')",
  "location": "The exact location mentioned", 
  "min_rating": float, // The minimum rating as a decimal number (e.g., 4.2)
  "min_reviews": int, // The minimum number of reviews as an integer
  "max_reviews": int, // The maximum number of reviews as an integer, null if not mentioned
  "price_range": "The exact price range mentioned (e.g., '$', '$$', '$$$')",
  "business_hours": "The exact business hours requirement",
  "keywords": "Descriptive adjectives or specific keywords mentioned, comma-separated if multiple",
  "numberOfLeads": "" // The number of establishments to search from, not the number of top results
}

RULES:
1. Return ONLY valid JSON - no explanations, intro text, or markdown
2. Convert text numbers to numeric types (e.g., "four point five" → 4.5)
3. If a parameter is missing, use these defaults:
   - min_rating: 0
   - min_reviews: 0
   - max_reviews: null (indicating no upper limit)
   - price_range: "" (empty string)
   - business_hours: "anytime"
   - keywords: "" (empty string)
   - numberOfLeads: "" (empty string if not explicitly mentioned)
4. For business hours, preserve the exact wording (e.g., "open now", "open 24 hours")
5. For "numberOfLeads", extract the total number of establishments to search from (e.g., "find top 5 sushi restaurants from 200 restaurants" should set numberOfLeads to 200, or "find 3 luxury hotels" should set numberOfLeads to 3)
6. Remove "topPlaces" entirely from the output format and parsing logic
7. For "business_type", extract the core business type by removing descriptive adjectives (e.g., "luxury hotels" → "hotels", "cozy cafés" → "cafés")
8. For "keywords", include any descriptive adjectives (e.g., "luxury", "cozy", "affordable", "premium", "upscale") found in the business type or elsewhere in the prompt, unless they are explicitly tied to another field like price_range. Also include any explicitly mentioned keywords (e.g., from "must include {keywords}").
9. If a descriptive term like "luxury" is used and no explicit price range is provided, infer a price_range of "$$$$" for terms like "luxury", "exclusive", or "VIP".
10. For reviews, parse both minimum and maximum review counts. For phrases like "between 50 and 100 reviews" or "reviews from 50 to 100", set min_reviews to 50 and max_reviews to 100. For phrases like "at most 100 reviews" or "no more than 100 reviews", set max_reviews to 100 and min_reviews to 0.

EXAMPLES:
Input: "Find 3 luxury hotels in Surabaya that has a rating of at least 4.5 and at least 100 reviews."
Output: {"business_type":"hotels","location":"Surabaya","min_rating":4.5,"min_reviews":100,"max_reviews":null,"price_range":"$$$$","business_hours":"anytime","keywords":"luxury","numberOfLeads":3}

Input: "Find a cozy café in Seattle that has a rating of at least 4.5 and between 50 and 100 reviews."
Output: {"business_type":"café","location":"Seattle","min_rating":4.5,"min_reviews":50,"max_reviews":100,"price_range":"","business_hours":"anytime","keywords":"cozy","numberOfLeads":""}

Input: "Find a salon in Bandung that has a rating of at least 4.2 and at most 50 reviews. Additional Requirements: • The business must have a price range of Rp50.000 - Rp100.000. • The business operates at open now. • Business reviews and descriptions must include 'premium, luxury, service'."
Output: {"business_type":"salon","location":"Bandung","min_rating":4.2,"min_reviews":0,"max_reviews":50,"price_range":"$$","business_hours":"open now","keywords":"premium, luxury, service","numberOfLeads":""}

Input: "Find 25 sushi restaurants in Tokyo that has a rating of at least 4.5 and fewer than 100 reviews."
Output: {"business_type":"sushi restaurants","location":"Tokyo","min_rating":4.5,"min_reviews":0,"max_reviews":100,"price_range":"","business_hours":"anytime","keywords":"","numberOfLeads":25}

Input: "Find the best Italian restaurant in New York with at least 4.7 rating."
Output: {"business_type":"Italian restaurant","location":"New York","min_rating":4.7,"min_reviews":0,"max_reviews":null,"price_range":"","business_hours":"anytime","keywords":"best","numberOfLeads":""}

Input: "Show me coffee shops in Portland from 150 shops with reviews between 50 and 200 and open on weekends."
Output: {"business_type":"coffee shops","location":"Portland","min_rating":0,"min_reviews":50,"max_reviews":200,"price_range":"","business_hours":"open on weekends","keywords":"","numberOfLeads":150}

Input: "Find a luxury hotel in Bali with a price range of Rp1.000.000 per night and rating at least 4.7"
Output: {"business_type":"hotel","location":"Bali","min_rating":4.7,"min_reviews":0,"max_reviews":null,"price_range":"$$$$","business_hours":"anytime","keywords":"luxury","numberOfLeads":""}

Input: "Find affordable restaurants in Jakarta with prices under Rp25.000 per person and no more than 100 reviews"
Output: {"business_type":"restaurants","location":"Jakarta","min_rating":0,"min_reviews":0,"max_reviews":100,"price_range":"$","business_hours":"anytime","keywords":"affordable","numberOfLeads":""}
"""

def parse_prompt_with_ai(prompt, client, headers, provider="openai"):
    """
    Parse the user prompt using an LLM API to extract search parameters
    
    Args:
        prompt (str): User prompt in the specified format
        client: API client (OpenAI)
        headers (dict): Headers for the API request
        provider (str): API provider ("openai" or "openrouter")
        
    Returns:
        dict: Dictionary containing extracted search parameters or None if parsing fails
    """
    try:
        # Common parameters for both APIs
        chat_params = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}  # Force JSON response
        }
        
        # Add extra_headers for OpenRouter
        if provider == "openrouter" and headers:
            chat_params["extra_headers"] = headers
        
        # Make the API call
        completion = client.chat.completions.create(**chat_params)
        
        # Parse the JSON response
        response_text = completion.choices[0].message.content
        parsed_parameters = json.loads(response_text)
        
        # Validate and convert numeric types
        parsed_parameters["min_rating"] = float(parsed_parameters.get("min_rating", 0))
        parsed_parameters["min_reviews"] = int(parsed_parameters.get("min_reviews", 0))
        
        # Handle max_reviews - convert to int if present, otherwise keep as None
        if "max_reviews" in parsed_parameters and parsed_parameters["max_reviews"] is not None:
            parsed_parameters["max_reviews"] = int(parsed_parameters["max_reviews"])
        
        # Ensure numberOfLeads is present but empty if not specified
        if "numberOfLeads" not in parsed_parameters:
            parsed_parameters["numberOfLeads"] = ""
        
        # Remove topPlaces from parsed parameters
        parsed_parameters.pop("topPlaces", None)
        
        # Set default values for missing parameters
        for key, default_value in DEFAULT_SEARCH_PARAMS.items():
            if key != "numberOfLeads" and key != "max_reviews" and (key not in parsed_parameters or parsed_parameters[key] is None):
                parsed_parameters[key] = default_value
        
        # Ensure max_reviews is included in the response
        if "max_reviews" not in parsed_parameters:
            parsed_parameters["max_reviews"] = None
                
        return parsed_parameters
        
    except Exception as e:
        print(f"Error in parsing with AI ({provider}): {str(e)}")
        # Instead of falling back to regex, return None to indicate parsing failure
        return None


def regex_pattern_parsing(prompt):
    """
    Fallback method using regex pattern matching to extract search parameters
    
    Args:
        prompt (str): User prompt
        
    Returns:
        dict: Dictionary with extracted parameters
    """
    # Initialize with default values
    parameters = DEFAULT_SEARCH_PARAMS.copy()
    # Always include numberOfLeads but set to empty string by default
    parameters["numberOfLeads"] = ""
    # Add max_reviews with default value of None
    parameters["max_reviews"] = None
    
    # Extract business type, location, and potentially top places
    match = re.search(r"Find (?:a )?(.*?) in (.*?) (?:that|with|from)", prompt, re.IGNORECASE)
    if match:
        parameters['business_type'] = match.group(1).strip()
        parameters['location'] = match.group(2).strip()
    
    # Extract number of leads (total to search from)
    match = re.search(r"from (\d+) (?:places|businesses|stores|shops|restaurants)", prompt, re.IGNORECASE)
    if match:
        parameters['numberOfLeads'] = int(match.group(1))
    
    # Extract minimum rating
    match = re.search(r"rating of at least ([0-9.]+)", prompt)
    if match:
        parameters['min_rating'] = float(match.group(1))
    
    # Alternative rating pattern
    if parameters['min_rating'] == 0:
        match = re.search(r"with at least ([0-9.]+) rating", prompt)
        if match:
            parameters['min_rating'] = float(match.group(1))
    
    # Extract review count range (between X and Y reviews)
    match = re.search(r"between (\d+) and (\d+) reviews", prompt, re.IGNORECASE)
    if match:
        parameters['min_reviews'] = int(match.group(1))
        parameters['max_reviews'] = int(match.group(2))
    else:
        # Extract minimum number of reviews
        match = re.search(r"at least (\d+) (?:number of )?reviews", prompt)
        if match:
            parameters['min_reviews'] = int(match.group(1))
        
        # Extract maximum number of reviews
        max_reviews_patterns = [
            r"(?:at most|no more than|fewer than|less than) (\d+) (?:number of )?reviews",
            r"reviews (?:up to|not exceeding) (\d+)"
        ]
        
        for pattern in max_reviews_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                parameters['max_reviews'] = int(match.group(1))
                # If only max is specified without min, set min to 0
                if "min_reviews" not in parameters or parameters["min_reviews"] == 0:
                    parameters['min_reviews'] = 0
                break
    
    # Extract price range
    match = re.search(r"price range of [\"']?(.*?)[\"']?\.", prompt)
    if match:
        parameters['price_range'] = match.group(1).strip()
    
    # Extract business hours
    match = re.search(r"operates at ([^\.•]+)", prompt)
    if match:
        parameters['business_hours'] = match.group(1).strip()
    
    # Alternative business hours pattern
    if parameters['business_hours'] == "anytime":
        match = re.search(r"(?:open|available) (?:on|during|at) ([^\.•,]+)", prompt, re.IGNORECASE)
        if match:
            parameters['business_hours'] = match.group(1).strip()
    
    # Extract keywords
    match = re.search(r"must include [\"']?(.*?)[\"']?(?:\.|\Z)", prompt)
    if match:
        parameters['keywords'] = match.group(1).strip()
    
    return parameters


def parse_prompt(prompt, provider="openai", **kwargs):
    """
    Parse the user prompt to extract search parameters
    
    Args:
        prompt (str): User prompt in the specified format
        provider (str): The API provider to use ("openai" or "openrouter")
        **kwargs: Additional arguments to pass to the client creation function
        
    Returns:
        dict: Dictionary containing extracted search parameters or error response dictionary
    """
    # Create the appropriate client
    client, headers, actual_provider = create_client(**kwargs)
    
    # Get the full parameters from the prompt using the selected API
    parameters = parse_prompt_with_ai(prompt, client, headers, provider=actual_provider)
    
    # Check if AI parsing failed
    if parameters is None:
        print("AI parsing failed. Unable to extract parameters from prompt.")
        # Return an error response using the imported utility function
        # But extract just the response object without status code
        response_dict, _ = error_response("AI parsing failed. Unable to extract parameters from prompt.")
        return response_dict
    
    return parameters