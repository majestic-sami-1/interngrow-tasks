from flask import Blueprint, jsonify, request, current_app
from security import require_api_key, rate_limit, sanitize_string

items_bp = Blueprint("items", __name__)

@items_bp.route("/items", methods=["GET"])
@rate_limit
@require_api_key
def get_items():
    """Returns catalog items with optional filtering by genre, search query, or featured status."""
    data_svc = current_app.data_service
    catalog = data_svc.get_catalog()

    genre = sanitize_string(request.args.get("genre", ""))
    search = sanitize_string(request.args.get("search", "")).lower()
    item_type = sanitize_string(request.args.get("type", ""))
    featured = request.args.get("featured", "").lower() in ("true", "1")

    filtered = catalog
    if genre:
        filtered = [i for i in filtered if any(g.lower() == genre.lower() for g in i.get("genres", []))]
    if item_type:
        filtered = [i for i in filtered if i.get("type", "").lower() == item_type.lower()]
    if search:
        filtered = [
            i for i in filtered
            if search in i.get("title", "").lower()
            or search in i.get("director", "").lower()
            or any(search in c.lower() for c in i.get("cast", []))
            or any(search in t.lower() for t in i.get("tags", []))
        ]
    if featured:
        filtered = [i for i in filtered if i.get("featured", False)]

    return jsonify({
        "status": "success",
        "total": len(filtered),
        "items": filtered
    })

@items_bp.route("/items/<item_id>", methods=["GET"])
@rate_limit
@require_api_key
def get_item(item_id: str):
    """Returns detailed information for a specific movie or show."""
    clean_id = sanitize_string(item_id)
    item = current_app.data_service.get_item_by_id(clean_id)
    if not item:
        return jsonify({"status": "error", "message": f"Item '{clean_id}' not found"}), 404

    return jsonify({
        "status": "success",
        "item": item
    })

@items_bp.route("/items/<item_id>/similar", methods=["GET"])
@rate_limit
@require_api_key
def get_similar_items(item_id: str):
    """Detects and returns similar items ('More Like This') using content similarity."""
    clean_id = sanitize_string(item_id)
    limit = min(12, max(1, int(request.args.get("limit", 6))))

    similar = current_app.hybrid_recommender.content_engine.get_similar_items(clean_id, top_n=limit)
    if not similar:
        item = current_app.data_service.get_item_by_id(clean_id)
        if not item:
            return jsonify({"status": "error", "message": f"Item '{clean_id}' not found"}), 404

    return jsonify({
        "status": "success",
        "item_id": clean_id,
        "count": len(similar),
        "similar_items": similar
    })
