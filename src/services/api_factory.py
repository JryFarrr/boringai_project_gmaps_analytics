from .openai_client import create_openai_client

def create_client(**kwargs):
    """
    Factory untuk membuat klien API. Saat ini hanya mendukung OpenAI.
    """
    client, headers = create_openai_client(**kwargs)
    return client, headers, "openai"