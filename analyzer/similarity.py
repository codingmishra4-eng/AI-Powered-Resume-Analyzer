"""
Text Similarity & Match Scoring Module
--------------------------------------
Computes TF-IDF vectorization, cosine similarity, and an explainable hybrid
compatibility score combining vocabulary alignment and hard skill overlap.
"""

from typing import Dict, List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import SCORING_WEIGHTS
from analyzer.text_preprocessing import preprocess_for_tfidf


def calculate_tfidf_similarity(resume_text: str, job_description: str) -> Tuple[float, List[Tuple[str, float]]]:
    """
    Computes TF-IDF cosine similarity between resume and job description.
    Also extracts the top shared influential keywords driving the score.

    Parameters:
        resume_text (str): Raw or parsed resume text.
        job_description (str): Target job description text.

    Returns:
        Tuple[float, List[Tuple[str, float]]]:
            - cosine_score: Float between 0.0 and 1.0
            - top_contributing_words: List of (word, relative_weight) tuples
    """
    cleaned_resume = preprocess_for_tfidf(resume_text)
    cleaned_jd = preprocess_for_tfidf(job_description)

    # If either document is empty after stopword removal
    if not cleaned_resume.strip() or not cleaned_jd.strip():
        return 0.0, []

    # Configure TF-IDF with unigrams and bigrams for context capture
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=2500,
        sublinear_tf=True
    )

    tfidf_matrix = vectorizer.fit_transform([cleaned_resume, cleaned_jd])
    sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    raw_similarity = float(sim_matrix[0][0])
    # Bound within [0.0, 1.0]
    cosine_score = max(0.0, min(1.0, raw_similarity))

    # Extract top keywords contributing to the similarity
    # Multiply element-wise to see feature overlap weight
    feature_names = vectorizer.get_feature_names_out()
    vec_resume = tfidf_matrix[0].toarray()[0]
    vec_jd = tfidf_matrix[1].toarray()[0]
    overlap_weights = vec_resume * vec_jd

    top_indices = np.argsort(overlap_weights)[::-1]
    top_contributions: List[Tuple[str, float]] = []

    for idx in top_indices:
        weight = float(overlap_weights[idx])
        if weight > 0.001 and len(top_contributions) < 12:
            top_contributions.append((feature_names[idx], round(weight, 4)))

    return cosine_score, top_contributions


def calculate_similarity(resume_text: str, job_description: str) -> float:
    """
    Convenience wrapper returning only the cosine similarity score (0.0 to 1.0).
    """
    score, _ = calculate_tfidf_similarity(resume_text, job_description)
    return score


def compute_match_details(
    resume_text: str,
    job_description: str,
    skill_comparison: Dict[str, any]
) -> Dict[str, any]:
    """
    Produces an explainable, multi-dimensional match breakdown.

    Combines:
    1. TF-IDF Cosine Similarity (Textual vocabulary and thematic alignment)
    2. Skill Overlap Ratio (Explicit hard & soft skill coverage)

    Parameters:
        resume_text (str): Text extracted from resume.
        job_description (str): Pasted job description text.
        skill_comparison (Dict): Result dictionary from SkillExtractor.compare_skills().

    Returns:
        Dict with overall score, sub-scores, keyword drivers, and educational explanations.
    """
    tfidf_score, top_keywords = calculate_tfidf_similarity(resume_text, job_description)
    skill_ratio = skill_comparison.get("overlap_ratio", 0.0)

    # Weighted hybrid calculation
    w_tfidf = SCORING_WEIGHTS["tfidf_weight"]
    w_skill = SCORING_WEIGHTS["skill_weight"]

    hybrid_score = (tfidf_score * w_tfidf) + (skill_ratio * w_skill)
    overall_match_percentage = round(hybrid_score * 100, 1)

    # Determine score rating label and badge color
    if overall_match_percentage >= 80:
        fit_level = "High Match"
        fit_description = "Strong alignment with core technical qualifications and domain keywords."
    elif overall_match_percentage >= 55:
        fit_level = "Moderate Match"
        fit_description = "Good fundamental alignment; some required tools or domain areas are missing."
    else:
        fit_level = "Needs Development"
        fit_description = "Significant skill gaps or limited vocabulary alignment with the target role."

    return {
        "overall_score": overall_match_percentage,
        "fit_level": fit_level,
        "fit_description": fit_description,
        "tfidf_score_pct": round(tfidf_score * 100, 1),
        "skill_score_pct": round(skill_ratio * 100, 1),
        "tfidf_weight": int(w_tfidf * 100),
        "skill_weight": int(w_skill * 100),
        "top_shared_keywords": top_keywords,
        "disclaimer": (
            "Note: This score is a mathematical similarity index based on text overlap and "
            "detected skills. It does not evaluate past performance depth, portfolio quality, "
            "culture fit, or soft skill nuance. It should be used as a targeted preparation guide, "
            "not as an automated hiring decision."
        )
    }
