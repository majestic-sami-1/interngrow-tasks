from flask import Blueprint, jsonify, request, current_app
from security import require_api_key, rate_limit, sanitize_string

history_bp = Blueprint("history", __name__)

@history_bp.route("/history", methods=["GET"])
@rate_limit
@require_api_key
def get_recommendation_history():
    """
    Recommendation History:
    Returns the audit trail of served recommendations, models used,
    reasons, timestamps, and recorded user feedback actions.
    """
    user_id = sanitize_string(request.args.get("user_id"))
    limit = min(100, max(1, int(request.args.get("limit", 30))))

    history = current_app.data_service.get_history(user_id=user_id if user_id else None, limit=limit)
    return jsonify({
        "status": "success",
        "total": len(history),
        "history": history
    })

@history_bp.route("/history/interaction", methods=["POST"])
@rate_limit
@require_api_key
def log_interaction():
    """Records an interaction (e.g. click, watch, like) on a recommended title."""
    data = request.get_json(silent=True) or {}
    user_id = sanitize_string(data.get("user_id"))
    item_id = sanitize_string(data.get("item_id"))
    action = sanitize_string(data.get("action", "clicked"))

    if not user_id or not item_id:
        return jsonify({"status": "error", "message": "Missing 'user_id' or 'item_id'"}), 400

    item = current_app.data_service.get_item_by_id(item_id)
    if not item:
        return jsonify({"status": "error", "message": f"Item '{item_id}' not found"}), 404

    current_app.data_service.log_recommendation(
        user_id=user_id,
        item_id=item_id,
        item_title=item["title"],
        model_type="User Interaction",
        score=1.0,
        status=action,
        reasons=[f"User recorded action: {action}"]
    )

    return jsonify({
        "status": "success",
        "message": f"Logged '{action}' on '{item['title']}'"
    })
