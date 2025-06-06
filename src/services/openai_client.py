import os
import json
from openai import OpenAI
from config import Config

def create_openai_client(api_key=None, organization=None):
    """
    Membuat klien API OpenAI.
    """
    api_key = api_key or Config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    
    client_kwargs = {"api_key": api_key}
    if organization:
        client_kwargs["organization"] = organization
    
    client = OpenAI(**client_kwargs)
    return client, {}

class OpenAIService:
    """Wrapper untuk panggilan OpenAI API."""
    def __init__(self):
        self.client, _ = create_openai_client()
        self.model = Config.DEFAULT_OPENAI_MODEL

    def _call_api(self, messages, json_mode=False):
        response_format = {"type": "json_object"} if json_mode else None
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format=response_format
        )
        return completion.choices[0].message.content

    def generate_insights(self, details, match_percentage):
        prompt = f"""Analyze this business:
        - Name: {details.get('placeName')}
        - Rating: {details.get('rating')} from {details.get('totalRatings')} reviews.
        - Match Score: {match_percentage}%
        Based on this, what are its 2 main strengths and 2 main weaknesses?
        Respond ONLY with JSON: {{"strengths": ["...", "..."], "weaknesses": ["...", "..."]}}"""
        
        response_str = self._call_api([{"role": "user", "content": prompt}], json_mode=True)
        try:
            return json.loads(response_str)
        except:
            return {"strengths": [], "weaknesses": []}