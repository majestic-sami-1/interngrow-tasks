import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    # Security Configurations
    API_KEY = os.environ.get("API_KEY", "cine-rec-secret-key-2026-secure")
    REQUIRE_API_KEY = os.environ.get("REQUIRE_API_KEY", "true").lower() in ("true", "1", "yes")
    ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")
    
    # Rate Limiting (Token Bucket / Sliding Window)
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_REQUESTS = 120  # requests
    RATE_LIMIT_WINDOW = 60    # seconds
    
    # Machine Learning / Recommender Parameters
    DEFAULT_HYBRID_ALPHA = 0.6  # 0.6 Content-Based, 0.4 Collaborative
    COLD_START_THRESHOLD = 3    # If user has < 3 ratings, shift weight to content & popularity
    SVD_LATENT_FACTORS = 5      # Latent features for collaborative matrix factorization
    
    # Data Paths
    DATA_DIR = BASE_DIR / "data"
    CATALOG_FILE = DATA_DIR / "catalog.json"
    USERS_FILE = DATA_DIR / "users.json"
    HISTORY_FILE = DATA_DIR / "history.json"
