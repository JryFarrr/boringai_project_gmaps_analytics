"""
Module for converting price strings to standardized price level symbols
"""

from src.services.api_clients.factory import create_client

def get_price_range_system_prompt():
    """
    Get the system prompt for price range conversion
    
    Returns:
        str: System prompt for price range conversion
    """
    return """You are an expert system for converting various price formats to standardized price level symbols.

Your job is to analyze a price string and convert it to a standard price level format ($, $$, $$$, $$$$).

PRICE RANGE CLASSIFICATION:
When encountering price information in any currency or format, classify it into standard price level symbols ($, $$, $$$, $$$$) based on relative affordability within the local context.

Follow these guidelines:
1. Analyze the price information relative to the business type mentioned (if provided)
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

For Indonesian currency (Rupiah/Rp) or colloquial formats (rb/ribu):
• $ = Below Rp50,000 or below 50rb
• $$ = Rp50,000 - Rp100,000 or 50rb-100rb
• $$$ = Above Rp100,000 up to Rp300,000 or >100rb up to 300rb
• $$$$ = Above Rp300,000 up to infinite or >300rb

Examples of price range conversions:
- "Rp5,000" → "$" 
- "Rp10,000 - Rp25,000" → "$"
- "Rp50,000 - Rp100,000" → "$$"
- "Rp200,000+" → "$$$"
- "affordable price" → "$"
- "premium price" → "$$$"
- "200-300 baht" → "$$$" (for Thailand)
- "₹500-₹1000" → "$$" (for India)
- "cheap" → "$"
- "50rb-100rb" → "$$"
- "moderate" → "$$"
- "$$$" → "$$$" (already in correct format)

OUTPUT FORMAT:
Return ONLY the price level symbols, nothing else. 
For example: "$", "$$", "$$$", or "$$$$"

RULES:
1. If the input is already in the standardized $ format (e.g., "$", "$$", "$$$", "$$$$"), return it unchanged
2. If the input is empty or None, return an empty string ""
3. Return ONLY the price level symbols, no explanation or additional text
4. If uncertain, make a best estimate based on the provided guidelines
5. For "luxury", "exclusive", "premium" descriptions, use "$$$$" unless context indicates otherwise
6. For colloquial price formats in Indonesian (like "50rb", "100rb"), treat as Rp50,000, Rp100,000, etc.
"""

def convert_price_range_with_ai(price_string, business_type=None, client=None, headers=None, provider="openai"):
    """
    Convert price string to standardized price range symbols using AI
    
    Args:
        price_string (str): The price string to convert
        business_type (str, optional): Type of business for context
        client: API client (OpenAI)
        headers (dict): Headers for the API request
        provider (str): API provider ("openai" or "openrouter")
        
    Returns:
        str: Standardized price range symbols ("$", "$$", "$$$", "$$$$") or empty string
    """
    # If price string is already in standardized format, return it
    if price_string in ["$", "$$", "$$$", "$$$$"]:
        return price_string
    
    # If price string is empty, return empty string
    if not price_string or price_string.strip() == "":
        return ""
    
    try:
        # Prepare user content
        user_content = f"Convert this price to standard price level symbols: {price_string}"
        if business_type:
            user_content += f" for a {business_type}"
        
        # Common parameters for API
        chat_params = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": get_price_range_system_prompt()},
                {"role": "user", "content": user_content}
            ]
        }
        
        # Add extra_headers for OpenRouter
        if provider == "openrouter" and headers:
            chat_params["extra_headers"] = headers
        
        # Make the API call
        completion = client.chat.completions.create(**chat_params)
        
        # Get the response text
        converted_price = completion.choices[0].message.content.strip()
        
        # Validate the response - should only contain $ symbols
        if all(char == '$' for char in converted_price) and len(converted_price) <= 4:
            return converted_price
        else:
            # If response is not in expected format, try to extract $ symbols
            import re
            match = re.search(r'(\${1,4})', converted_price)
            if match:
                return match.group(1)
            # Return empty string as fallback
            return ""
        
    except Exception as e:
        print(f"Error in converting price range with AI: {str(e)}")
        # Return empty string on error
        return ""

def process_price_range(price_string, business_type=None, **kwargs):
    """
    Main function to process price range string to standardized format
    
    Args:
        price_string (str): The price string to convert
        business_type (str, optional): Type of business for context
        **kwargs: Additional arguments to pass to the client creation function
        
    Returns:
        str: Standardized price range symbols or original string on failure
    """
    # If already in correct format, return as is
    if price_string in ["$", "$$", "$$$", "$$$$"]:
        return price_string
    
    # If empty, return empty string
    if not price_string or price_string.strip() == "":
        return ""
    
    # Create API client
    from src.services.api_clients.factory import create_client
    client, headers, actual_provider = create_client(**kwargs)
    
    # Convert using AI
    converted_price = convert_price_range_with_ai(
        price_string, 
        business_type=business_type,
        client=client, 
        headers=headers, 
        provider=actual_provider
    )
    
    # Return converted price, or original if conversion failed
    return converted_price if converted_price else price_string