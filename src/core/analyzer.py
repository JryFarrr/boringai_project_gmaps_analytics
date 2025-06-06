from ..services.openai_client import OpenAIService
from ..services.searchapi import SearchApiService
from config import Config

class Analyzer:
    def __init__(self):
        self.openai = OpenAIService()
        self.searchapi = SearchApiService()
        self.weights = Config.MATCH_WEIGHTS

    def _calculate_match(self, details, constraints):
        score = 100.0; meets = True; reasoning = []
        keyword_match_info = {"n": 0, "b": 0, "string": "Keywords not specified."}
        
        min_rating = constraints.get("min_rating")
        if min_rating and details.get("rating", 0) < min_rating:
            score -= self.weights['rating']; meets = False
            reasoning.append(f"Rating {details.get('rating')} below minimum {min_rating}.")
        
        keywords = constraints.get("keywords")
        if keywords:
            place_id = details.get("placeId")
            n, b = self.searchapi.get_keyword_match_count(place_id, keywords)
            if n == -1:
                keyword_match_info["string"] = "Keyword search API failed."
                score -= self.weights['keywords']
            else:
                keyword_match_info = {"n": n, "b": b, "string": f"{n} out of {b} reviews mention the keyword."}
                if n == 0:
                    meets = False; reasoning.append(f"Keyword '{keywords}' not found in reviews.")
                    score = 0
        
        if not meets:
            if score > 0 : score -= 50
        
        return max(0, score), meets, " ".join(reasoning) or "Meets primary criteria.", keyword_match_info

    def run(self, details, constraints):
        match_percentage, meets_constraints, reason, keyword_info = self._calculate_match(details, constraints)
        
        insights = {}
        if meets_constraints and match_percentage > 50:
             insights = self.openai.generate_insights(details, match_percentage)

        analysis_result = {
            "placeName": details.get("placeName"),
            "address": details.get("address"),
            "rating": details.get("rating"),
            "totalRatings": details.get("totalRatings"),
            "matchPercentage": round(match_percentage, 2),
            "matchReasoning": reason,
            "keywordMatch": keyword_info["string"],
            # --- PENYESUAIAN: Dua baris di bawah ini dihapus dari output ---
            # "keywordCountN": keyword_info["n"], 
            # "keywordTotalB": keyword_info["b"],
            "strengths": insights.get("strengths", []),
            "weaknesses": insights.get("weaknesses", []),
            **details
        }
        
        return analysis_result, meets_constraints