import json
import math
import threading
from datetime import datetime, timezone
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import Config

class DataService:
    """
    Manages loading, updating, and saving catalog, users, and recommendation logs.
    Provides deep User Profile Analysis and statistical insights.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.catalog = []
        self.users = []
        self.history = []
        
        self.load_data()

    def load_data(self):
        """Loads data from JSON files."""
        with self.lock:
            with open(Config.CATALOG_FILE, "r", encoding="utf-8") as f:
                self.catalog = json.load(f)

            with open(Config.USERS_FILE, "r", encoding="utf-8") as f:
                self.users = json.load(f)

            with open(Config.HISTORY_FILE, "r", encoding="utf-8") as f:
                self.history = json.load(f)

    def save_users(self):
        """Persists users to file."""
        with open(Config.USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.users, f, indent=2)

    def save_history(self):
        """Persists history logs to file."""
        with open(Config.HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

    def get_catalog(self) -> List[Dict[str, Any]]:
        return self.catalog

    def get_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        return next((i for i in self.catalog if i["id"] == item_id), None)

    def get_users(self) -> List[Dict[str, Any]]:
        return self.users

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return next((u for u in self.users if u["id"] == user_id), None)

    def get_history(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        with self.lock:
            if user_id:
                filtered = [h for h in self.history if h.get("user_id") == user_id]
            else:
                filtered = self.history
            return sorted(filtered, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    def log_recommendation(
        self,
        user_id: str,
        item_id: str,
        item_title: str,
        model_type: str,
        score: float,
        status: str = "served",
        reasons: Optional[List[str]] = None
    ):
        """Appends a new recommendation or interaction entry to the history log."""
        with self.lock:
            now_dt = datetime.now(timezone.utc)
            entry = {
                "id": f"rec-{int(now_dt.timestamp() * 1000)}",
                "user_id": user_id,
                "item_id": item_id,
                "item_title": item_title,
                "model_type": model_type,
                "score": round(score, 3),
                "timestamp": now_dt.isoformat().replace("+00:00", "Z"),
                "status": status,
                "reasons": reasons or []
            }
            self.history.insert(0, entry)
            # Keep history within reasonable size
            if len(self.history) > 300:
                self.history = self.history[:300]
            self.save_history()

    def add_user_rating(self, user_id: str, item_id: str, rating: float) -> Dict[str, Any]:
        """Records or updates a user rating and adds to their activity history."""
        with self.lock:
            user = next((u for u in self.users if u["id"] == user_id), None)
            item = self.get_item_by_id(item_id)
            if not user or not item:
                return {"success": False, "error": "User or Item not found"}

            if "ratings" not in user:
                user["ratings"] = {}
            user["ratings"][item_id] = round(rating, 1)

            if "history" not in user:
                user["history"] = []
            
            now_dt = datetime.now(timezone.utc)
            user["history"].append({
                "item_id": item_id,
                "item_title": item["title"],
                "action": "rated",
                "score": round(rating, 1),
                "timestamp": now_dt.isoformat().replace("+00:00", "Z")
            })

            # Also log to global recommendation history
            self.history.insert(0, {
                "id": f"rec-{int(now_dt.timestamp() * 1000)}",
                "user_id": user_id,
                "item_id": item_id,
                "item_title": item["title"],
                "model_type": "User Interaction",
                "score": round(rating / 5.0, 3),
                "timestamp": now_dt.isoformat().replace("+00:00", "Z"),
                "status": f"rated_{int(rating)}stars",
                "reasons": [f"Rated {rating} ★ by {user['name']}"]
            })

            self.save_users()
            self.save_history()

            return {"success": True, "ratings_count": len(user["ratings"])}

    def toggle_watchlist(self, user_id: str, item_id: str) -> Dict[str, Any]:
        """Toggles an item in the user's watchlist."""
        with self.lock:
            user = next((u for u in self.users if u["id"] == user_id), None)
            item = self.get_item_by_id(item_id)
            if not user or not item:
                return {"success": False, "error": "User or Item not found"}

            if "watchlist" not in user:
                user["watchlist"] = []

            if item_id in user["watchlist"]:
                user["watchlist"].remove(item_id)
                action = "removed_from_watchlist"
                in_watchlist = False
            else:
                user["watchlist"].append(item_id)
                action = "added_to_watchlist"
                in_watchlist = True

            now_dt = datetime.now(timezone.utc)
            self.history.insert(0, {
                "id": f"rec-{int(now_dt.timestamp() * 1000)}",
                "user_id": user_id,
                "item_id": item_id,
                "item_title": item["title"],
                "model_type": "Watchlist Action",
                "score": 1.0 if in_watchlist else 0.0,
                "timestamp": now_dt.isoformat().replace("+00:00", "Z"),
                "status": action,
                "reasons": [f"{'Saved to' if in_watchlist else 'Removed from'} watchlist by {user['name']}"]
            })

            self.save_users()
            self.save_history()
            return {"success": True, "in_watchlist": in_watchlist, "watchlist_count": len(user["watchlist"])}

    def analyze_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Deep User Profile Analysis:
        - Genre affinity distribution & radar percentages
        - Average rating, rating variance, count
        - Taste Diversity Index (Shannon Entropy)
        - Novelty / Discovery Index
        - Preferred directors & themes
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        ratings = user.get("ratings", {})
        rated_items = [self.get_item_by_id(iid) for iid in ratings.keys() if self.get_item_by_id(iid)]

        # 1. Genre Affinity Calculation
        genre_scores = defaultdict(float)
        genre_counts = defaultdict(int)
        total_affinity_weight = 0.0

        for item in rated_items:
            rating = ratings.get(item["id"], 3.0)
            weight = max(0.1, rating)
            for genre in item.get("genres", []):
                genre_scores[genre] += weight
                genre_counts[genre] += 1
                total_affinity_weight += weight

        genre_affinity = []
        for genre, score in sorted(genre_scores.items(), key=lambda x: x[1], reverse=True):
            pct = round((score / total_affinity_weight) * 100, 1) if total_affinity_weight > 0 else 0
            avg_g_rating = round(score / genre_counts[genre], 2) if genre_counts[genre] > 0 else 0
            genre_affinity.append({
                "genre": genre,
                "affinity_percentage": pct,
                "count": genre_counts[genre],
                "avg_rating": avg_g_rating
            })

        # 2. Diversity Score (Shannon Entropy normalized to [0, 100])
        num_genres = len(genre_affinity)
        if num_genres > 1 and total_affinity_weight > 0:
            probs = [g["affinity_percentage"] / 100.0 for g in genre_affinity if g["affinity_percentage"] > 0]
            entropy = -sum(p * math.log(p) for p in probs)
            max_entropy = math.log(num_genres)
            diversity_score = int(round((entropy / max_entropy) * 100)) if max_entropy > 0 else 50
        elif num_genres == 1:
            diversity_score = 15
        else:
            diversity_score = 0

        # 3. Rating Habits
        scores_list = list(ratings.values())
        avg_rating = round(sum(scores_list) / len(scores_list), 2) if scores_list else 0.0
        five_star_count = sum(1 for s in scores_list if s >= 4.8)

        # 4. Novelty Index (Average popularity of liked items; lower popularity = higher novelty)
        if rated_items:
            avg_pop = sum(i.get("popularity", 90) for i in rated_items) / len(rated_items)
            novelty_score = int(round(100 - avg_pop * 0.7))
        else:
            novelty_score = 50

        # 5. Top Directors and Tags
        director_counter = Counter(i.get("director") for i in rated_items if i.get("director"))
        tag_counter = Counter()
        for i in rated_items:
            tag_counter.update(i.get("tags", []))

        return {
            "user_id": user["id"],
            "name": user["name"],
            "avatar": user.get("avatar"),
            "bio": user.get("bio"),
            "total_ratings": len(ratings),
            "watchlist_count": len(user.get("watchlist", [])),
            "average_rating": avg_rating,
            "five_star_count": five_star_count,
            "diversity_score": diversity_score,
            "diversity_label": "Eclectic & Diverse" if diversity_score > 70 else ("Balanced" if diversity_score > 40 else "Specialized"),
            "novelty_score": novelty_score,
            "genre_affinity": genre_affinity,
            "top_directors": [d for d, _ in director_counter.most_common(3)],
            "favorite_tags": [t for t, _ in tag_counter.most_common(6)],
            "recent_activity": user.get("history", [])[-6:][::-1]
        }
