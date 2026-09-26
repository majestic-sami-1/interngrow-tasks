from flask import Blueprint, jsonify, request, current_app
from security import require_api_key, rate_limit, sanitize_string, validate_alpha

recommendations_bp = Blueprint("recommendations", __name__)

@recommendations_bp.route("/recommendations", methods=["GET"])
@rate_limit
@require_api_key
def get_recommendations():
    """
    Personalized Suggestions Engine:
    Supports Hybrid Model, Content-Based, and Collaborative Filtering.
    Tunable alpha parameter for hybrid blending.
    Automatically audits and logs generated recommendations into history.
    """
    user_id = sanitize_string(request.args.get("user_id", "user-1"))
    model_type = sanitize_string(request.args.get("model", "hybrid")).lower()
    raw_alpha = request.args.get("alpha")
    limit = min(25, max(1, int(request.args.get("limit", 12))))
    exclude_rated = request.args.get("exclude_rated", "true").lower() in ("true", "1", "yes")

    alpha = validate_alpha(raw_alpha, default=0.6) if raw_alpha is not None else None

    # Validate user exists
    user = current_app.data_service.get_user_by_id(user_id)
    if not user:
        return jsonify({"status": "error", "message": f"User '{user_id}' not found"}), 404

    recs_data = current_app.hybrid_recommender.recommend(
        user_id=user_id,
        user_ratings=user.get("ratings", {}),
        model_type=model_type,
        alpha=alpha,
        top_n=limit,
        exclude_rated=exclude_rated
    )

    # Log top 3 recommendations into audit history
    for item_rec in recs_data.get("recommendations", [])[:3]:
        current_app.data_service.log_recommendation(
            user_id=user_id,
            item_id=item_rec["item"]["id"],
            item_title=item_rec["item"]["title"],
            model_type=recs_data["model_used"],
            score=item_rec["score"],
            status="served",
            reasons=item_rec.get("reasons", [])
        )

    return jsonify({
        "status": "success",
        "user_id": user_id,
        "user_name": user["name"],
        "model_used": recs_data["model_used"],
        "is_cold_start": recs_data["is_cold_start"],
        "cold_start_note": recs_data.get("cold_start_note"),
        "alpha_used": recs_data.get("alpha_used"),
        "count": len(recs_data["recommendations"]),
        "recommendations": recs_data["recommendations"]
    })

@recommendations_bp.route("/recommendations/curated", methods=["GET"])
@rate_limit
@require_api_key
def get_curated_rails():
    """
    Returns Netflix-style organized rails for the home feed:
    - 'Top Picks For You' (Hybrid Model)
    - 'Because You Loved [Favorite Title]' (Similar Item Detection)
    - 'Trending & High Affinity'
    """
    user_id = sanitize_string(request.args.get("user_id", "user-1"))
    user = current_app.data_service.get_user_by_id(user_id)
    if not user:
        return jsonify({"status": "error", "message": f"User '{user_id}' not found"}), 404

    ratings = user.get("ratings", {})
    
    # 1. Top Picks
    hybrid_res = current_app.hybrid_recommender.recommend(
        user_id=user_id,
        user_ratings=ratings,
        model_type="hybrid",
        top_n=8
    )

    # 2. Because You Loved (Find highest rated item)
    seed_item = None
    similar_recs = []
    if ratings:
        best_item_id = max(ratings, key=ratings.get)
        seed_item = current_app.data_service.get_item_by_id(best_item_id)
        if seed_item:
            raw_sim = current_app.hybrid_recommender.content_engine.get_similar_items(best_item_id, top_n=6)
            similar_recs = [
                {
                    "item": s["item"],
                    "score": s["similarity_score"],
                    "match_percentage": s["match_percentage"],
                    "reasons": s["reasons"]
                }
                for s in raw_sim
            ]

    # 3. Trending & Popular (Popularity ranked)
    catalog = current_app.data_service.get_catalog()
    trending = sorted(catalog, key=lambda x: x.get("popularity", 0), reverse=True)[:8]

    return jsonify({
        "status": "success",
        "user_id": user_id,
        "rails": {
            "top_picks": {
                "title": "Top Picks For You",
                "subtitle": "AI Hybrid blend calibrated to your recent taste profile",
                "items": hybrid_res.get("recommendations", [])
            },
            "because_you_watched": {
                "title": f"Because You Loved {seed_item['title']}" if seed_item else "Recommended For You",
                "seed_item": seed_item,
                "items": similar_recs
            },
            "trending": {
                "title": "Trending & Critically Acclaimed",
                "subtitle": "Most popular among all global members",
                "items": [
                    {
                        "item": item,
                        "score": round(item.get("popularity", 90) / 100.0, 2),
                        "match_percentage": item.get("popularity", 90),
                        "reasons": [f"Ranked #{idx+1} in Popularity", f"{item.get('rating')} ★ on IMDb"]
                    }
                    for idx, item in enumerate(trending)
                ]
            }
        }
    })
