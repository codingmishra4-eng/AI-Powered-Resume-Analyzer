"""
Unit Tests for ATS Compatibility Analyzer Module
------------------------------------------------
Tests digital text verification, section heading detection,
contact completeness, and layout/formatting risk calculations.
"""

import pytest
from analyzer.ats_analyzer import analyze_ats_compatibility


def test_analyze_ats_compatibility_clean_document():
    """Verify clean document yields high ATS score and passed checks."""
    raw_text = """
    ALEX RIVERA
    alex.rivera@example.com | (555) 234-5678 | San Francisco, CA | linkedin.com/in/alex-dev

    PROFESSIONAL SUMMARY
    Senior Software Engineer with 5+ years of experience in Python, FastAPI, and Docker.

    WORK EXPERIENCE
    Senior Backend Developer | Finova Labs
    - Architected REST APIs using Python and FastAPI, improving latency by 35%.
    - Containerized legacy services with Docker.

    EDUCATION
    BS in Computer Science | Western Tech University (2020)

    TECHNICAL SKILLS
    Python, FastAPI, Docker, PostgreSQL, Redis, Git
    """

    sections = {
        "Summary": "Senior Software Engineer...",
        "Experience": "Senior Backend Developer...",
        "Education": "BS in Computer Science...",
        "Skills": "Python, FastAPI, Docker..."
    }

    contacts = {
        "email": "alex.rivera@example.com",
        "phone": "(555) 234-5678",
        "location": "San Francisco, CA",
        "linkedin": "linkedin.com/in/alex-dev",
        "github": None
    }

    res = analyze_ats_compatibility(
        raw_text=raw_text,
        parsed_sections=sections,
        contact_info=contacts,
        page_count=1,
        file_name="resume.pdf"
    )

    assert res["ats_score"] >= 80.0
    assert res["score_category"] == "High ATS Compatibility"
    assert len(res["passed_checks"]) >= 4
    assert len(res["risk_checks"]) == 0


def test_analyze_ats_compatibility_scanned_image_risk():
    """Verify scanned document with minimal text produces risk check and low score."""
    raw_text = "   "
    sections = {"Summary": "Not Detected", "Experience": "Not Detected"}
    contacts = {"email": None, "phone": None}

    res = analyze_ats_compatibility(
        raw_text=raw_text,
        parsed_sections=sections,
        contact_info=contacts,
        page_count=2,
        file_name="scanned_resume.pdf"
    )

    assert res["ats_score"] < 40.0
    assert any("Scanned" in r["title"] for r in res["risk_checks"])


def test_analyze_ats_compatibility_missing_email_and_headings():
    """Verify missing email and missing core sections trigger appropriate ATS risks."""
    raw_text = "John Doe. Contact via LinkedIn. Developer with Python skills." * 15
    sections = {
        "Summary": "Developer with Python skills",
        "Experience": "Not Detected",
        "Education": "Not Detected",
        "Skills": "Not Detected"
    }
    contacts = {"email": None, "phone": None, "linkedin": "linkedin.com/in/johndoe"}

    res = analyze_ats_compatibility(
        raw_text=raw_text,
        parsed_sections=sections,
        contact_info=contacts,
        page_count=1,
        file_name="cv.pdf"
    )

    assert any("Email" in r["title"] for r in res["risk_checks"])
    assert any("Experience" in r["title"] for r in res["risk_checks"])
    assert len(res["prioritized_fixes"]) >= 2
