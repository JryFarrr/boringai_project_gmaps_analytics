"""
Factory module for creating API clients
"""

from src.services.api_clients.openai_client import create_openai_client

def create_client(**kwargs):
    """
    Factory function to create an API client based on the provider
    
    Args:
        **kwargs: Additional arguments to pass to the client creation function
        
    Returns:
        tuple: (client, headers, provider)
    """

    client, headers = create_openai_client(**kwargs)
    return client, headers, "openai"