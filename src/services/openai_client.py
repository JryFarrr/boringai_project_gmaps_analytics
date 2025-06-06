import json
from config import Config
from openai import OpenAI

# Fungsi ini dibutuhkan oleh prompt_parser
def create_openai_client(api_key=None, organization=None):
    final_api_key = api_key or Config.OPENAI_API_KEY
    if not final_api_key:
        raise ValueError("OPENAI_API_KEY is not set. Please check your .env file.")
    client_kwargs = {"api_key": final_api_key}
    if organization:
        client_kwargs["organization"] = organization
    client = OpenAI(**client_kwargs)
    return client, {}

class OpenAIService:
    def __init__(self):
        self.client, _ = create_openai_client()
        self.model = Config.DEFAULT_OPENAI_MODEL

    def _call_api(self, messages, json_mode=False):
        try:
            response_format = {"type": "json_object"} if json_mode else None
            completion = self.client.chat.completions.create(
                model=self.model, messages=messages, response_format=response_format
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API call failed: {e}")
            return "{}" if json_mode else ""

    def summarize_reviews(self, reviews_texts, sentiment):
        if not reviews_texts: return ""
        reviews_for_prompt = "\n- ".join(reviews_texts)
        prompt = f"""Summarize key points from these {sentiment} reviews into one fluent paragraph. Focus on main themes.
Reviews:\n- {reviews_for_prompt}\n\nConcise Summary:"""
        return self._call_api([{"role": "user", "content": prompt}])

    def generate_insights(self, details, match_percentage):
        positive_summary = self.summarize_reviews(details.get('positiveReviews', []), 'positive')
        negative_summary = self.summarize_reviews(details.get('negativeReviews', []), 'negative')
        prompt = f"""As a business analyst, provide insights for the following business. Respond ONLY with a valid JSON object with "strengths" and "weaknesses" keys.
Data:
- Name: {details.get('placeName')}
- Rating: {details.get('rating')} from {details.get('totalRatings')} reviews.
- Match Score: {match_percentage}%
- Positive Summary: {positive_summary}
- Negative Summary: {negative_summary}
Based on this, determine 2-3 main strengths and weaknesses."""
        response_str = self._call_api([{"role": "user", "content": prompt}], json_mode=True)
        try:
            # Mengembalikan tuple (dict, str, str)
            return json.loads(response_str), positive_summary, negative_summary
        except json.JSONDecodeError:
            return {"strengths": [], "weaknesses": []}, positive_summary, negative_summary