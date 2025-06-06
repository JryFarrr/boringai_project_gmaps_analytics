from config import Config

class Formatter:
    """Memformat data ke dalam struktur yang konsisten."""
    def format_place_details(self, details):
        reviews = details.get('reviews_from_searchapi', [])
        
        positive_reviews = self._sample_reviews([r for r in reviews if r.get('rating', 0) >= 4])
        negative_reviews = self._sample_reviews([r for r in reviews if r.get('rating', 0) < 4])

        return {
            "placeId": details.get('place_id'),
            "placeName": details.get('name'),
            "address": details.get('formatted_address'),
            "contact": {
                "phone": details.get('formatted_phone_number'),
                "website": details.get('website')
            },
            "rating": details.get('rating'),
            "totalRatings": details.get('user_ratings_total'),
            "priceRange": self._map_price_level(details.get('price_level')),
            "businessHours": details.get('opening_hours', {}).get('weekday_text', []),
            "businessType": details.get('types', []),
            "positiveReviews": [r.get('text', '') for r in positive_reviews],
            "negativeReviews": [r.get('text', '') for r in negative_reviews]
        }
    
    def _map_price_level(self, level):
        return "$" * level if isinstance(level, int) else ""
    
    def _sample_reviews(self, reviews):
        n = len(reviews)
        rules = Config.REVIEW_SAMPLING_RULES
        
        if n <= rules['low']['max']:
            return reviews[:rules['low']['max_sample']]
        
        elif n <= rules['medium']['max']:
            rule = rules['medium']
            size = min(max(int(n * rule['percentage']), rule['min_sample']), rule['max_sample'])
        else:
            rule = rules['high']
            size = min(max(int(n * rule['percentage']), rule['min_sample']), rule['max_sample'])
            
        return sorted(reviews, key=lambda r: r.get('unix_timestamp', 0), reverse=True)[:size]