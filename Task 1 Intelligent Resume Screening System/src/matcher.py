"""
Candidate Matching and Scoring Engine
Computes lexical and semantic similarity between Job Descriptions and Resumes
using scikit-learn's TfidfVectorizer and Cosine Similarity, coupled with skill gap analysis.
"""

from typing import Dict, List, Any, Tuple
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .extractor import extract_skills


def calculate_tfidf_similarity(job_description: str, resume_texts: List[str]) -> List[float]:
    """
    Vectorizes the Job Description and candidate resumes using scikit-learn's TfidfVectorizer,
    and computes Cosine Similarity between the JD and each candidate resume.

    Args:
        job_description: Plain text of the target job description.
        resume_texts: List of candidate resume plain texts.

    Returns:
        List of cosine similarity scores as percentages (0.0% to 100.0%).
    """
    if not job_description or not resume_texts:
        return [0.0] * len(resume_texts)

    # Clean text representation
    corpus = [job_description] + resume_texts

    # Use unigram and bigram TF-IDF with English stop word removal and sublinear scaling
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
        max_df=1.0,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except Exception:
        # Fallback if vocabulary is completely empty or trivial
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)

    jd_vector = tfidf_matrix[0:1]
    resume_vectors = tfidf_matrix[1:]

    # Compute cosine similarity between JD and all candidate vectors
    similarity_matrix = cosine_similarity(jd_vector, resume_vectors)

    # Convert to percentage and clamp between 0.0 and 100.0
    scores = []
    for val in similarity_matrix[0]:
        pct = max(0.0, min(100.0, float(val) * 100.0))
        scores.append(round(pct, 2))

    return scores


def analyze_skill_gap(jd_skills: List[str], resume_skills: List[str]) -> Dict[str, Any]:
    """
    Performs a side-by-side skill gap comparison between required JD skills
    and detected candidate skills.

    Args:
        jd_skills: List of required skills identified in the Job Description.
        resume_skills: List of skills detected in the candidate's resume.

    Returns:
        Dictionary containing:
            - matched_skills: Skills present in both JD and Resume.
            - missing_skills: Skills in JD but absent from Resume.
            - additional_skills: Skills candidate possesses beyond the JD.
            - skill_match_score: Percentage of JD skills satisfied (0 - 100%).
    """
    jd_set = set(jd_skills)
    resume_set = set(resume_skills)

    matched = sorted(list(jd_set.intersection(resume_set)))
    missing = sorted(list(jd_set.difference(resume_set)))
    additional = sorted(list(resume_set.difference(jd_set)))

    if jd_set:
        skill_match_score = round((len(matched) / len(jd_set)) * 100.0, 2)
    else:
        # If no skills specified in JD, skill score defaults to 100 if candidate has skills, else 0
        skill_match_score = 100.0 if resume_set else 0.0

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "additional_skills": additional,
        "skill_match_score": skill_match_score,
    }


def rank_candidates(
    job_description: str,
    candidates: List[Dict[str, Any]],
    tfidf_weight: float = 0.60,
    skill_weight: float = 0.40,
) -> pd.DataFrame:
    """
    Evaluates, scores, and ranks a batch of candidate resumes against a Job Description.

    Args:
        job_description: Target job description text.
        candidates: List of dicts, each having at least:
                    {'id': str, 'name': str, 'filename': str, 'text': str, 'email': str, 'phone': str}
        tfidf_weight: Weight given to TF-IDF Cosine Similarity (0.0 to 1.0).
        skill_weight: Weight given to Skill Gap Match Ratio (0.0 to 1.0).

    Returns:
        pandas.DataFrame with ranked candidates and detailed score/skill breakdowns.
    """
    if not candidates:
        return pd.DataFrame()

    # 1. Extract skills from Job Description
    jd_skills = extract_skills(job_description)

    # 2. Extract resume texts
    resume_texts = [c.get("text", "") for c in candidates]

    # 3. Compute TF-IDF Cosine Similarity scores
    tfidf_scores = calculate_tfidf_similarity(job_description, resume_texts)

    results = []
    for i, candidate in enumerate(candidates):
        resume_text = candidate.get("text", "")
        # Extract candidate skills if not already pre-extracted
        detected_skills = candidate.get("skills")
        if detected_skills is None:
            detected_skills = extract_skills(resume_text)

        # Skill gap analysis
        gap_analysis = analyze_skill_gap(jd_skills, detected_skills)
        skill_score = gap_analysis["skill_match_score"]
        tfidf_score = tfidf_scores[i]

        # Calculate weighted composite score
        # If JD has no detected skills, composite score equals TF-IDF score
        if jd_skills:
            composite_score = round(
                (tfidf_score * tfidf_weight) + (skill_score * skill_weight), 2
            )
        else:
            composite_score = tfidf_score

        results.append({
            "Candidate Name": candidate.get("name", f"Candidate {i+1}"),
            "Match Score (%)": composite_score,
            "TF-IDF Similarity (%)": tfidf_score,
            "Skill Match (%)": skill_score,
            "Matched Skills": ", ".join(gap_analysis["matched_skills"]) if gap_analysis["matched_skills"] else "None",
            "Missing Skills": ", ".join(gap_analysis["missing_skills"]) if gap_analysis["missing_skills"] else "None",
            "Detected Skills": ", ".join(detected_skills) if detected_skills else "None",
            "Matched Skills List": gap_analysis["matched_skills"],
            "Missing Skills List": gap_analysis["missing_skills"],
            "Detected Skills List": detected_skills,
            "Email": candidate.get("email") or "Not Found",
            "Phone": candidate.get("phone") or "Not Found",
            "File Name": candidate.get("filename", "Unknown"),
            "Raw Text": resume_text,
        })

    df = pd.DataFrame(results)

    # Sort descending by composite Match Score, then by TF-IDF Similarity
    df = df.sort_values(
        by=["Match Score (%)", "TF-IDF Similarity (%)"], ascending=[False, False]
    ).reset_index(drop=True)

    # Insert 1-based Rank
    df.insert(0, "Rank", range(1, len(df) + 1))

    return df
