"""
Module for parsing user prompts and extracting search parameters
"""

import json
import re
from config.config import DEFAULT_SEARCH_PARAMS
from services.api_clients.factory import create_client

def get_system_prompt():
    """
    Get the system prompt for parameter extraction
    
    Returns:
        str: System prompt
    """
    return """You are an expert system for extracting structured business search parameters from user queries.

Your job is to analyze a search query and extract precise parameters for a business discovery system.

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
  "business_type": "The exact business type or category mentioned",
  "location": "The exact location mentioned", 
  "min_rating": float, // The minimum rating as a decimal number (e.g., 4.2)
  "min_reviews": int, // The minimum number of reviews as an integer
  "price_range": "The exact price range mentioned (e.g., '$', '$$', '$$$')",
  "business_hours": "The exact business hours requirement",
  "keywords": "The exact keywords mentioned, comma-separated if multiple",
  "numberOfLeads": "", // The number of establishments to search from, not the number of top results
  "topPlaces": "" // The number of top places to return (e.g., "top 5"), empty string if not specified
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
   - numberOfLeads: "" (empty string if not explicitly mentioned)
   - topPlaces: "" (empty string if not explicitly mentioned)
4. For price range with "rupiah" + "$" notation, preserve exactly as written
5. For business hours, preserve the exact wording (e.g., "open now", "open 24 hours")
6. IMPORTANT: For "numberOfLeads", extract the total number of establishments to search from (e.g., "find top 5 sushi restaurants from 200 restaurants" should set numberOfLeads to 200)
7. For "topPlaces", extract the number of top results requested (e.g., "find top 5 sushi restaurants" should set topPlaces to 5)

EXAMPLES:
Input: "Find a cozy café in Seattle that has a rating of at least 4.5 and at least 100 reviews."
Output: {"business_type":"cozy café","location":"Seattle","min_rating":4.5,"min_reviews":100,"price_range":"","business_hours":"anytime","keywords":"","numberOfLeads":"","topPlaces":""}

Input: "Find a salon in Bandung that has a rating of at least 4.2 and at least 50 number of reviews. Additional Requirements: • The business must have a price range of 'rupiah' + '$$'. • The business operates at open now. • Business reviews and descriptions must include 'premium, luxury, service'."
Output: {"business_type":"salon","location":"Bandung","min_rating":4.2,"min_reviews":50,"price_range":"rupiah + $$","business_hours":"open now","keywords":"premium, luxury, service","numberOfLeads":"","topPlaces":""}

Input: "Find top 5 sushi restaurants in Tokyo from 200 restaurants that has a rating of at least 4.5 and at least 100 reviews."
Output: {"business_type":"sushi restaurants","location":"Tokyo","min_rating":4.5,"min_reviews":100,"price_range":"","business_hours":"anytime","keywords":"","numberOfLeads":200,"topPlaces":5}

Input: "Find the best Italian restaurant in New York with at least 4.7 rating."
Output: {"business_type":"Italian restaurant","location":"New York","min_rating":4.7,"min_reviews":0,"price_range":"","business_hours":"anytime","keywords":"","numberOfLeads":"","topPlaces":""}

Input: "Show me top 10 coffee shops in Portland from 150 shops with at least 50 reviews and open on weekends."
Output: {"business_type":"coffee shops","location":"Portland","min_rating":0,"min_reviews":50,"price_range":"","business_hours":"open on weekends","keywords":"","numberOfLeads":150,"topPlaces":10}
"""


def parse_prompt_with_ai(prompt, client, headers, provider="openai"):
    """
    Parse the user prompt using an LLM API to extract search parameters
    
    Args:
        prompt (str): User prompt in the specified format
        client: API client (OpenAI or OpenRouter)
        headers (dict): Headers for the API request
        provider (str): API provider ("openai" or "openrouter")
        
    Returns:
        dict: Dictionary containing extracted search parameters
    """
    try:
        # Common parameters for both APIs
        chat_params = {
            "model": "gpt-4o-mini" if provider == "openrouter" else "gpt-4o",
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
        
        # Ensure numberOfLeads and topPlaces are present but empty if not specified
        if "numberOfLeads" not in parsed_parameters:
            parsed_parameters["numberOfLeads"] = ""
        if "topPlaces" not in parsed_parameters:
            parsed_parameters["topPlaces"] = ""
        
        # Set default values for missing parameters
        for key, default_value in DEFAULT_SEARCH_PARAMS.items():
            if key != "numberOfLeads" and key != "topPlaces" and (key not in parsed_parameters or parsed_parameters[key] is None):
                parsed_parameters[key] = default_value
                
        return parsed_parameters
        
    except Exception as e:
        print(f"Error in parsing with AI ({provider}): {str(e)}")
        return regex_pattern_parsing(prompt)


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
    # Always include numberOfLeads and topPlaces but set to empty string by default
    parameters["numberOfLeads"] = ""
    parameters["topPlaces"] = ""
    
    # Extract business type, location, and potentially top places
    match = re.search(r"Find (?:top\s+(\d+)\s+)?(?:a )?(.*?) in (.*?) (?:that|with|from)", prompt, re.IGNORECASE)
    if match:
        if match.group(1):  # If "top N" is found
            parameters['topPlaces'] = int(match.group(1))
        parameters['business_type'] = match.group(2).strip()
        parameters['location'] = match.group(3).strip()
    
    # Extract number of leads (total to search from)
    match = re.search(r"from (\d+) (?:places|businesses|stores|shops|restaurants)", prompt, re.IGNORECASE)
    if match:
        parameters['numberOfLeads'] = int(match.group(1))
    
    # Extract top places from other patterns if not already set
    if parameters['topPlaces'] == "":
        match = re.search(r"(?:show|get|find|display) (?:me )?(?:the )?top (\d+)", prompt, re.IGNORECASE)
        if match:
            parameters['topPlaces'] = int(match.group(1))
    
    # Extract minimum rating
    match = re.search(r"rating of at least ([0-9.]+)", prompt)
    if match:
        parameters['min_rating'] = float(match.group(1))
    
    # Alternative rating pattern
    if parameters['min_rating'] == 0:
        match = re.search(r"with at least ([0-9.]+) rating", prompt)
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
        dict: Dictionary containing extracted search parameters
    """
    # Create the appropriate client
    client, headers, actual_provider = create_client(provider=provider, **kwargs)
    
    # Get the full parameters from the prompt using the selected API
    parameters = parse_prompt_with_ai(prompt, client, headers, provider=actual_provider)
    
    return parameters