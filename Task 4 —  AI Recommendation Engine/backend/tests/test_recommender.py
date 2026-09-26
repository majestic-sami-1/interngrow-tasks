import unittest
import json
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from config import Config
from models import ContentBasedRecommender, CollaborativeFilteringRecommender, HybridRecommender

class TestRecommendationEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        cls.api_key = Config.API_KEY
        cls.headers = {"X-API-Key": cls.api_key}

    def test_01_security_unauthorized_without_key(self):
        """Test that requests without API key are rejected with 401."""
        res = self.client.get("/api/items")
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertEqual(data.get("status"), "error")

    def test_02_security_authorized_with_key(self):
        """Test that requests with valid API key succeed."""
        res = self.client.get("/api/items", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertGreater(data.get("total", 0), 20)

    def test_03_security_headers_present(self):
        """Test that security defensive headers are injected in response."""
        res = self.client.get("/api/health")
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(res.headers.get("X-Frame-Options"), "DENY")
        self.assertIn("Content-Security-Policy", res.headers)

    def test_04_content_based_model_similarity(self):
        """Test Content-Based similar item detection for Interstellar (item-1)."""
        res = self.client.get("/api/items/item-1/similar", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(len(data.get("similar_items", [])) > 0)
        top_sim = data["similar_items"][0]
        self.assertIn("item", top_sim)
        self.assertGreater(top_sim["similarity_score"], 0.0)
        self.assertTrue(len(top_sim["reasons"]) > 0)

    def test_05_collaborative_filtering_recommendations(self):
        """Test Collaborative Filtering SVD recommendations."""
        res = self.client.get("/api/recommendations?user_id=user-1&model=collaborative", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("model_used"), "Collaborative Filtering (SVD)")
        self.assertTrue(len(data.get("recommendations", [])) > 0)
        first_rec = data["recommendations"][0]
        self.assertIn("predicted_rating", first_rec)

    def test_06_hybrid_recommendation_blending(self):
        """Test Hybrid Model with custom alpha weights."""
        res_08 = self.client.get("/api/recommendations?user_id=user-1&model=hybrid&alpha=0.8", headers=self.headers)
        self.assertEqual(res_08.status_code, 200)
        data_08 = res_08.get_json()
        self.assertEqual(data_08.get("model_used"), "Hybrid Recommendation Model")
        self.assertEqual(data_08.get("alpha_used"), 0.8)
        
        # Check explainability breakdown
        first_rec = data_08["recommendations"][0]
        self.assertIn("breakdown", first_rec)
        self.assertEqual(first_rec["breakdown"]["content_weight"], "80%")
        self.assertEqual(first_rec["breakdown"]["collaborative_weight"], "20%")

    def test_07_cold_start_handling(self):
        """Test that zero-ratings user (user-5) triggers cold-start fallback."""
        res = self.client.get("/api/recommendations?user_id=user-5&model=hybrid", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("is_cold_start"))
        self.assertIsNotNone(data.get("cold_start_note"))
        self.assertTrue(len(data.get("recommendations", [])) > 0)

    def test_08_user_profile_analysis(self):
        """Test User Profile Analysis metrics (diversity, novelty, genre affinity)."""
        res = self.client.get("/api/users/user-1/profile", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        analysis = data.get("profile_analysis")
        self.assertIsNotNone(analysis)
        self.assertIn("diversity_score", analysis)
        self.assertIn("novelty_score", analysis)
        self.assertIn("genre_affinity", analysis)
        # Alex Rivera should have Sci-Fi as top affinity
        top_genre = analysis["genre_affinity"][0]["genre"]
        self.assertIn(top_genre, ["Sci-Fi", "Cyberpunk", "Adventure"])

    def test_09_recommendation_history_and_interaction(self):
        """Test logging and fetching recommendation history."""
        # 1. Fetch history
        res = self.client.get("/api/history?user_id=user-1", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("history", data)

        # 2. Log an interaction
        log_res = self.client.post("/api/history/interaction", headers=self.headers, json={
            "user_id": "user-1",
            "item_id": "item-3",
            "action": "watched"
        })
        self.assertEqual(log_res.status_code, 200)

    def test_10_rate_item_and_realtime_refresh(self):
        """Test rating submission and dynamic refresh."""
        res = self.client.post("/api/users/user-4/rate", headers=self.headers, json={
            "item_id": "item-1",
            "rating": 4.5
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")

if __name__ == "__main__":
    unittest.main()
