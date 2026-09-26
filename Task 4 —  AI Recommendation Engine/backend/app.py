import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from security import add_security_headers
from services import DataService
from models import HybridRecommender
from routes import items_bp, users_bp, recommendations_bp, history_bp, analytics_bp

def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for decoupled frontend
    CORS(app, resources={r"/api/*": {"origins": Config.ALLOWED_ORIGINS}})

    # Attach Security Headers to all responses
    @app.after_request
    def apply_security_headers(response):
        return add_security_headers(response)

    # Initialize Core Services & ML Engine
    data_svc = DataService()
    hybrid_rec = HybridRecommender(
        catalog=data_svc.get_catalog(),
        users=data_svc.get_users(),
        default_alpha=Config.DEFAULT_HYBRID_ALPHA,
        cold_start_threshold=Config.COLD_START_THRESHOLD
    )

    app.data_service = data_svc
    app.hybrid_recommender = hybrid_rec

    # Register Blueprints under /api prefix
    app.register_blueprint(items_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/api")
    app.register_blueprint(recommendations_bp, url_prefix="/api")
    app.register_blueprint(history_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api")

    # API Root & Health Check
    @app.route("/", methods=["GET"])
    def root():
        return jsonify({
            "name": "CineMatch AI Recommendation Engine API",
            "version": "1.0.0",
            "status": "operational",
            "docs": {
                "health": "/api/health",
                "items": "/api/items",
                "similar_items": "/api/items/<id>/similar",
                "users": "/api/users",
                "user_profile": "/api/users/<id>/profile",
                "recommendations": "/api/recommendations?user_id=user-1&model=hybrid&alpha=0.6",
                "curated_rails": "/api/recommendations/curated?user_id=user-1",
                "history": "/api/history?user_id=user-1",
                "model_comparison": "/api/analytics/model-comparison?user_id=user-1"
            },
            "security": {
                "auth": "X-API-Key header required (or ?api_key= query param)",
                "rate_limiting": f"{Config.RATE_LIMIT_REQUESTS} req / {Config.RATE_LIMIT_WINDOW}s"
            }
        })

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "catalog_count": len(app.data_service.get_catalog()),
            "users_count": len(app.data_service.get_users()),
            "ml_engine": "Hybrid (Content TF-IDF + Collaborative SVD)",
            "auth_required": Config.REQUIRE_API_KEY
        })

    # Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"status": "error", "code": 404, "message": "Endpoint or resource not found"}), 404

    @app.errorhandler(500)
    def handle_internal_error(e):
        return jsonify({"status": "error", "code": 500, "message": "Internal engine processing error"}), 500

    return app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app = create_app()
    print("==================================================")
    print("CineMatch AI Recommendation Engine API")
    print("Security: API Key Required | Rate Limiting Active")
    print(f"Running on: http://127.0.0.1:{port}")
    print(f"API Key: {Config.API_KEY}")
    print("==================================================")
    app.run(host="127.0.0.1", port=port, debug=False)
