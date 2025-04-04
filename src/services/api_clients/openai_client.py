"""
OpenAI API client implementation
"""

import os
from openai import OpenAI
from src.config.config import OPENAI_API_KEY

def create_openai_client(api_key=None, organization=None):
    """
    Create an OpenAI API client
    
    Args:
        api_key (str): OpenAI API key (defaults to OPENAI_API_KEY from config)
        organization (str): OpenAI organization ID
        
    Returns:
        tuple: (client, headers)
    """
    # Use provided API key or fall back to environment/config
    if not api_key:
        api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    
    # Create the client with organization ID if provided
    client_kwargs = {"api_key": api_key}
    if organization:
        client_kwargs["organization"] = organization
    
    client = OpenAI(**client_kwargs)
    
    # No special headers needed for standard OpenAI calls
    headers = {}
    
    return client, headers