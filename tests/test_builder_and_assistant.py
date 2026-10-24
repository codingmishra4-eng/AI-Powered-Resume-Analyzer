"""
Unit Tests for Resume Builder & AI Assistant Modules
----------------------------------------------------
Tests PDF and DOCX generation, extractability verification,
report compilation, bullet point rewriting, and score Q&A.
"""

import io
import pytest
from analyzer.ai_assistant import ResumeAssistant
from analyzer.resume_builder import (
    generate_analysis_report,
    generate_docx_resume,
    generate_pdf_resume,
    verify_generated_resume_extractability,
)


@pytest.fixture
def mock_structured_resume():
    return {
        "file_name": "candidate.pdf",
        "candidate_name": "Alex Rivera",
        "contact": {
            "email": "alex.rivera@example.com",
            "phone": "(555) 234-5678",
            "location": "San Francisco, CA",
            "linkedin": "linkedin.com/in/alex-dev",
            "github": "github.com/alex-code"
        },
        "summary": "Senior Software Engineer with 5+ years of experience in Python, FastAPI, and Docker.",
        "skills_raw": "Python, FastAPI, Docker, PostgreSQL, Redis, Git",
        "experience": [
            {
                "title": "Senior Backend Developer",
                "company": "Finova Labs",
                "dates": "2022 - Present",
                "bullets": [
                    "Architected high-throughput microservices using Python and FastAPI, serving 2.5M daily requests.",
                    "Optimized PostgreSQL queries, reducing latency by 35%."
                ]
            }
        ],
        "education": [
            {
                "degree": "BS in Computer Science",
                "institution": "Western Tech University",
                "dates": "2021",
                "details": "GPA 3.8/4.0"
            }
        ],
        "projects": [
            {
                "title": "ResumeIQ Platform",
                "bullets": ["Built intelligent resume parser using PyMuPDF and Streamlit."]
            }
        ],
        "certifications": [{"name": "AWS Certified Solutions Architect", "date": "2023"}]
    }


def test_generate_docx_resume(mock_structured_resume):
    """Verify DOCX generation returns a valid in-memory document."""
    stream = generate_docx_resume(mock_structured_resume)
    assert isinstance(stream, io.BytesIO)
    bytes_val = stream.getvalue()
    assert len(bytes_val) > 1000
    # Check Word magic header PK (ZIP format)
    assert bytes_val[:2] == b"PK"


def test_generate_pdf_resume(mock_structured_resume):
    """Verify PDF generation returns a valid in-memory vector PDF."""
    stream = generate_pdf_resume(mock_structured_resume)
    assert isinstance(stream, io.BytesIO)
    bytes_val = stream.getvalue()
    assert len(bytes_val) > 1000
    # Check PDF magic header %PDF
    assert bytes_val[:4] == b"%PDF"


def test_verify_generated_resume_extractability(mock_structured_resume):
    """Verify self-test re-parser validates that generated PDF has 100% extractable text."""
    stream = generate_pdf_resume(mock_structured_resume)
    is_ok, msg = verify_generated_resume_extractability(stream.getvalue(), "test.pdf")
    assert is_ok is True
    assert "Verified!" in msg


def test_generate_analysis_report():
    """Verify comprehensive markdown analysis report generation."""
    qa = {"quality_score": 85.0, "rating": "Strong Resume", "summary": "Great impact.", "findings": []}
    aa = {"ats_score": 90.0, "score_category": "High ATS Compatibility", "summary": "Clean text.", "prioritized_fixes": ["Use standard fonts."]}
    jm = {"has_job_description": True, "job_match_score": 80.0, "fit_level": "Strong Match", "required_skills": {"matched": ["Python"], "missing": [], "total": 1}}

    report = generate_analysis_report("Alex_Resume.pdf", "Senior Engineer", qa, aa, jm)
    assert "# ResumeIQ" in report
    assert "85.0%" in report
    assert "90.0%" in report
    assert "80.0%" in report


def test_resume_assistant_rewrite_summary():
    """Verify local AI assistant rewrites summary using active professional tone."""
    assistant = ResumeAssistant(provider="local")
    res = assistant.rewrite_summary(
        current_summary="I am a python dev.",
        candidate_name="Alex Rivera",
        top_skills=["Python", "FastAPI", "Docker"],
        target_role="Senior Backend Engineer"
    )
    assert "improved" in res
    assert "Python" in res["improved"]
    assert "Senior Backend Engineer" in res["improved"]
    assert "I am" not in res["improved"]


def test_resume_assistant_improve_bullet():
    """Verify bullet enhancer replaces passive words with active verbs and impact formula."""
    assistant = ResumeAssistant(provider="local")
    imp = assistant.improve_bullet_point("responsible for building backend APIs and fixed bugs.")
    assert "improved" in imp
    assert not imp["improved"].lower().startswith("responsible for")
    assert any(verb in imp["improved"] for verb in ["Engineered", "Architected", "Spearheaded", "Developed"])


def test_resume_assistant_qa():
    """Verify score explainer Q&A returns insightful context-aware answers."""
    assistant = ResumeAssistant(provider="local")
    answer = assistant.answer_analysis_question(
        question="How is my ATS compatibility evaluated?",
        quality_score=85.0,
        ats_score=90.0,
        job_match_score=78.0,
        top_missing_skills=["Kubernetes"]
    )
    assert "ATS Compatibility Score" in answer
    assert "90.0%" in answer
