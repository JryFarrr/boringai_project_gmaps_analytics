"""
OpenRouter API client implementation
"""

import os
from openai import OpenAI
from config.config import OPENROUTER_API_KEY

def create_openrouter_client(api_key=None, referer_url=None, site_name=None):
    """
    Create an OpenRouter API client
    
    Args:
        api_key (str): OpenRouter API key (defaults to OPENROUTER_API_KEY from config)
        referer_url (str): Website URL for OpenRouter rankings
        site_name (str): Site name for OpenRouter rankings
        
    Returns:
        tuple: (client, headers)
    """
    # Use provided API key or fall back to environment/config
    if not api_key:
        api_key = OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
    
    # Create the client with OpenRouter base URL
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    
    # Set up headers for OpenRouter specific features
    headers = {}
    if referer_url:
        headers["HTTP-Referer"] = referer_url
    if site_name:
        headers["X-Title"] = site_name
    
    return client, headers