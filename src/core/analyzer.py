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
        if keywords:
            keyword_n = details.get("keywordFoundCount", 0)
            if keyword_n == 0:
                score -= self.weights['keywords'] * 2 # Kurangi lebih banyak jika keyword tidak ditemukan
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
        
        # Tentukan 'meets' berdasarkan final_score
        # Jika skor adalah 0, secara otomatis 'meets' menjadi False
        if final_score == 0:
            meets = False
        else:
            # Jika ada reasoning, dan skor > 0, meets bisa tetap True
            # tergantung pada seberapa ketat kriteria Anda
            # Untuk kasus ini, jika skor > 0, kita asumsikan meets True
            # kecuali jika ada kondisi lain yang secara eksplisit menjadikannya False.
            # Namun, karena kita ingin jika 0% match tidak discrap, logika di atas sudah cukup.
            pass # meets akan tetap True jika skor > 0 dan tidak ada kondisi 'meets=False' di atas

        return final_score, meets, " ".join(reasoning) or "Meets primary criteria."

    def run(self, details, constraints):
        match_percentage, meets_constraints, reason = self._calculate_match(details, constraints)
        
        insights, positive_summary, negative_summary = {}, "", ""
        # Hanya generate insights jika memenuhi kriteria dan match_percentage > 0
        if meets_constraints and match_percentage > 0: # Cek tambahan: match_percentage harus lebih dari 0
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
        
        # Jika match_percentage adalah 0, maka meets_constraints juga harus False
        # Ini untuk memastikan logic di workflow.py benar
        if match_percentage == 0:
            meets_constraints = False

        return analysis_result, meets_constraints