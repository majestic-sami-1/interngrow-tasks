from flask import Blueprint, jsonify, request, current_app
from security import require_api_key, rate_limit, sanitize_string, validate_rating

users_bp = Blueprint("users", __name__)

@users_bp.route("/users", methods=["GET"])
@rate_limit
@require_api_key
def list_users():
    """Lists all available user personas."""
    users = current_app.data_service.get_users()
    summaries = [
        {
            "id": u["id"],
            "name": u["name"],
            "avatar": u.get("avatar"),
            "bio": u.get("bio"),
            "preferred_genres": u.get("preferred_genres", []),
            "ratings_count": len(u.get("ratings", {})),
            "watchlist_count": len(u.get("watchlist", []))
        }
        for u in users
    ]
    return jsonify({
        "status": "success",
        "total": len(summaries),
        "users": summaries
    })

@users_bp.route("/users/<user_id>", methods=["GET"])
@rate_limit
@require_api_key
def get_user(user_id: str):
    """Retrieves full profile for a specific user."""
    clean_id = sanitize_string(user_id)
    user = current_app.data_service.get_user_by_id(clean_id)
    if not user:
        return jsonify({"status": "error", "message": f"User '{clean_id}' not found"}), 404

    return jsonify({
        "status": "success",
        "user": user
    })

@users_bp.route("/users/<user_id>/profile", methods=["GET"])
@rate_limit
@require_api_key
def get_user_profile_analysis(user_id: str):
    """
    User Profile Analysis:
    Returns genre affinity distribution, taste diversity index, rating patterns,
    favorite themes, and recent activity.
    """
    clean_id = sanitize_string(user_id)
    analysis = current_app.data_service.analyze_user_profile(clean_id)
    if not analysis:
        return jsonify({"status": "error", "message": f"User '{clean_id}' not found"}), 404

    return jsonify({
        "status": "success",
        "profile_analysis": analysis
    })

@users_bp.route("/users/<user_id>/rate", methods=["POST"])
@rate_limit
@require_api_key
def submit_rating(user_id: str):
    """
    Submits a rating for an item. Updates user profile and re-trains/refreshes
    the collaborative filtering model in real-time.
    """
    clean_uid = sanitize_string(user_id)
    data = request.get_json(silent=True) or {}
    
    item_id = sanitize_string(data.get("item_id"))
    raw_rating = data.get("rating")
    valid_rating = validate_rating(raw_rating)

    if not item_id:
        return jsonify({"status": "error", "message": "Missing 'item_id'"}), 400
    if valid_rating is None:
        return jsonify({"status": "error", "message": "Rating must be a number between 0.5 and 5.0"}), 400

    result = current_app.data_service.add_user_rating(clean_uid, item_id, valid_rating)
    if not result.get("success"):
        return jsonify({"status": "error", "message": result.get("error")}), 404

    # Real-time refresh of collaborative model with new rating matrix
    current_app.hybrid_recommender.refresh_user_data(current_app.data_service.get_users())

    return jsonify({
        "status": "success",
        "message": f"Recorded rating {valid_rating} ★ for {item_id}",
        "ratings_count": result.get("ratings_count")
    })

@users_bp.route("/users/<user_id>/watchlist", methods=["POST"])
@rate_limit
@require_api_key
def toggle_watchlist(user_id: str):
    """Toggles saving an item to user's watchlist."""
    clean_uid = sanitize_string(user_id)
    data = request.get_json(silent=True) or {}
    item_id = sanitize_string(data.get("item_id"))

    if not item_id:
        return jsonify({"status": "error", "message": "Missing 'item_id'"}), 400

    result = current_app.data_service.toggle_watchlist(clean_uid, item_id)
    if not result.get("success"):
        return jsonify({"status": "error", "message": result.get("error")}), 404

    return jsonify({
        "status": "success",
        "in_watchlist": result.get("in_watchlist"),
        "watchlist_count": result.get("watchlist_count")
    })
