import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

class CollaborativeFilteringRecommender:
    """
    Collaborative Filtering Recommender using Matrix Factorization via SVD
    and User-Item Collaborative Neighborhood Similarity.
    """
    def __init__(self, catalog: List[Dict[str, Any]], users: List[Dict[str, Any]], latent_factors: int = 4):
        self.catalog = catalog
        self.users = users
        self.latent_factors = latent_factors
        
        self.item_map = {item["id"]: item for item in catalog}
        self.item_ids = [item["id"] for item in catalog]
        self.user_map = {u["id"]: u for u in users}
        self.user_ids = [u["id"] for u in users]
        
        self.R = None
        self.R_predicted = None
        self.item_cf_similarity = None
        
        self.fit()

    def fit(self):
        """Constructs rating matrix, computes SVD decomposition, and item-item co-rating similarity."""
        num_users = len(self.user_ids)
        num_items = len(self.item_ids)

        if num_users == 0 or num_items == 0:
            return

        # 1. Build User-Item Matrix R
        R = np.zeros((num_users, num_items), dtype=np.float32)
        user_means = np.zeros(num_users, dtype=np.float32)
        has_ratings = np.zeros(num_users, dtype=bool)

        for u_idx, u_id in enumerate(self.user_ids):
            ratings = self.user_map[u_id].get("ratings", {})
            user_ratings_list = []
            for i_idx, i_id in enumerate(self.item_ids):
                if i_id in ratings:
                    val = float(ratings[i_id])
                    R[u_idx, i_idx] = val
                    user_ratings_list.append(val)

            if user_ratings_list:
                user_means[u_idx] = float(np.mean(user_ratings_list))
                has_ratings[u_idx] = True
            else:
                user_means[u_idx] = 3.5  # Neutral baseline

        self.R = R
        self.user_means = user_means

        # 2. Mean-center the ratings matrix
        R_demeaned = np.zeros_like(R)
        for u_idx in range(num_users):
            for i_idx in range(num_items):
                if R[u_idx, i_idx] > 0:
                    R_demeaned[u_idx, i_idx] = R[u_idx, i_idx] - user_means[u_idx]

        # 3. Matrix Factorization via SVD
        k = min(self.latent_factors, min(num_users, num_items) - 1)
        if k >= 1:
            try:
                # Truncated SVD using numpy
                U, S, Vt = np.linalg.svd(R_demeaned, full_matrices=False)
                # Keep top-k latent dimensions
                U_k = U[:, :k]
                S_k = np.diag(S[:k])
                Vt_k = Vt[:k, :]

                # Reconstruct full predicted rating matrix
                pred_demeaned = np.dot(np.dot(U_k, S_k), Vt_k)
                self.R_predicted = pred_demeaned + user_means[:, np.newaxis]
            except Exception:
                # Fallback to mean imputation if SVD fails
                self.R_predicted = np.tile(user_means[:, np.newaxis], (1, num_items))
        else:
            self.R_predicted = np.tile(user_means[:, np.newaxis], (1, num_items))

        # 4. Item-Item Collaborative Cosine Similarity
        # Columns of R represent items rated by users
        item_vectors = R.T  # (num_items x num_users)
        norms = np.linalg.norm(item_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1e-7
        norm_item_vectors = item_vectors / norms
        self.item_cf_similarity = np.dot(norm_item_vectors, norm_item_vectors.T)

    def predict_user_rating(self, user_id: str, item_id: str) -> float:
        """Predicts rating of an item for a given user in [1.0, 5.0]."""
        if item_id not in self.item_ids:
            return 3.5

        i_idx = self.item_ids.index(item_id)

        if user_id in self.user_ids:
            u_idx = self.user_ids.index(user_id)
            pred = float(self.R_predicted[u_idx, i_idx])
        else:
            # New/Unknown user baseline
            item = self.item_map.get(item_id, {})
            pred = float(item.get("rating", 7.5)) / 2.0  # Scale 10 to 5

        # Bound within valid rating range [1.0, 5.0]
        return max(1.0, min(5.0, pred))

    def recommend_for_user(
        self,
        user_id: str,
        user_ratings: Optional[Dict[str, float]] = None,
        top_n: int = 10,
        exclude_rated: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generates Top-N Collaborative Filtering recommendations for a user.
        Uses SVD latent factors if user exists, or Item-Item CF based on active ratings.
        """
        if user_ratings is None and user_id in self.user_map:
            user_ratings = self.user_map[user_id].get("ratings", {})
        elif user_ratings is None:
            user_ratings = {}

        is_known_user = user_id in self.user_ids
        num_items = len(self.item_ids)

        if is_known_user and len(user_ratings) >= 2:
            u_idx = self.user_ids.index(user_id)
            pred_scores = self.R_predicted[u_idx]
        else:
            # Cold-start / Active session user: compute score via Item-Item CF
            pred_scores = np.zeros(num_items, dtype=np.float32)
            if user_ratings:
                sim_sums = np.zeros(num_items, dtype=np.float32)
                for rated_item_id, rating in user_ratings.items():
                    if rated_item_id in self.item_ids:
                        r_idx = self.item_ids.index(rated_item_id)
                        sim_row = self.item_cf_similarity[r_idx]
                        pred_scores += sim_row * float(rating)
                        sim_sums += np.abs(sim_row)
                
                # Normalize
                mask = sim_sums > 0
                pred_scores[mask] /= sim_sums[mask]
                pred_scores[~mask] = 3.0
            else:
                # Complete cold start: use catalog popularity & rating prior
                for idx, item in enumerate(self.catalog):
                    pred_scores[idx] = (item.get("rating", 7.0) / 2.0)

        # Sort and return candidates
        sorted_indices = np.argsort(pred_scores)[::-1]
        results = []

        for idx in sorted_indices:
            item = self.catalog[idx]
            item_id = item["id"]

            if exclude_rated and item_id in user_ratings:
                continue

            raw_pred = float(pred_scores[idx])
            # Normalized score [0.0, 1.0]
            norm_score = max(0.0, min(1.0, (raw_pred - 1.0) / 4.0))

            results.append({
                "item": item,
                "cf_score": round(norm_score, 4),
                "predicted_rating": round(raw_pred, 1),
                "reasons": [
                    "Strong collaborative match with similar viewer taste profiles",
                    f"Predicted rating: {round(raw_pred, 1)} ★"
                ]
            })

            if len(results) >= top_n:
                break

        return results
