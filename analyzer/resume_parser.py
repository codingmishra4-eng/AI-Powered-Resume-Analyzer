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


def extract_candidate_name(text: str) -> Optional[str]:
    """
    Extracts the likely candidate name from the top lines of a resume.
    Filters out headers like 'RESUME', 'CV', 'SUMMARY', or contact tokens.
    """
    if not text:
        return None

    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    ignore_keywords = {
        "resume", "curriculum", "vitae", "cv", "summary", "profile", "contact",
        "phone", "email", "address", "portfolio", "engineer", "developer", "experience"
    }

    # Inspect the first 6 non-empty lines
    for line in lines[:6]:
        # Clean line of special symbols
        clean_line = re.sub(r"[^a-zA-Z\s.-]", "", line).strip()
        words = clean_line.split()

        # Typical names are 2 to 4 words long
        if 2 <= len(words) <= 4:
            # Check that words are capitalized or uppercase
            is_valid_name = True
            for word in words:
                if not (word.isupper() or word.istitle()):
                    is_valid_name = False
                    break
                if word.lower() in ignore_keywords or len(word) < 2:
                    is_valid_name = False
                    break
            if is_valid_name:
                return " ".join(words)

    return None


def extract_location(text: str) -> Optional[str]:
    """
    Extracts candidate location (City, State / Country) using common geographic patterns.
    """
    if not text:
        return None

    # Common US City, State patterns: 'San Francisco, CA', 'Austin, TX'
    us_pattern = r"\b([A-Z][a-zA-Z\s]+),\s*([A-Z]{2})\b"
    match = re.search(us_pattern, text[:1000])
    if match:
        city = match.group(1).strip()
        state = match.group(2).strip()
        if len(city.split()) <= 3:
            return f"{city}, {state}"

    # General City, Country patterns
    intl_pattern = r"\b([A-Z][a-zA-Z\s]+),\s*(USA|United States|UK|United Kingdom|Canada|Germany|India|Australia|Singapore)\b"
    match_intl = re.search(intl_pattern, text[:1000], re.IGNORECASE)
    if match_intl:
        return f"{match_intl.group(1).strip()}, {match_intl.group(2).strip()}"

    return None


def parse_structured_experience(experience_text: str) -> List[Dict[str, any]]:
    """
    Parses unstructured work experience text into structured job role items:
    job title, company/organization, dates, and bullet points.
    """
    if not experience_text or experience_text == "Not Detected":
        return []

    roles: List[Dict[str, any]] = []
    lines = [line.strip() for line in experience_text.split("\n") if line.strip()]

    # Pattern detecting date ranges (e.g., 2021 - Present, March 2020 – 2022, 05/2019 - 10/2021)
    date_pattern = r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4}|\d{1,2}/\d{4})\s*(?:–|-|to)\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4}|\d{1,2}/\d{4}|Present|Current)"

    current_role: Optional[Dict[str, any]] = None

    for line in lines:
        date_match = re.search(date_pattern, line, re.IGNORECASE)
        # If line contains a date range or pipe divider with company
        if date_match or ("|" in line and ("developer" in line.lower() or "engineer" in line.lower() or "manager" in line.lower())):
            if current_role and (current_role.get("bullets") or current_role.get("title")):
                roles.append(current_role)

            parts = [p.strip() for p in line.split("|")]
            title = parts[0] if len(parts) > 0 else line
            company = parts[1] if len(parts) > 1 else ""
            dates = date_match.group(0) if date_match else (parts[2] if len(parts) > 2 else "")

            current_role = {
                "title": title,
                "company": company,
                "dates": dates,
                "bullets": []
            }
        else:
            # Bullet point or responsibility line
            clean_bullet = line.lstrip("•-*–+> ").strip()
            if clean_bullet and current_role:
                current_role["bullets"].append(clean_bullet)
            elif clean_bullet and not current_role:
                # First role fallback
                current_role = {
                    "title": "Professional Experience",
                    "company": "",
                    "dates": "",
                    "bullets": [clean_bullet]
                }

    if current_role:
        roles.append(current_role)

    return roles


def parse_structured_education(education_text: str) -> List[Dict[str, str]]:
    """
    Parses unstructured education text into structured degree items:
    degree, institution, graduation year/dates, and GPA/honors.
    """
    if not education_text or education_text == "Not Detected":
        return []

    items = []
    lines = [line.strip() for line in education_text.split("\n") if line.strip()]

    degree_pattern = r"\b(Bachelor(?:'s)?|Master(?:'s)?|B\.S\.|M\.S\.|B\.Tech|M\.Tech|Ph\.D\.|B\.A\.|Associate)\b"
    gpa_pattern = r"(?:GPA|Grade):\s*([0-9]\.[0-9]{1,2}(?:/[0-9]\.[0-9])?)"

    current_edu: Optional[Dict[str, str]] = None

    for line in lines:
        if re.search(degree_pattern, line, re.IGNORECASE) or ("university" in line.lower() or "college" in line.lower() or "institute" in line.lower()):
            if current_edu:
                items.append(current_edu)

            degree_match = re.search(degree_pattern, line, re.IGNORECASE)
            degree_str = line if degree_match else "Degree / Qualification"

            current_edu = {
                "degree": degree_str,
                "institution": "",
                "dates": "",
                "details": ""
            }

            year_match = re.search(r"\b(19\d{2}|20\d{2})\b", line)
            if year_match:
                current_edu["dates"] = year_match.group(0)
        else:
            if current_edu:
                if not current_edu["institution"] and ("university" in line.lower() or "college" in line.lower() or "institute" in line.lower()):
                    current_edu["institution"] = line
                else:
                    current_edu["details"] += (" " + line).strip()

    if current_edu:
        items.append(current_edu)

    return items


def parse_structured_projects(projects_text: str) -> List[Dict[str, any]]:
    """
    Parses unstructured project descriptions into structured project cards.
    """
    if not projects_text or projects_text == "Not Detected":
        return []

    projects = []
    lines = [line.strip() for line in projects_text.split("\n") if line.strip()]

    current_proj: Optional[Dict[str, any]] = None

    for line in lines:
        # If line starts with a title or bullet
        if line.startswith("-") or line.startswith("•") or line.startswith("*"):
            bullet = line.lstrip("•-* ").strip()
            if current_proj:
                current_proj["bullets"].append(bullet)
            else:
                current_proj = {"title": "Key Project", "bullets": [bullet], "tools": []}
        elif ":" in line and not line.lower().startswith("http"):
            if current_proj:
                projects.append(current_proj)
            title, desc = line.split(":", 1)
            current_proj = {
                "title": title.strip().lstrip("•-* "),
                "bullets": [desc.strip()] if desc.strip() else [],
                "tools": []
            }
        else:
            if current_proj:
                current_proj["bullets"].append(line)
            else:
                current_proj = {"title": line, "bullets": [], "tools": []}

    if current_proj:
        projects.append(current_proj)

    return projects


def parse_structured_certifications(cert_text: str) -> List[Dict[str, str]]:
    """
    Parses unstructured certifications text into structured certification entries.
    """
    if not cert_text or cert_text == "Not Detected":
        return []

    certs = []
    lines = [line.strip() for line in cert_text.split("\n") if line.strip()]

    for line in lines:
        clean = line.lstrip("•-* ").strip()
        year_match = re.search(r"\b(20\d{2}|19\d{2})\b", clean)
        date_str = year_match.group(0) if year_match else ""
        certs.append({
            "name": clean,
            "date": date_str
        })

    return certs


def parse_full_resume_structure(raw_text: str, file_name: str = "") -> Dict[str, any]:
    """
    Generates a complete, structured representation of the resume:
    name, contacts, sections, experience roles, education, projects, certifications,
    and metadata.
    """
    contact = extract_contact_info(raw_text)
    name = extract_candidate_name(raw_text)
    location = extract_location(raw_text)
    contact["location"] = location

    sections = parse_resume_sections(raw_text)

    experience_list = parse_structured_experience(sections.get("Experience", ""))
    education_list = parse_structured_education(sections.get("Education", ""))
    projects_list = parse_structured_projects(sections.get("Projects", ""))
    certs_list = parse_structured_certifications(sections.get("Certifications", ""))

    words = raw_text.split()

    return {
        "file_name": file_name,
        "candidate_name": name or "Candidate",
        "contact": contact,
        "summary": sections.get("Summary", ""),
        "sections": sections,
        "experience": experience_list,
        "education": education_list,
        "projects": projects_list,
        "certifications": certs_list,
        "skills_raw": sections.get("Skills", ""),
        "word_count": len(words),
        "character_count": len(raw_text)
    }
