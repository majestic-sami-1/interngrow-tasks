import time
import threading
import functools
from flask import request, jsonify
from config import Config

class SlidingWindowRateLimiter:
    """Thread-safe sliding window in-memory rate limiter."""
    def __init__(self, max_requests: int = 120, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.history = {}
        self.lock = threading.Lock()

    def _cleanup(self, now: float):
        """Purge entries older than window."""
        cutoff = now - self.window_seconds
        for client_id in list(self.history.keys()):
            self.history[client_id] = [t for t in self.history[client_id] if t > cutoff]
            if not self.history[client_id]:
                del self.history[client_id]

    def is_allowed(self, client_id: str) -> tuple[bool, int, int]:
        """
        Returns (is_allowed, remaining_requests, retry_after_seconds)
        """
        if not Config.RATE_LIMIT_ENABLED:
            return True, self.max_requests, 0

        now = time.time()
        cutoff = now - self.window_seconds

        with self.lock:
            if client_id not in self.history:
                self.history[client_id] = []

            # Filter out timestamps outside window
            self.history[client_id] = [t for t in self.history[client_id] if t > cutoff]
            current_count = len(self.history[client_id])

            if current_count >= self.max_requests:
                earliest = self.history[client_id][0]
                retry_after = max(1, int(earliest + self.window_seconds - now))
                return False, 0, retry_after

            self.history[client_id].append(now)
            remaining = self.max_requests - (current_count + 1)
            return True, remaining, 0

_limiter = SlidingWindowRateLimiter(
    max_requests=Config.RATE_LIMIT_REQUESTS,
    window_seconds=Config.RATE_LIMIT_WINDOW
)

def rate_limit(f):
    """Decorator to apply rate limiting to endpoints."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "OPTIONS":
            return f(*args, **kwargs)

        # Identify client by IP or API Key
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()
        client_key = request.headers.get("X-API-Key") or client_ip

        allowed, remaining, retry_after = _limiter.is_allowed(client_key)
        if not allowed:
            response = jsonify({
                "status": "error",
                "code": 429,
                "error": "Too Many Requests",
                "message": f"Rate limit exceeded. Try again in {retry_after} seconds."
            })
            response.status_code = 429
            response.headers["Retry-After"] = str(retry_after)
            response.headers["X-RateLimit-Limit"] = str(Config.RATE_LIMIT_REQUESTS)
            response.headers["X-RateLimit-Remaining"] = "0"
            return response

        response = f(*args, **kwargs)
        if hasattr(response, "headers"):
            response.headers["X-RateLimit-Limit"] = str(Config.RATE_LIMIT_REQUESTS)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
    return decorated_function
