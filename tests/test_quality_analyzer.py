"""
Unit Tests for Resume Quality Analyzer Module
---------------------------------------------
Tests content completeness, action verb ratios, quantifiable metric audits,
weak phrasing detection, and dimensional sub-scores.
"""

import pytest
from analyzer.quality_analyzer import analyze_resume_quality, audit_bullet_points


def test_audit_bullet_points():
    """Verify detection of metrics and action verbs in bullet points."""
    bullets = [
        "Architected scalable microservices using FastAPI, reducing API latency by 35%.",
        "Managed database cluster handling 2.5M daily requests.",
        "Responsible for fixing bugs and helping with testing.",
        "Engineered automated CI/CD pipeline cutting release time by 40%."
    ]

    audit = audit_bullet_points(bullets)
    assert audit["total_bullets"] == 4
    assert audit["metric_bullets"] == 3
    assert audit["metric_ratio"] == 0.75
    assert audit["action_verb_bullets"] >= 3
    assert len(audit["weak_bullets"]) == 1
    assert "responsible for" in audit["weak_bullets"][0][1]


def test_analyze_resume_quality_strong_resume():
    """Verify strong resume achieves high quality score with positive findings."""
    raw_text = """
    Results-driven Software Engineer with 5+ years of experience in Python and cloud systems.
    Architected high-throughput microservices using FastAPI and PostgreSQL, serving 2M daily requests.
    Optimized database queries, reducing query response times by 35%.
    Containerized legacy applications using Docker and orchestrated deployments on AWS.
    Mentored 4 junior engineers on clean code and automated pytest testing.
    """
    sections = {
        "Summary": "Results-driven Software Engineer with 5+ years of experience...",
        "Experience": "Architected high-throughput microservices...",
        "Education": "BS Computer Science",
        "Skills": "Python, FastAPI, Docker, PostgreSQL, AWS, Redis, Git, Unit Testing"
    }
    structured_data = {
        "experience": [
            {
                "title": "Senior Engineer",
                "bullets": [
                    "Architected high-throughput microservices serving 2M daily requests.",
                    "Optimized database queries, reducing response times by 35%.",
                    "Mentored 4 junior engineers on clean code."
                ]
            }
        ]
    }
    detected_skills = {"Python", "FastAPI", "Docker", "PostgreSQL", "AWS", "Redis", "Git"}

    res = analyze_resume_quality(raw_text, sections, structured_data, detected_skills)

    assert res["quality_score"] >= 80.0
    assert res["rating"] == "Strong Resume"
    assert res["breakdown"]["work_experience_achievements"] >= 75.0
    assert res["high_priority_count"] == 0


def test_analyze_resume_quality_sparse_resume():
    """Verify sparse resume with no metrics or sections flags high-priority findings."""
    raw_text = "Developer looking for work. Worked on some python apps."
    sections = {
        "Summary": "Developer looking for work",
        "Experience": "Not Detected",
        "Education": "Not Detected",
        "Skills": "Not Detected"
    }
    structured_data = {"experience": []}
    detected_skills = {"Python"}

    res = analyze_resume_quality(raw_text, sections, structured_data, detected_skills)

    assert res["quality_score"] < 50.0
    assert res["high_priority_count"] >= 2
    priorities = [f["priority"] for f in res["findings"]]
    assert "High" in priorities
