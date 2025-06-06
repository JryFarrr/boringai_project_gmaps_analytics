from ..services.openai_client import OpenAIService
from config import Config

class Analyzer:
    def __init__(self):
        self.openai = OpenAIService()
        self.weights = Config.MATCH_WEIGHTS

    def _calculate_match(self, details, constraints):
        score = 100.0; meets = True; reasoning = []
        
        # Cek Rating
        min_rating = constraints.get("min_rating")
        if min_rating and details.get("rating", 0) < min_rating:
            score -= self.weights['rating']; meets = False
            reasoning.append(f"Rating {details.get('rating')} below minimum {min_rating}.")
        
        # Cek Keyword (berdasarkan data yang sudah disiapkan)
        keywords = constraints.get("keywords")
        if keywords:
            keyword_n = details.get("keywordFoundCount", 0)
            if keyword_n == 0:
                meets = False; reasoning.append(f"Keyword '{keywords}' not found in reviews.")
                score = 0
            elif keyword_n == -1: # API Call gagal
                score -= self.weights['keywords']
                reasoning.append("Keyword search failed.")
        
        if not meets and score > 0: score -= 50
        
        return max(0, score), meets, " ".join(reasoning) or "Meets primary criteria."

    def run(self, details, constraints):
        match_percentage, meets_constraints, reason = self._calculate_match(details, constraints)
        
        insights, positive_summary, negative_summary = {}, "", ""
        if meets_constraints and match_percentage > 50:
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
        
        return analysis_result, meets_constraints