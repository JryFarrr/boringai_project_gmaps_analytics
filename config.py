import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Menyimpan semua konfigurasi, kredensial, dan pengaturan aplikasi.
    """
    # Kunci API
    Maps_API_KEY = os.getenv("Maps_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SEARCHAPI_API_KEY = os.getenv("SEARCHAPI_API_KEY", "DhyaGcMobTCxHcd2GaUJ6Z5o")

    # --- PENYESUAIAN: Jumlah review untuk pencarian keyword sekarang bisa dikonfigurasi ---
    SEARCHAPI_NUM_REVIEWS = 20

    # Pengaturan default
    DEFAULT_OPENAI_MODEL = os.getenv("DEFAULT_OPENAI_MODEL", "gpt-4o-mini")
    DEFAULT_SEARCH_PARAMS = {
        'business_type': "", 'location': "", 'min_rating': 0.0,
        'min_reviews': 0, 'max_reviews': None, 'price_range': "",
        'business_hours': "anytime", 'keywords': "", 'numberOfLeads': ""
    }
    
    # Bobot untuk perhitungan persentase kecocokan
    MATCH_WEIGHTS = {'rating': 25, 'reviews': 20, 'price_range': 15, 'business_hours': 15, 'keywords': 25}
    
    # Aturan untuk pengambilan sampel review sesuai PDF
    REVIEW_SAMPLING_RULES = {
        'low': {'max': 10, 'percentage': 1.0, 'min_sample': 0, 'max_sample': 10},
        'medium': {'max': 100, 'percentage': 0.4, 'min_sample': 5, 'max_sample': 30},
        'high': {'percentage': 0.2, 'min_sample': 25, 'max_sample': 50}
    }