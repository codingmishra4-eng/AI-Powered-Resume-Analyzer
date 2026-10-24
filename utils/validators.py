"""
Validation and Sanitization Utilities
-------------------------------------
Provides beginner-friendly, secure validation for resume uploads,
job description text, and document scanning detection.
"""

import os
from typing import Tuple
from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB


def validate_file_upload(file_name: str, file_size_bytes: int) -> Tuple[bool, str]:
    """
    Validate that an uploaded file has a permissible extension and conforms
    to the maximum allowable file size.

    Parameters:
        file_name (str): The original filename of the uploaded file.
        file_size_bytes (int): Size of the file in bytes.

    Returns:
        Tuple[bool, str]: (True, "") if valid, otherwise (False, "Error description").
    """
    if not file_name:
        return False, "No file was provided for upload."

    # Extract extension in lowercase
    _, ext = os.path.splitext(file_name.lower())

    if ext not in ALLOWED_EXTENSIONS:
        allowed_list = ", ".join(sorted(list(ALLOWED_EXTENSIONS)))
        return False, f"Unsupported file format '{ext}'. Allowed formats: {allowed_list}"

    if file_size_bytes <= 0:
        return False, "The uploaded file is empty (0 bytes). Please upload a valid document."

    if file_size_bytes > MAX_FILE_SIZE_BYTES:
        size_in_mb = file_size_bytes / (1024 * 1024)
        return (
            False,
            f"File size ({size_in_mb:.2f} MB) exceeds maximum limit of {MAX_FILE_SIZE_MB} MB."
        )

    return True, ""


def validate_job_description(text: str) -> Tuple[bool, str]:
    """
    Validate that the job description contains meaningful, non-empty text.

    Parameters:
        text (str): The raw job description input string.

    Returns:
        Tuple[bool, str]: (True, "") if valid, otherwise (False, "Error message").
    """
    if not text or not text.strip():
        return False, "Job description cannot be empty. Please paste the job requirements."

    cleaned = text.strip()
    words = cleaned.split()

    if len(words) < 10:
        return (
            False,
            f"Job description is too brief ({len(words)} words). "
            "Please provide at least 10 words for an accurate analysis."
        )

    return True, ""


def sanitize_text(text: str) -> str:
    """
    Sanitize extracted or input text by normalizing line breaks, removing null
    characters, and stripping leading/trailing whitespace.
    Does NOT modify the underlying meaning of the resume content.

    Parameters:
        text (str): Raw text string.

    Returns:
        str: Cleaned and normalized text string.
    """
    if not text:
        return ""

    # Remove null bytes which can disrupt C-based parsers or databases
    clean = text.replace("\x00", "")

    # Normalize Windows (CRLF) and Mac (CR) line endings to standard Unix LF
    clean = clean.replace("\r\n", "\n").replace("\r", "\n")

    # Replace consecutive spaces with a single space while keeping line breaks intact
    lines = [line.strip() for line in clean.split("\n")]
    
    # Reassemble without excessive empty lines (maximum of 2 consecutive newlines)
    result = []
    empty_count = 0
    for line in lines:
        if not line:
            empty_count += 1
            if empty_count <= 2:
                result.append(line)
        else:
            empty_count = 0
            result.append(line)

    return "\n".join(result).strip()


def detect_scanned_document(text: str, page_count: int = 1) -> Tuple[bool, str]:
    """
    Determine if a parsed PDF appears to be a scanned image-only document.
    Scanned PDFs lack a readable text layer, producing zero or very few characters.

    Parameters:
        text (str): The text extracted from the document.
        page_count (int): Total number of pages in the document.

    Returns:
        Tuple[bool, str]: (is_scanned, explanation_message)
    """
    stripped_text = text.strip()
    total_chars = len(stripped_text)
    effective_pages = max(1, page_count)
    chars_per_page = total_chars / effective_pages

    # If the document has pages but yields virtually no text, it's image-based
    if total_chars < 50 or chars_per_page < 30:
        msg = (
            "Notice: This PDF appears to be a scanned image or photo without an "
            "embedded text layer. PyMuPDF extracted minimal or no text. "
            "To analyze this resume, please convert it using an OCR tool or upload "
            "a text-based PDF/Word document."
        )
        return True, msg

    return False, ""
