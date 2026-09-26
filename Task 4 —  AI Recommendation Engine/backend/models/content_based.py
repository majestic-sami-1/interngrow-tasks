import re
import math
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple
import numpy as np

class ContentBasedRecommender:
    """
    Content-Based Recommendation Engine using custom TF-IDF Vectorization
    and Cosine Similarity across rich multi-attribute item metadata.
    """
    def __init__(self, catalog: List[Dict[str, Any]]):
        self.catalog = catalog
        self.item_map = {item["id"]: item for item in catalog}
        self.item_ids = [item["id"] for item in catalog]
        self.vocab = {}
        self.idf = {}
        self.tfidf_matrix = None
        self.item_similarity_matrix = None
        
        self._fit_transform()

    def _tokenize(self, text: str) -> List[str]:
        """Normalize and tokenize text into lowercase word tokens."""
        text = text.lower()
        tokens = re.findall(r"\b[a-z0-9\-]{2,}\b", text)
        return tokens

    def _extract_document(self, item: Dict[str, Any]) -> str:
        """
        Creates an information-rich document representation with strategic
        term weighting (e.g. repeated genres and director for higher relevance).
        """
        genres = " ".join([g.lower().replace(" ", "-") for g in item.get("genres", [])] * 3)
        tags = " ".join([t.lower().replace(" ", "-") for t in item.get("tags", [])] * 2)
        director = " ".join([d.lower().replace(" ", "-") for d in item.get("director", "").split(",")] * 3)
        cast = " ".join([c.lower().replace(" ", "-") for c in item.get("cast", [])] * 2)
        overview = item.get("overview", "")
        title = item.get("title", "") * 2
        item_type = item.get("type", "").lower()

        return f"{title} {genres} {tags} {director} {cast} {overview} {item_type}"

    def _fit_transform(self):
        """Constructs vocabulary, computes IDF, and generates L2-normalized TF-IDF matrix."""
        documents = [self._extract_document(item) for item in self.catalog]
        doc_tokens = [self._tokenize(doc) for doc in documents]
        N = len(documents)

        # 1. Build Document Frequencies (DF)
        df = defaultdict(int)
        for tokens in doc_tokens:
            unique_terms = set(tokens)
            for term in unique_terms:
                df[term] += 1

        # Filter out rare terms (df >= 1) and create vocabulary index
        self.vocab = {term: idx for idx, (term, count) in enumerate(df.items())}
        num_terms = len(self.vocab)

        # 2. Compute Smoothed IDF: log((1 + N) / (1 + df)) + 1
        self.idf = np.zeros(num_terms, dtype=np.float32)
        for term, idx in self.vocab.items():
            self.idf[idx] = math.log((1.0 + N) / (1.0 + df[term])) + 1.0

        # 3. Compute TF-IDF Matrix (N items x V terms)
        matrix = np.zeros((N, num_terms), dtype=np.float32)
        for i, tokens in enumerate(doc_tokens):
            if not tokens:
                continue
            tf_counts = Counter(tokens)
            total_tokens = len(tokens)
            for term, count in tf_counts.items():
                if term in self.vocab:
                    term_idx = self.vocab[term]
                    # Augmented TF to prevent bias towards long descriptions
                    tf = 0.5 + 0.5 * (count / max(tf_counts.values()))
                    matrix[i, term_idx] = tf * self.idf[term_idx]

            # L2 normalization for each item vector
            norm = np.linalg.norm(matrix[i])
            if norm > 0:
                matrix[i] /= norm

        self.tfidf_matrix = matrix

        # 4. Item-Item Cosine Similarity Matrix (N x N)
        # Since matrix is L2 normalized, dot product directly equals cosine similarity
        self.item_similarity_matrix = np.dot(self.tfidf_matrix, self.tfidf_matrix.T)

    def get_similar_items(self, item_id: str, top_n: int = 6) -> List[Dict[str, Any]]:
        """
        Returns the most similar items to a given item ID based on content features.
        Includes explainability breakdown (shared genres, tags, director).
        """
        if item_id not in self.item_ids:
            return []

        idx = self.item_ids.index(item_id)
        sim_scores = self.item_similarity_matrix[idx].copy()
        sim_scores[idx] = -1.0  # Exclude self

        top_indices = np.argsort(sim_scores)[::-1][:top_n]
        source_item = self.item_map[item_id]

        results = []
        for i in top_indices:
            score = float(sim_scores[i])
            if score <= 0:
                continue
            target_item = self.catalog[i]

            # Find matching attributes for explainability
            shared_genres = list(set(source_item.get("genres", [])) & set(target_item.get("genres", [])))
            shared_tags = list(set(source_item.get("tags", [])) & set(target_item.get("tags", [])))
            same_director = (
                source_item.get("director") == target_item.get("director")
                and bool(source_item.get("director"))
            )

            reasons = []
            if same_director:
                reasons.append(f"Directed by {source_item['director']}")
            if shared_genres:
                reasons.append(f"Shared genres: {', '.join(shared_genres)}")
            if shared_tags:
                reasons.append(f"Themes: {', '.join(shared_tags[:3])}")

            results.append({
                "item": target_item,
                "similarity_score": round(score, 4),
                "match_percentage": int(round(score * 100)),
                "reasons": reasons
            })

        return results

    def recommend_for_user(
        self,
        user_ratings: Dict[str, float],
        top_n: int = 10,
        exclude_rated: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Creates user profile vector from rated items, computes cosine similarity
        with all candidate items, and returns top-N ranked items.
        """
        if not user_ratings:
            # Cold-start / fallback to popularity-weighted catalog
            sorted_items = sorted(self.catalog, key=lambda x: x.get("popularity", 0), reverse=True)
            return [
                {
                    "item": item,
                    "content_score": round(item.get("popularity", 50) / 100.0, 4),
                    "reasons": ["Popular among all viewers", f"Top rated {item.get('rating', '')}/10"]
                }
                for item in sorted_items[:top_n]
            ]

        # 1. Build User Profile Vector: weighted average of item vectors
        num_terms = self.tfidf_matrix.shape[1]
        user_vector = np.zeros(num_terms, dtype=np.float32)
        total_weight = 0.0

        for item_id, rating in user_ratings.items():
            if item_id in self.item_ids:
                idx = self.item_ids.index(item_id)
                # Centered rating weight: ratings > 3.0 are positive affinity, < 3.0 are negative
                weight = float(rating) - 2.5
                user_vector += weight * self.tfidf_matrix[idx]
                total_weight += abs(weight)

        if total_weight > 0:
            user_vector /= total_weight

        # L2-normalize user vector
        user_norm = np.linalg.norm(user_vector)
        if user_norm > 0:
            user_vector /= user_norm
            scores = np.dot(self.tfidf_matrix, user_vector)
        else:
            scores = np.zeros(len(self.catalog), dtype=np.float32)

        # 2. Rank candidates
        scored_indices = np.argsort(scores)[::-1]
        recommendations = []

        # Find favorite genres for explainability
        genre_counts = Counter()
        for i_id, r in user_ratings.items():
            if r >= 4.0 and i_id in self.item_map:
                genre_counts.update(self.item_map[i_id].get("genres", []))
        top_fav_genres = [g for g, _ in genre_counts.most_common(2)]

        for idx in scored_indices:
            candidate_item = self.catalog[idx]
            item_id = candidate_item["id"]

            if exclude_rated and item_id in user_ratings:
                continue

            score = float(scores[idx])
            # Normalize score into [0, 1] range for stability
            norm_score = max(0.0, min(1.0, (score + 1.0) / 2.0))

            reasons = []
            matching_genres = [g for g in candidate_item.get("genres", []) if g in top_fav_genres]
            if matching_genres:
                reasons.append(f"Matches your affinity for {', '.join(matching_genres)}")
            else:
                reasons.append(f"High metadata alignment with your watch history")

            recommendations.append({
                "item": candidate_item,
                "content_score": round(norm_score, 4),
                "reasons": reasons
            })

            if len(recommendations) >= top_n:
                break

        return recommendations
