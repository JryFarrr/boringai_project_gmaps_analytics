from config import Config

class Formatter:
    def _sample_reviews(self, reviews, total_num_for_category):
        """
        Mengambil sampel review berdasarkan JUMLAH TOTAL review di kategori tsb.
        """
        num_to_sample = 0
        rules = Config.REVIEW_SAMPLING_RULES

        if total_num_for_category <= rules['low']['max']:
            num_to_sample = total_num_for_category
        elif total_num_for_category <= rules['medium']['max']:
            rule = rules['medium']
            num_to_sample = min(max(int(total_num_for_category * rule['percentage']), rule['min_sample']), rule['max_sample'])
        else: # > 100
            rule = rules['high']
            num_to_sample = min(max(int(total_num_for_category * rule['percentage']), rule['min_sample']), rule['max_sample'])
        
        # Urutkan review yang berhasil diambil berdasarkan waktu dan potong sejumlah num_to_sample
        sorted_reviews = sorted(reviews, key=lambda r: r.get('unix_timestamp', 0), reverse=True)
        return sorted_reviews[:num_to_sample]

    # Menerima argumen baru dari Finder
    def format_place_details(self, details, all_reviews, keyword_n, place_result):
        """
        Memformat detail mentah dan menerapkan logika sampling review yang benar.
        """
        histogram = place_result.get('reviews_histogram', {})
        total_reviews_from_keyword_search = place_result.get('reviews', 0)

        # Hitung total review positif/negatif dari histogram
        total_positive = histogram.get('4', 0) + histogram.get('5', 0)
        total_negative = histogram.get('1', 0) + histogram.get('2', 0)

        # Pisahkan review yang berhasil diambil
        positive_reviews_fetched = [r for r in all_reviews if r.get('rating', 0) >= 4]
        negative_reviews_fetched = [r for r in all_reviews if r.get('rating', 0) < 3] # Rating 3 dianggap netral

        # Terapkan sampling dengan jumlah total yang benar
        sampled_positive = self._sample_reviews(positive_reviews_fetched, total_positive)
        sampled_negative = self._sample_reviews(negative_reviews_fetched, total_negative)
        
        # Buat string untuk keywordMatch
        keyword_match_string = f"{keyword_n} out of {total_reviews_from_keyword_search} reviews mention the keyword." if keyword_n != -1 else "Keyword search API failed."

        return {
            "placeId": details.get('place_id'),
            "placeName": details.get('name'),
            "address": details.get('formatted_address'),
            "contact": {"phone": details.get('formatted_phone_number'), "website": details.get('website')},
            "rating": details.get('rating'),
            "totalRatings": details.get('user_ratings_total'),
            "priceRange": "$" * details.get('price_level', 0) if details.get('price_level') else "",
            "businessHours": details.get('opening_hours', {}).get('weekday_text', []),
            "businessType": details.get('types', []),
            "positiveReviews": [r.get('text', '') for r in sampled_positive if r.get('text')],
            "negativeReviews": [r.get('text', '') for r in sampled_negative if r.get('text')],
            # Sertakan hasil keyword match untuk digunakan Analyzer
            "keywordMatch": keyword_match_string,
            "keywordFoundCount": keyword_n
        }