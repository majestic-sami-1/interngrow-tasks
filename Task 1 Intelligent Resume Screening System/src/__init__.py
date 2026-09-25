"""
Intelligent Resume Screening System - Core Package
InternGrow AI Track - Task 1
"""

from .parser import extract_text, extract_text_from_pdf, extract_text_from_docx
from .extractor import (
    extract_skills,
    extract_email,
    extract_phone,
    extract_candidate_name,
    categorize_skills,
    SKILL_CATEGORIES,
)
from .matcher import (
    calculate_tfidf_similarity,
    analyze_skill_gap,
    rank_candidates,
)

__all__ = [
    "extract_text",
    "extract_text_from_pdf",
    "extract_text_from_docx",
    "extract_skills",
    "extract_email",
    "extract_phone",
    "extract_candidate_name",
    "categorize_skills",
    "SKILL_CATEGORIES",
    "calculate_tfidf_similarity",
    "analyze_skill_gap",
    "rank_candidates",
]
