from flask import Blueprint, jsonify, request, current_app
from security import require_api_key, rate_limit, sanitize_string

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/analytics/model-comparison", methods=["GET"])
@rate_limit
@require_api_key
def compare_models():
    """
    Compares recommendations produced by Content-Based, Collaborative Filtering (SVD),
    and Hybrid models for a given user.
    """
    user_id = sanitize_string(request.args.get("user_id", "user-1"))
    user = current_app.data_service.get_user_by_id(user_id)
    if not user:
        return jsonify({"status": "error", "message": f"User '{user_id}' not found"}), 404

    ratings = user.get("ratings", {})

    content_res = current_app.hybrid_recommender.recommend(
        user_id=user_id,
        user_ratings=ratings,
        model_type="content",
        top_n=5
    )

    cf_res = current_app.hybrid_recommender.recommend(
        user_id=user_id,
        user_ratings=ratings,
        model_type="collaborative",
        top_n=5
    )

    hybrid_res = current_app.hybrid_recommender.recommend(
        user_id=user_id,
        user_ratings=ratings,
        model_type="hybrid",
        alpha=0.6,
        top_n=5
    )

    # Compute agreement/overlap
    content_ids = {r["item"]["id"] for r in content_res["recommendations"]}
    cf_ids = {r["item"]["id"] for r in cf_res["recommendations"]}
    hybrid_ids = {r["item"]["id"] for r in hybrid_res["recommendations"]}

    overlap_count = len(content_ids & cf_ids)
    jaccard_similarity = round(overlap_count / len(content_ids | cf_ids), 3) if (content_ids | cf_ids) else 0

    return jsonify({
        "status": "success",
        "user_id": user_id,
        "metrics": {
            "content_vs_cf_overlap": overlap_count,
            "jaccard_similarity": jaccard_similarity,
            "cold_start_active": hybrid_res["is_cold_start"]
        },
        "content_based": {
            "model_name": content_res["model_used"],
            "items": content_res["recommendations"]
        },
        "collaborative": {
            "model_name": cf_res["model_used"],
            "items": cf_res["recommendations"]
        },
        "hybrid": {
            "model_name": hybrid_res["model_used"],
            "items": hybrid_res["recommendations"]
        }
    })
