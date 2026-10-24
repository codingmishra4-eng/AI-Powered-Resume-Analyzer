"""
Unit Tests for Recommendations Module
-------------------------------------
Tests rule-based generation of actionable resume improvements,
metric checks, action verb recommendations, and structure validation.
"""

import pytest
from analyzer.recommendations import (
    check_quantifiable_metrics,
    check_weak_phrasing,
    generate_recommendations,
)


def test_check_quantifiable_metrics():
    """Verify detection of percentages, request metrics, and quantifiable results."""
    text_with_metrics = (
        "Improved API response time by 35%. Handled 2M requests daily. "
        "Reduced costs by $50K and managed 10 users."
    )
    info = check_quantifiable_metrics(text_with_metrics)
    assert info["has_metrics"] is True
    assert info["count"] >= 3

    text_without_metrics = "Worked on developing various backend features and fixed issues."
    info_empty = check_quantifiable_metrics(text_without_metrics)
    assert info_empty["has_metrics"] is False


def test_check_weak_phrasing():
    """Verify identification of passive or weak bullet phrases."""
    text = "I was responsible for maintaining servers and helped with testing."
    weak = check_weak_phrasing(text)
    assert "responsible for" in weak
    assert "helped with" in weak


def test_generate_recommendations():
    """Verify end-to-end recommendation rules generate actionable advice."""
    resume_text = "Junior developer with no metrics. Responsible for bug fixes."
    sections = {
        "Summary": "Junior developer",
        "Experience": "Bug fixes",
        "Education": "Not Detected",
        "Skills": "Python",
        "Projects": "Not Detected",
        "Certifications": "Not Detected",
    }
    contact_info = {"email": "dev@test.com", "phone": None, "linkedin": None, "github": None}
    skill_comp = {
        "missing_skills": ["Docker", "PostgreSQL", "FastAPI"],
        "suggested_priorities": ["Docker", "PostgreSQL"],
    }

    recs = generate_recommendations(resume_text, sections, contact_info, skill_comp)
    assert len(recs) >= 3

    titles = [r["title"] for r in recs]
    # Should recommend addressing missing skills
    assert any("Missing Skills" in t for t in titles)
    # Should recommend quantifiable metrics
    assert any("Measurable" in t for t in titles)
    # Should recommend adding missing sections
    assert any("Missing Core Section" in t for t in titles)
    # Should recommend completing contact links
    assert any("Contact Links" in t for t in titles)
