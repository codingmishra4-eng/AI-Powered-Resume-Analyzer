"""
Unit Tests for Similarity & Text Processing Module
--------------------------------------------------
Tests text cleaning, stopword removal, TF-IDF vectorization,
cosine similarity, and hybrid scoring calculations.
"""

import pytest
from analyzer.text_preprocessing import clean_text, remove_stopwords, tokenize_text
from analyzer.similarity import (
    calculate_similarity,
    calculate_tfidf_similarity,
    compute_match_details,
)


def test_clean_text():
    """Test lowercasing, email removal, URL removal, and symbol handling."""
    raw = "Senior Python & C++ Dev! Contact: dev@example.com, https://myportfolio.io"
    cleaned = clean_text(raw)

    assert "senior python" in cleaned
    assert "c++" in cleaned
    assert "dev@example.com" not in cleaned
    assert "https" not in cleaned


def test_stopwords_and_tokenization():
    """Test tokenization and filtering of common English stopwords."""
    text = "the developer was coding with python and docker"
    tokens = tokenize_text(text)
    filtered = remove_stopwords(tokens)

    assert "the" not in filtered
    assert "was" not in filtered
    assert "with" not in filtered
    assert "developer" in filtered
    assert "python" in filtered
    assert "docker" in filtered


def test_similarity_identical_texts():
    """Identical non-trivial texts should produce cosine similarity of 1.0."""
    text = "Senior Python engineer building microservices with FastAPI, Docker, and PostgreSQL."
    score = calculate_similarity(text, text)
    assert pytest.approx(score, 0.01) == 1.0


def test_similarity_disparate_texts():
    """Unrelated texts should produce low similarity."""
    resume = "French pastry chef specializing in chocolate croissants and wedding cakes."
    job = "DevOps infrastructure engineer with Kubernetes, Terraform, and AWS experience."
    score = calculate_similarity(resume, job)
    assert score < 0.15


def test_similarity_empty_inputs():
    """Empty inputs should gracefully return 0.0 without errors."""
    assert calculate_similarity("", "Python Developer") == 0.0
    assert calculate_similarity("Python Developer", "") == 0.0
    assert calculate_similarity("", "") == 0.0


def test_compute_match_details_hybrid_formula():
    """Verify that hybrid match details combines TF-IDF and skill ratio correctly."""
    resume = "Python FastAPI Docker PostgreSQL developer with Git"
    job = "Python FastAPI Docker Kubernetes Redis"

    skill_comp = {
        "matched_skills": ["Python", "FastAPI", "Docker"],
        "missing_skills": ["Kubernetes", "Redis"],
        "additional_skills": ["PostgreSQL", "Git"],
        "overlap_ratio": 0.6,
        "overlap_percentage": 60.0,
        "suggested_priorities": ["Kubernetes", "Redis"],
    }

    details = compute_match_details(resume, job, skill_comp)

    assert "overall_score" in details
    assert "fit_level" in details
    assert "disclaimer" in details
    assert details["overall_score"] >= 0.0 and details["overall_score"] <= 100.0
    assert details["skill_score_pct"] == 60.0
