from flask import Response

def add_security_headers(response: Response) -> Response:
    """Injects standard defensive HTTP security headers."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Content Security Policy (allows inline scripts/styles for UI dashboard, Google Fonts, and images)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' http: https: data: blob: 'unsafe-inline' 'unsafe-eval';"
    )
    return response
