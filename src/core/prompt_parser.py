import json
import re
from ..services.api_factory import create_client
from ..utils.response import error_response
from config import Config

class PromptParser:
    """
    Menganalisis prompt pengguna untuk mengekstrak parameter pencarian terstruktur.
    Menggunakan kombinasi AI dan regex untuk akurasi.
    """
    def get_system_prompt(self):
        # Isi prompt sistem tetap sama seperti sebelumnya
        return """You are an expert system for extracting structured business search parameters from user queries in both English and Indonesian. Your job is to analyze a search query and extract precise parameters for a business discovery system.

LANGUAGE HANDLING: Process queries in English and Indonesian, recognizing nuances and synonyms.

KEYWORD DETECTION: Extract explicit, implicit, and paraphrased keywords (e.g., "feels homey" -> "homey").

PRICE RANGE CLASSIFICATION: Convert any price information (e.g., "murah", "di bawah 50rb", "expensive") into standard price symbols ($, $$, $$$, $$$$).
- $ = Budget/Inexpensive
- $$ = Moderate
- $$$ = Upscale
- $$$$ = Luxury/Premium
- **Conditional Price Range:** Only extract or infer a `price_range` for 'restaurant', 'cafe', 'bar', 'hotel', or their synonyms. For all other business types (e.g., 'salon', 'workshop'), set `price_range` to an empty string ("").

OUTPUT FORMAT: Return ONLY a valid JSON object with these fields: "business_type", "location", "min_rating", "min_reviews", "max_reviews", "price_range", "business_hours", "keywords", "numberOfLeads".

RULES:
1. Return ONLY valid JSON.
2. Convert text numbers to numeric types (e.g., "four point five" -> 4.5).
3. Use default values for missing parameters as defined in the system.
4. Extract the total number of establishments to search for into "numberOfLeads".

EXAMPLES:
Input: "Find 3 luxury hotels in Surabaya that has a rating of at least 4.5 and at least 100 reviews."
Output: {"business_type":"hotels","location":"Surabaya","min_rating":4.5,"min_reviews":100,"max_reviews":null,"price_range":"$$$$","business_hours":"anytime","keywords":"luxury","numberOfLeads":3}

Input: "Cari salon kecantikan yang murah di Surabaya"
Output: {"business_type":"salon kecantikan","location":"Surabaya","min_rating":0,"min_reviews":0,"max_reviews":null,"price_range":"","business_hours":"anytime","keywords":"murah","numberOfLeads":""}
"""

    def parse_with_ai(self, prompt, client, headers, provider="openai"):
        try:
            chat_params = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }
            
            completion = client.chat.completions.create(**chat_params)
            response_text = completion.choices[0].message.content
            parsed = json.loads(response_text)

            # --- FIX: Penegakan Aturan Conditional Price Range ---
            # Daftar tipe bisnis yang boleh memiliki price range.
            ALLOWED_PRICE_RANGE_TYPES = {
                'restaurant', 'restoran', 'rumah makan', 
                'cafe', 'kafe', 'kedai kopi', 
                'bar', 
                'hotel', 'penginapan'
            }
            business_type = parsed.get("business_type", "").lower()
            
            # Periksa apakah business_type yang diekstrak ada dalam daftar yang diizinkan.
            # Menggunakan 'any' untuk menangani kasus seperti "cafe dan restoran".
            is_allowed = any(allowed_type in business_type for allowed_type in ALLOWED_PRICE_RANGE_TYPES)
            
            if not is_allowed:
                parsed["price_range"] = ""
            # --- END FIX ---

            # --- LOGIKA KONVERSI TIPE DATA YANG DIPERBAIKI ---
            min_rating_val = parsed.get("min_rating")
            parsed["min_rating"] = float(min_rating_val) if min_rating_val is not None else 0.0

            min_reviews_val = parsed.get("min_reviews")
            parsed["min_reviews"] = int(min_reviews_val) if min_reviews_val is not None else 0
            
            max_reviews_val = parsed.get("max_reviews")
            if max_reviews_val is not None:
                parsed["max_reviews"] = int(max_reviews_val)
            
            num_leads_val = parsed.get("numberOfLeads")
            if num_leads_val:
                try:
                    parsed["numberOfLeads"] = int(num_leads_val)
                except (ValueError, TypeError):
                    parsed["numberOfLeads"] = "" 
            
            return parsed
            
        except Exception as e:
            print(f"Error in parsing with AI: {e}")
            return None

    def parse(self, prompt):
        """
        Menganalisis prompt menggunakan AI sebagai prioritas utama.
        """
        client, headers, provider = create_client()
        parameters = self.parse_with_ai(prompt, client, headers, provider)

        if parameters is None:
            return {"error": "Unable to extract parameters from prompt.", "done": True}

        # Mengisi nilai default untuk parameter yang tidak ditemukan
        final_params = Config.DEFAULT_SEARCH_PARAMS.copy()
        final_params.update(parameters)
        
        return final_params