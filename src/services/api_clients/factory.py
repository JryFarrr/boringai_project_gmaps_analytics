"""
Factory module for creating API clients
"""

from src.services.api_clients.openai_client import create_openai_client
from src.services.api_clients.openrouter_client import create_openrouter_client

def create_client(provider="openai", **kwargs):
    """
    Factory function to create an API client based on the provider
    
    Args:
        provider (str): The API provider to use ("openai" or "openrouter")
        **kwargs: Additional arguments to pass to the client creation function
        
    Returns:
        tuple: (client, headers, provider)
    """
    if provider.lower() == "openrouter":
        client, headers = create_openrouter_client(**kwargs)
        return client, headers, "openrouter"
    else:  # default to OpenAI
        client, headers = create_openai_client(**kwargs)
        return client, headers, "openai"