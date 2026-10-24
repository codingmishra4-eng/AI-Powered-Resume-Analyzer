"""
Unit Tests for Resume Parser Module
-----------------------------------
Tests extraction of text from PDF, DOCX, and TXT files,
as well as contact information and section parsing.
"""

import io
from pathlib import Path
import pytest
from analyzer.resume_parser import (
    extract_contact_info,
    extract_text_from_docx,
    extract_text_from_file,
    extract_text_from_pdf,
    extract_text_from_txt,
    parse_resume_sections,
)
from config import DATA_DIR


def test_extract_text_from_txt():
    """Test extracting text from sample text file."""
    txt_path = DATA_DIR / "sample_resume.txt"
    assert txt_path.exists(), "sample_resume.txt should exist"

    text, pages, warning = extract_text_from_txt(txt_path)
    assert len(text) > 100
    assert pages == 1
    assert warning == ""
    assert "ALEX RIVERA" in text


def test_extract_text_from_pdf():
    """Test extracting text from generated sample PDF file."""
    pdf_path = DATA_DIR / "sample_resume.pdf"
    assert pdf_path.exists(), "sample_resume.pdf should exist"

    text, pages, warning = extract_text_from_pdf(pdf_path)
    assert len(text) > 100
    assert pages >= 1
    assert warning == ""
    assert "Python" in text


def test_extract_text_from_docx():
    """Test extracting text from generated sample DOCX file."""
    docx_path = DATA_DIR / "sample_resume.docx"
    assert docx_path.exists(), "sample_resume.docx should exist"

    text, pages, warning = extract_text_from_docx(docx_path)
    assert len(text) > 100
    assert pages >= 1
    assert warning == ""
    assert "FastAPI" in text


def test_extract_text_from_unsupported():
    """Test unsupported file extensions."""
    text, pages, warning = extract_text_from_file(b"test", "resume.png")
    assert text == ""
    assert "Unsupported file type" in warning


def test_extract_contact_info():
    """Verify regex extraction of email, phone, linkedin, and github."""
    sample_text = """
    Jane Doe
    Email: jane.doe@example.com | Phone: (555) 123-4567
    LinkedIn: linkedin.com/in/jane-doe-dev
    GitHub: github.com/janedoe-code
    Portfolio: https://janedoe.dev
    """
    contacts = extract_contact_info(sample_text)
    assert contacts["email"] == "jane.doe@example.com"
    assert "(555) 123-4567" in contacts["phone"]
    assert "linkedin.com/in/jane-doe-dev" in contacts["linkedin"]
    assert "github.com/janedoe-code" in contacts["github"]
    assert "janedoe.dev" in contacts["portfolio"]


def test_extract_contact_info_missing():
    """Verify that unidentifiable contact details return None."""
    sample_text = "Experienced developer with no contact information listed."
    contacts = extract_contact_info(sample_text)
    assert contacts["email"] is None
    assert contacts["phone"] is None
    assert contacts["linkedin"] is None
    assert contacts["github"] is None


def test_parse_resume_sections():
    """Verify splitting of standard resume sections."""
    sample_resume = """
    JOHN DOE
    
    PROFESSIONAL SUMMARY
    Senior engineer with 5 years experience.

    TECHNICAL SKILLS
    Python, Docker, SQL, AWS

    WORK EXPERIENCE
    Software Engineer at TechCorp (2020-Present)
    Built backend microservices using FastAPI.

    EDUCATION
    BS in Computer Science, Tech University (2020)

    PROJECTS
    Built an open-source resume analyzer.

    CERTIFICATIONS
    AWS Certified Cloud Practitioner
    """
    sections = parse_resume_sections(sample_resume)
    assert sections["Summary"] != "Not Detected"
    assert "Senior engineer" in sections["Summary"]

    assert sections["Skills"] != "Not Detected"
    assert "Python" in sections["Skills"]

    assert sections["Experience"] != "Not Detected"
    assert "TechCorp" in sections["Experience"]

    assert sections["Education"] != "Not Detected"
    assert "Tech University" in sections["Education"]

    assert sections["Projects"] != "Not Detected"
    assert "AWS Certified" in sections["Certifications"]
