from ..services.openai_client import OpenAIService
from config import Config

class Analyzer:
    def __init__(self):
        self.openai = OpenAIService()
        self.weights = Config.MATCH_WEIGHTS

    def _calculate_match(self, details, constraints):
        score = 100.0
        meets = True
        reasoning = []

        # Cek Rating
        min_rating = constraints.get("min_rating")
        if min_rating is not None and details.get("rating", 0) < min_rating:
            score -= self.weights['rating']
            # meets = False # Meets akan disimpulkan di akhir berdasarkan skor
            reasoning.append(f"Rating {details.get('rating')} below minimum {min_rating}.")

        # Cek Reviews (min_reviews dan max_reviews)
        min_reviews = constraints.get("min_reviews")
        if min_reviews is not None and details.get("totalRatings", 0) < min_reviews:
            score -= self.weights['reviews']
            # meets = False
            reasoning.append(f"Total reviews {details.get('totalRatings')} below minimum {min_reviews}.")
        
        max_reviews = constraints.get("max_reviews")
        if max_reviews is not None and details.get("totalRatings", 0) > max_reviews:
            score -= self.weights['reviews']
            # meets = False
            reasoning.append(f"Total reviews {details.get('totalRatings')} above maximum {max_reviews}.")

        # Cek Price Range
        price_range = constraints.get("price_range")
        if price_range and details.get("priceRange") != price_range:
            if not details.get("priceRange") and price_range:
                score -= self.weights['price_range']
                # meets = False
                reasoning.append(f"Price range '{details.get('priceRange') or 'N/A'}' does not match required '{price_range}'.")
            elif details.get("priceRange") and details.get("priceRange") != price_range:
                score -= self.weights['price_range']
                # meets = False
                reasoning.append(f"Price range '{details.get('priceRange')}' does not match required '{price_range}'.")


        # Cek Business Hours
        business_hours = constraints.get("business_hours")
        if business_hours and business_hours.lower() != "anytime":
            is_open_match = False
            for hour_text in details.get('businessHours', []):
                if business_hours.lower() in hour_text.lower():
                    is_open_match = True
                    break
            if not is_open_match:
                score -= self.weights['business_hours']
                # meets = False
                reasoning.append(f"Business hours do not match required '{business_hours}'.")

        # Cek Keyword
        keywords = constraints.get("keywords")
        keyword_not_found = False
        if keywords:
            keyword_n = details.get("keywordFoundCount", 0)
            if keyword_n == 0:
                keyword_not_found = True
                reasoning.append(f"Keyword '{keywords}' not found in reviews.")
            elif keyword_n == -1: # API Call gagal
                score -= self.weights['keywords']
                reasoning.append("Keyword search failed.")
        
        # Cek Address
        location = constraints.get("location")
        if location and not details.get("address", "").lower().count(location.lower()):
            score -= self.weights['address']
            # meets = False
            reasoning.append(f"Address '{details.get('address')}' does not contain required location '{location}'.")

        # Pastikan skor tidak negatif
        final_score = max(0, score)

        if keyword_not_found:
            final_score = 0
        
        # Tentukan 'meets' berdasarkan final_score
        if final_score == 0:
            meets = False

        return final_score, meets, " ".join(reasoning) or "Meets primary criteria."

    def run(self, details, constraints):
        match_percentage, _, reason = self._calculate_match(details, constraints)
        
        insights, positive_summary, negative_summary = {}, "", ""
        # Hanya generate insights jika match_percentage > 0
        if match_percentage > 0:
             insights, positive_summary, negative_summary = self.openai.generate_insights(details, match_percentage)

        # Hapus data mentah yang tidak perlu dari output akhir
        final_details = details.copy()
        final_details.pop("keywordFoundCount", None)
        final_details.pop("positiveReviews", None)
        final_details.pop("negativeReviews", None)

        analysis_result = {
            **final_details,
            "matchPercentage": round(match_percentage, 2),
            "matchReasoning": reason,
            "strengths": insights.get("strengths", []),
            "weaknesses": insights.get("weaknesses", []),
            "summaryPositive": positive_summary,
            "summaryNegative": negative_summary,
        }
        
        return analysis_result