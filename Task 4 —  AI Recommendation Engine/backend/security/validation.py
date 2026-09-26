import re
from typing import Any, Optional

def sanitize_string(val: Any, max_len: int = 150) -> str:
    """Strips dangerous characters and limits length."""
    if val is None:
        return ""
    text = str(val).strip()
    # Strip HTML tags
    clean = re.sub(r"<[^>]*>", "", text)
    # Return within limit
    return clean[:max_len]

def validate_rating(val: Any) -> Optional[float]:
    """Validates that a rating is between 1.0 and 5.0."""
    try:
        r = float(val)
        if 0.5 <= r <= 5.0:
            return round(r, 1)
        return None
    except (ValueError, TypeError):
        return None

def validate_alpha(val: Any, default: float = 0.6) -> float:
    """Validates hybrid weighting alpha between 0.0 and 1.0."""
    try:
        a = float(val)
        return max(0.0, min(1.0, a))
    except (ValueError, TypeError):
        return default
