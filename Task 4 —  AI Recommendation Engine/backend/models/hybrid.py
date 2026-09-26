from typing import List, Dict, Any, Optional
import numpy as np
from .content_based import ContentBasedRecommender
from .collaborative import CollaborativeFilteringRecommender

class HybridRecommender:
    """
    Production-grade Hybrid Recommendation Engine combining Content-Based
    and Collaborative Filtering with dynamic weight tuning, cold-start handling,
    and granular explainability.
    """
    def __init__(
        self,
        catalog: List[Dict[str, Any]],
        users: List[Dict[str, Any]],
        default_alpha: float = 0.6,
        cold_start_threshold: int = 3
    ):
        self.catalog = catalog
        self.users = users
        self.default_alpha = default_alpha
        self.cold_start_threshold = cold_start_threshold
        
        self.item_map = {item["id"]: item for item in catalog}
        self.content_engine = ContentBasedRecommender(catalog)
        self.cf_engine = CollaborativeFilteringRecommender(catalog, users)

    def refresh_user_data(self, updated_users: List[Dict[str, Any]]):
        """Re-fits collaborative model when new ratings or users are registered."""
        self.users = updated_users
        self.cf_engine = CollaborativeFilteringRecommender(self.catalog, self.users)

    def recommend(
        self,
        user_id: str,
        user_ratings: Optional[Dict[str, float]] = None,
        model_type: str = "hybrid",
        alpha: Optional[float] = None,
        top_n: int = 12,
        exclude_rated: bool = True
    ) -> Dict[str, Any]:
        """
        Generates recommendations using the selected model type:
        - 'hybrid': Weighted combination of Content-Based and Collaborative Filtering
        - 'content': Pure Content-Based Filtering (TF-IDF & Metadata Cosine Similarity)
        - 'collaborative': Pure Collaborative Filtering (Matrix Factorization & Co-ratings)
        """
        # Resolve user ratings
        if user_ratings is None:
            user_obj = next((u for u in self.users if u["id"] == user_id), None)
            user_ratings = user_obj.get("ratings", {}) if user_obj else {}

        num_ratings = len(user_ratings)
        is_cold_start = num_ratings < self.cold_start_threshold

        # Pure Content-Based
        if model_type == "content":
            raw_recs = self.content_engine.recommend_for_user(
                user_ratings=user_ratings,
                top_n=top_n,
                exclude_rated=exclude_rated
            )
            return {
                "model_used": "Content-Based Filtering",
                "is_cold_start": is_cold_start,
                "ratings_count": num_ratings,
                "alpha_used": 1.0,
                "recommendations": [
                    {
                        "item": r["item"],
                        "score": r["content_score"],
                        "match_percentage": int(round(r["content_score"] * 100)),
                        "content_score": r["content_score"],
                        "cf_score": 0.0,
                        "reasons": r["reasons"]
                    }
                    for r in raw_recs
                ]
            }

        # Pure Collaborative Filtering
        if model_type == "collaborative":
            raw_recs = self.cf_engine.recommend_for_user(
                user_id=user_id,
                user_ratings=user_ratings,
                top_n=top_n,
                exclude_rated=exclude_rated
            )
            return {
                "model_used": "Collaborative Filtering (SVD)",
                "is_cold_start": is_cold_start,
                "ratings_count": num_ratings,
                "alpha_used": 0.0,
                "recommendations": [
                    {
                        "item": r["item"],
                        "score": r["cf_score"],
                        "match_percentage": int(round(r["cf_score"] * 100)),
                        "content_score": 0.0,
                        "cf_score": r["cf_score"],
                        "predicted_rating": r.get("predicted_rating", 4.0),
                        "reasons": r["reasons"]
                    }
                    for r in raw_recs
                ]
            }

        # Hybrid Recommendation Model
        active_alpha = self.default_alpha if alpha is None else max(0.0, min(1.0, float(alpha)))
        
        # Cold start adaptation: If user has very few ratings, shift heavily to content & popularity
        if is_cold_start:
            effective_alpha = max(active_alpha, 0.85)
            cold_start_note = "Cold-start detected: Model prioritized Content & Global Affinity"
        else:
            effective_alpha = active_alpha
            cold_start_note = None

        # Fetch candidate scores from both engines
        content_recs = self.content_engine.recommend_for_user(
            user_ratings=user_ratings,
            top_n=len(self.catalog),
            exclude_rated=exclude_rated
        )
        content_score_map = {r["item"]["id"]: (r["content_score"], r["reasons"]) for r in content_recs}

        cf_recs = self.cf_engine.recommend_for_user(
            user_id=user_id,
            user_ratings=user_ratings,
            top_n=len(self.catalog),
            exclude_rated=exclude_rated
        )
        cf_score_map = {r["item"]["id"]: (r["cf_score"], r.get("predicted_rating", 4.0), r["reasons"]) for r in cf_recs}

        # Combine scores for all non-rated candidate items
        hybrid_candidates = []
        for item in self.catalog:
            item_id = item["id"]
            if exclude_rated and item_id in user_ratings:
                continue

            c_score, c_reasons = content_score_map.get(item_id, (0.4, ["Catalog match"]))
            cf_data = cf_score_map.get(item_id, (0.4, 3.5, ["General viewer interest"]))
            cf_score = cf_data[0]
            pred_rating = cf_data[1]

            # Linear blend: alpha * content + (1 - alpha) * cf
            blended_score = (effective_alpha * c_score) + ((1.0 - effective_alpha) * cf_score)

            # Assemble explainability
            content_pct = int(round(effective_alpha * 100))
            cf_pct = 100 - content_pct
            
            reasons = []
            if c_reasons:
                reasons.append(c_reasons[0])
            if cf_data[2]:
                reasons.append(cf_data[2][0])

            explain_breakdown = {
                "content_weight": f"{content_pct}%",
                "collaborative_weight": f"{cf_pct}%",
                "content_score": round(c_score, 3),
                "cf_score": round(cf_score, 3)
            }

            hybrid_candidates.append({
                "item": item,
                "score": round(blended_score, 4),
                "match_percentage": int(round(blended_score * 100)),
                "content_score": round(c_score, 3),
                "cf_score": round(cf_score, 3),
                "predicted_rating": round(pred_rating, 1),
                "reasons": reasons,
                "breakdown": explain_breakdown
            })

        # Sort descending by blended score
        hybrid_candidates.sort(key=lambda x: x["score"], reverse=True)

        return {
            "model_used": "Hybrid Recommendation Model",
            "is_cold_start": is_cold_start,
            "cold_start_note": cold_start_note,
            "ratings_count": num_ratings,
            "alpha_used": effective_alpha,
            "configured_alpha": active_alpha,
            "recommendations": hybrid_candidates[:top_n]
        }
