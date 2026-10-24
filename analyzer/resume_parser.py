"""
Resume Parser Module
--------------------
Extracts text and structured sections from PDF, DOCX, and TXT resume files.
Provides explainable, transparent parsing rules without hidden hallucinations.
"""

import io
import re
from typing import Dict, List, Optional, Tuple, Union
from utils.validators import sanitize_text, detect_scanned_document


def extract_text_from_pdf(file_source: Union[str, bytes, io.BytesIO]) -> Tuple[str, int, str]:
    """
    Extract text content and page count from a PDF document using PyMuPDF (fitz).

    Parameters:
        file_source: Path string, bytes, or BytesIO buffer containing the PDF.

    Returns:
        Tuple[str, int, str]: (extracted_text, page_count, status_message)
    """
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
    except ImportError:
        return "", 0, "PyMuPDF is not installed. Please install requirements."

    try:
        # Open PDF from stream or file path
        if isinstance(file_source, bytes):
            doc = fitz.open(stream=file_source, filetype="pdf")
        elif isinstance(file_source, io.BytesIO):
            doc = fitz.open(stream=file_source.getvalue(), filetype="pdf")
        else:
            doc = fitz.open(file_source)

        # Check for encrypted or password-protected PDF
        if doc.is_encrypted:
            return "", 0, "This PDF is password-protected or encrypted. Please provide an unlocked document."

        page_count = len(doc)
        if page_count == 0:
            return "", 0, "The PDF document has 0 pages."

        text_pages: List[str] = []
        for page_idx in range(page_count):
            page = doc[page_idx]
            page_text = page.get_text("text")
            if page_text:
                text_pages.append(page_text)

        full_text = "\n".join(text_pages)
        sanitized = sanitize_text(full_text)

        # Detect if document appears to be a scanned image
        is_scanned, scan_warning = detect_scanned_document(sanitized, page_count)
        if is_scanned:
            return sanitized, page_count, scan_warning

        return sanitized, page_count, ""

    except Exception as exc:
        return "", 0, f"Error reading PDF file: {str(exc)}"


def extract_text_from_docx(file_source: Union[str, bytes, io.BytesIO]) -> Tuple[str, int, str]:
    """
    Extract text from a Microsoft Word (.docx) document using python-docx.

    Parameters:
        file_source: Path string, bytes, or BytesIO buffer containing the DOCX file.

    Returns:
        Tuple[str, int, str]: (extracted_text, page_count, status_message)
    """
    try:
        import docx
    except ImportError:
        return "", 0, "python-docx is not installed. Please install requirements."

    try:
        if isinstance(file_source, bytes):
            stream = io.BytesIO(file_source)
            doc = docx.Document(stream)
        elif isinstance(file_source, io.BytesIO):
            doc = docx.Document(file_source)
        else:
            doc = docx.Document(file_source)

        paragraphs_text = [p.text for p in doc.paragraphs if p.text.strip()]
        
        # Also extract text from any tables in the docx document
        table_text = []
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    table_text.append(" | ".join(row_cells))

        combined_text = "\n".join(paragraphs_text + table_text)
        sanitized = sanitize_text(combined_text)

        if not sanitized:
            return "", 1, "The Word document appears empty or contains only non-text media."

        # DOCX files do not have explicit page counts without rendering, assume at least 1
        return sanitized, 1, ""

    except Exception as exc:
        return "", 0, f"Error reading Word (.docx) document: {str(exc)}"


def extract_text_from_txt(file_source: Union[str, bytes, io.BytesIO]) -> Tuple[str, int, str]:
    """
    Extract text from a plain text (.txt) document.

    Parameters:
        file_source: Path string, bytes, or BytesIO buffer.

    Returns:
        Tuple[str, int, str]: (extracted_text, page_count, status_message)
    """
    try:
        raw_bytes: bytes
        if isinstance(file_source, bytes):
            raw_bytes = file_source
        elif isinstance(file_source, io.BytesIO):
            raw_bytes = file_source.getvalue()
        else:
            with open(file_source, "rb") as f:
                raw_bytes = f.read()

        # Try UTF-8 first, fallback to Latin-1
        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = raw_bytes.decode("latin-1")

        sanitized = sanitize_text(content)
        if not sanitized:
            return "", 1, "The text file is empty."

        return sanitized, 1, ""
    except Exception as exc:
        return "", 0, f"Error reading text document: {str(exc)}"


def extract_text_from_file(file_source: Union[str, bytes, io.BytesIO], file_name: str) -> Tuple[str, int, str]:
    """
    Master file extractor: identifies file extension and dispatches to appropriate extractor.

    Parameters:
        file_source: File path, bytes, or file-like buffer.
        file_name (str): Original filename for extension routing.

    Returns:
        Tuple[str, int, str]: (text, page_count, warning_or_error)
    """
    ext = file_name.lower().strip()
    if ext.endswith(".pdf"):
        return extract_text_from_pdf(file_source)
    elif ext.endswith(".docx"):
        return extract_text_from_docx(file_source)
    elif ext.endswith(".txt"):
        return extract_text_from_txt(file_source)
    else:
        return "", 0, f"Unsupported file type '{file_name}'. Please upload PDF, DOCX, or TXT."


def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
    """
    Extracts contact details (Email, Phone, LinkedIn, GitHub, Portfolio)
    using deterministic regular expressions.

    Returns a dictionary distinguishing identified fields from 'Not Detected'.
    """
    contact_data: Dict[str, Optional[str]] = {
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "portfolio": None
    }

    if not text:
        return contact_data

    # 1. Email pattern
    email_pattern = r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
    email_match = re.search(email_pattern, text)
    if email_match:
        contact_data["email"] = email_match.group(0).strip()

    # 2. Phone pattern: handles (123) 456-7890, +1 123 456 7890, 123-456-7890, 123.456.7890
    phone_pattern = r"(?:(?:\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})"
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        contact_data["phone"] = phone_match.group(0).strip()

    # 3. LinkedIn URL or handle
    linkedin_pattern = r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+"
    linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
    if linkedin_match:
        contact_data["linkedin"] = linkedin_match.group(0).strip()

    # 4. GitHub URL or handle
    github_pattern = r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_-]+"
    github_match = re.search(github_pattern, text, re.IGNORECASE)
    if github_match:
        contact_data["github"] = github_match.group(0).strip()

    # 5. General portfolio or personal website (excluding github, linkedin, and email domains)
    portfolio_pattern = r"(?:https?://[^\s]+|www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?|(?<!@)\b[a-zA-Z0-9-]+\.(?:dev|io|me|tech|site)\b(?:/[^\s]*)?)"
    email_domain = contact_data["email"].split("@")[-1].lower() if contact_data["email"] else ""

    for match in re.finditer(portfolio_pattern, text, re.IGNORECASE):
        url = match.group(0).strip().rstrip(".,;)")
        url_lower = url.lower()
        if (
            "linkedin.com" not in url_lower
            and "github.com" not in url_lower
            and (not email_domain or email_domain not in url_lower)
        ):
            contact_data["portfolio"] = url
            break

    return contact_data


def parse_resume_sections(text: str) -> Dict[str, str]:
    """
    Partitions resume text into standard resume sections:
    - Summary / Objective
    - Work Experience
    - Education
    - Skills
    - Projects
    - Certifications

    Returns a dictionary of section names mapped to their identified content.
    If a section cannot be identified, it is marked as 'Not Detected'.
    """
    sections = {
        "Summary": "Not Detected",
        "Experience": "Not Detected",
        "Education": "Not Detected",
        "Skills": "Not Detected",
        "Projects": "Not Detected",
        "Certifications": "Not Detected"
    }

    if not text:
        return sections

    # Common heading patterns for standard sections
    section_patterns = {
        "Summary": r"(?:^|\n)\s*(?:PROFESSIONAL SUMMARY|EXECUTIVE SUMMARY|SUMMARY|OBJECTIVE|PROFILE|ABOUT ME)\s*(?:\n|:)",
        "Experience": r"(?:^|\n)\s*(?:WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EXPERIENCE|EMPLOYMENT HISTORY|WORK HISTORY)\s*(?:\n|:)",
        "Education": r"(?:^|\n)\s*(?:EDUCATION|ACADEMIC BACKGROUND|ACADEMIC QUALIFICATIONS|DEGREES)\s*(?:\n|:)",
        "Skills": r"(?:^|\n)\s*(?:TECHNICAL SKILLS|CORE COMPETENCIES|SKILLS & ABILITIES|SKILLS|AREAS OF EXPERTISE)\s*(?:\n|:)",
        "Projects": r"(?:^|\n)\s*(?:KEY PROJECTS|PROJECTS|PERSONAL PROJECTS|ACADEMIC PROJECTS)\s*(?:\n|:)",
        "Certifications": r"(?:^|\n)\s*(?:CERTIFICATIONS|LICENSES & CERTIFICATIONS|COURSES & CERTIFICATES|CERTIFICATES)\s*(?:\n|:)"
    }

    # Find the starting index of each heading present in the text
    matches = []
    for section_name, pattern in section_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            matches.append((match.start(), match.end(), section_name))

    # Sort matches by appearance in the text
    matches.sort(key=lambda item: item[0])

    # Extract text slices between matched headings
    for i in range(len(matches)):
        _, start_pos, section_name = matches[i]
        end_pos = matches[i + 1][0] if i + 1 < len(matches) else len(text)
        content = text[start_pos:end_pos].strip()
        if content:
            sections[section_name] = content

    return sections
