import functools
from flask import request, jsonify, current_app
from config import Config

def validate_api_key(provided_key: str) -> bool:
    """Validates provided API key against configured key."""
    if not Config.REQUIRE_API_KEY:
        return True
    if not provided_key:
        return False
    return provided_key.strip() == Config.API_KEY.strip()

def require_api_key(f):
    """
    Decorator to protect API routes with API Key authentication.
    Accepts API key from:
    1. 'X-API-Key' HTTP Header
    2. 'Authorization: Bearer <KEY>' HTTP Header
    3. 'api_key' Query parameter
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow CORS pre-flight OPTIONS requests without auth
        if request.method == "OPTIONS":
            return f(*args, **kwargs)

        if not Config.REQUIRE_API_KEY:
            return f(*args, **kwargs)

        # 1. Header: X-API-Key
        key = request.headers.get("X-API-Key")
        
        # 2. Header: Authorization Bearer
        if not key:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                key = auth_header.split(" ", 1)[1].strip()

        # 3. Query param
        if not key:
            key = request.args.get("api_key")

        if not validate_api_key(key):
            return jsonify({
                "status": "error",
                "code": 401,
                "error": "Unauthorized",
                "message": "Invalid or missing API key. Provide via 'X-API-Key' header or '?api_key=' parameter."
            }), 401

        return f(*args, **kwargs)
    return decorated_function
