"""
Unit Tests for Validators Module
--------------------------------
Tests file upload constraints, job description validation,
text sanitization, and scanned document detection.
"""

import pytest
from utils.validators import (
    validate_file_upload,
    validate_job_description,
    sanitize_text,
    detect_scanned_document,
)


def test_validate_file_upload_valid_formats():
    """Ensure valid extensions within size limit pass validation."""
    valid, msg = validate_file_upload("resume.pdf", 1024 * 500)
    assert valid is True
    assert msg == ""

    valid, msg = validate_file_upload("my_cv.DOCX", 1024 * 200)
    assert valid is True

    valid, msg = validate_file_upload("notes.txt", 1024)
    assert valid is True


def test_validate_file_upload_invalid_extension():
    """Ensure disallowed file extensions are rejected with clear explanation."""
    valid, msg = validate_file_upload("resume.exe", 1024)
    assert valid is False
    assert "Unsupported file format" in msg

    valid, msg = validate_file_upload("archive.zip", 2048)
    assert valid is False


def test_validate_file_upload_size_limits():
    """Ensure 0-byte and oversized files are rejected."""
    # 0 bytes
    valid, msg = validate_file_upload("resume.pdf", 0)
    assert valid is False
    assert "empty" in msg.lower()

    # Exceeding 5MB limit
    oversized = 6 * 1024 * 1024
    valid, msg = validate_file_upload("huge_file.pdf", oversized)
    assert valid is False
    assert "exceeds maximum limit" in msg.lower()


def test_validate_job_description_empty_and_short():
    """Ensure empty or excessively short job descriptions are rejected."""
    valid, msg = validate_job_description("")
    assert valid is False
    assert "empty" in msg.lower()

    valid, msg = validate_job_description("   ")
    assert valid is False

    valid, msg = validate_job_description("Python developer wanted.")
    assert valid is False
    assert "too brief" in msg.lower()


def test_validate_job_description_valid():
    """Ensure meaningful job descriptions pass validation."""
    jd = "We are seeking a senior Python developer with experience in Django, FastAPI, PostgreSQL, and Docker."
    valid, msg = validate_job_description(jd)
    assert valid is True
    assert msg == ""


def test_sanitize_text():
    """Verify sanitization cleans null bytes, normalizes line breaks and whitespace."""
    raw = "Hello\x00 World!\r\n\r\n\r\nThis is a   test.\r\n"
    clean = sanitize_text(raw)
    assert "\x00" not in clean
    assert "\r" not in clean
    assert "Hello World!" in clean


def test_detect_scanned_document():
    """Ensure scanned image PDFs with little or no text trigger a warning."""
    # High page count, negligible text
    is_scanned, msg = detect_scanned_document("   ", page_count=2)
    assert is_scanned is True
    assert "scanned image" in msg.lower()

    # Normal text-heavy document
    normal_text = "Experienced software engineer specializing in Python and distributed systems. " * 20
    is_scanned, msg = detect_scanned_document(normal_text, page_count=1)
    assert is_scanned is False
    assert msg == ""
