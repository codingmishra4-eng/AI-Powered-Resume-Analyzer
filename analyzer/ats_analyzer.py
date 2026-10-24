"""
ATS Compatibility Analyzer Module
---------------------------------
Evaluates how reliably Applicant Tracking Systems (ATS) can parse,
segment, and index the resume document. Checks text layers, standard headings,
contact information extraction, formatting risks, and complex layout artifacts.
"""

import re
from typing import Dict, List, Tuple
from config import ATS_COMPATIBILITY_WEIGHTS


# Standard ATS-friendly section heading variations
STANDARD_HEADINGS = {
    "Experience": [
        "work experience", "professional experience", "experience",
        "employment history", "work history", "career history"
    ],
    "Education": [
        "education", "academic background", "academic qualifications",
        "degrees", "educational background"
    ],
    "Skills": [
        "skills", "technical skills", "core competencies",
        "skills & abilities", "areas of expertise", "technologies"
    ],
    "Summary": [
        "summary", "professional summary", "executive summary",
        "profile", "about me", "career summary"
    ],
    "Projects": [
        "projects", "key projects", "personal projects",
        "academic projects", "technical projects"
    ],
    "Certifications": [
        "certifications", "licenses & certifications", "certificates",
        "courses & certificates"
    ]
}

# Problematic characters for older ATS parsers
PROBLEMATIC_SYMBOLS = ["■", "✦", "❖", "✓", "✔", "★", "►", "▼", "§", "♠", "♣", "♥", "♦"]


def analyze_ats_compatibility(
    raw_text: str,
    parsed_sections: Dict[str, str],
    contact_info: Dict[str, any],
    page_count: int = 1,
    file_name: str = "resume.pdf"
) -> Dict[str, any]:
    """
    Computes a comprehensive ATS Parsing Compatibility Score (0-100)
    and detailed diagnostic breakdown of parsing risks and formatting issues.

    Parameters:
        raw_text (str): Full text extracted from document.
        parsed_sections (Dict): Output from parse_resume_sections().
        contact_info (Dict): Output from extract_contact_info().
        page_count (int): Total number of document pages.
        file_name (str): Original uploaded file name.

    Returns:
        Dict containing score, rating, sub-scores, passed checks, warnings, and risks.
    """
    passed_checks: List[Dict[str, str]] = []
    warning_checks: List[Dict[str, str]] = []
    risk_checks: List[Dict[str, str]] = []
    prioritized_fixes: List[str] = []

    words = raw_text.split()
    total_words = len(words)
    total_chars = len(raw_text)

    # -------------------------------------------------------------------------
    # 1. Text Extraction Reliability (25% weight)
    # -------------------------------------------------------------------------
    text_extraction_score = 100.0

    if total_chars < 50 or (page_count > 0 and total_chars / page_count < 40):
        text_extraction_score = 10.0
        risk_checks.append({
            "category": "Extraction Reliability",
            "title": "Severe: Document Appears Scanned or Lacks Text Layer",
            "description": "ATS parsers require embedded digital text glyphs. Scanned images produce zero extractable text.",
            "recommendation": "Convert the document using Optical Character Recognition (OCR) or export directly from Word/Google Docs."
        })
        prioritized_fixes.append("Re-save document with an embedded digital text layer.")
    else:
        passed_checks.append({
            "category": "Extraction Reliability",
            "title": "Clean Digital Text Layer Detected",
            "description": f"Successfully extracted {total_chars:,} characters across {page_count} page(s)."
        })

    # Check for excessive replacement or unprintable characters (encoding corruptions)
    unknown_chars = raw_text.count("\ufffd") + raw_text.count("")
    if unknown_chars > 3:
        text_extraction_score = max(20.0, text_extraction_score - 25.0)
        warning_checks.append({
            "category": "Extraction Reliability",
            "title": "Font Encoding Artifacts Detected",
            "description": f"Found {unknown_chars} corrupt or replacement characters, indicating custom fonts with missing CMaps.",
            "recommendation": "Use universal system fonts like Arial, Calibri, Helvetica, or Times New Roman."
        })
        prioritized_fixes.append("Replace decorative fonts with standard fonts like Calibri or Arial.")

    # -------------------------------------------------------------------------
    # 2. Standard Section Headings (25% weight)
    # -------------------------------------------------------------------------
    heading_score = 0.0
    detected_count = 0
    total_core = 4  # Experience, Education, Skills, Summary

    core_sections = ["Experience", "Education", "Skills", "Summary"]
    for sec in core_sections:
        if parsed_sections.get(sec, "Not Detected") != "Not Detected":
            detected_count += 1
            passed_checks.append({
                "category": "Section Headings",
                "title": f"Standard '{sec}' Heading Recognized",
                "description": f"ATS parser successfully mapped and segmented your {sec} section."
            })
        else:
            if sec in ["Experience", "Skills"]:
                risk_checks.append({
                    "category": "Section Headings",
                    "title": f"Missing Core Section: {sec}",
                    "description": f"The parser could not locate an obvious standard '{sec}' heading. ATS algorithms may miss your work history or qualifications.",
                    "recommendation": f"Add an explicit, capitalized heading such as 'WORK EXPERIENCE' or 'TECHNICAL SKILLS'."
                })
                prioritized_fixes.append(f"Add a distinct, conventional heading for '{sec}'.")
            else:
                warning_checks.append({
                    "category": "Section Headings",
                    "title": f"Optional Section Not Detected: {sec}",
                    "description": f"No obvious '{sec}' heading was found. While optional, it helps structure candidate summaries.",
                    "recommendation": f"Consider adding a '{sec}' heading to clarify your career profile."
                })

    heading_score = (detected_count / total_core) * 100.0

    # -------------------------------------------------------------------------
    # 3. Contact Information Completeness (20% weight)
    # -------------------------------------------------------------------------
    contact_score = 0.0
    contact_points = 0
    max_contact_points = 4

    # Email
    if contact_info.get("email"):
        contact_points += 1
        passed_checks.append({
            "category": "Contact Details",
            "title": "Email Address Extracted",
            "description": f"Detected: {contact_info['email']}"
        })
    else:
        risk_checks.append({
            "category": "Contact Details",
            "title": "Missing Email Address",
            "description": "ATS systems require a valid email to index candidate profiles and send recruiter updates.",
            "recommendation": "Include a standard, professional email address in the resume header."
        })
        prioritized_fixes.append("Place your email address clearly at the top of the resume.")

    # Phone
    if contact_info.get("phone"):
        contact_points += 1
        passed_checks.append({
            "category": "Contact Details",
            "title": "Phone Number Extracted",
            "description": f"Detected: {contact_info['phone']}"
        })
    else:
        warning_checks.append({
            "category": "Contact Details",
            "title": "Phone Number Not Detected",
            "description": "A contact phone number was not clearly identifiable in the top header.",
            "recommendation": "Add a phone number with country/area code in the header."
        })

    # Links (LinkedIn / GitHub)
    if contact_info.get("linkedin") or contact_info.get("github"):
        contact_points += 1
        passed_checks.append({
            "category": "Contact Details",
            "title": "Professional Profiles Extracted",
            "description": f"Found LinkedIn/GitHub profile link."
        })
    else:
        warning_checks.append({
            "category": "Contact Details",
            "title": "No LinkedIn or Portfolio URL Found",
            "description": "Tech recruiters heavily favor resumes with direct links to verified professional profiles.",
            "recommendation": "Add clickable LinkedIn and GitHub profile links to your header."
        })

    # Location
    if contact_info.get("location"):
        contact_points += 1
        passed_checks.append({
            "category": "Contact Details",
            "title": "Location Extracted",
            "description": f"Detected: {contact_info['location']}"
        })
    else:
        contact_points += 0.5  # Partial credit if absent since location is often optional for remote roles
        warning_checks.append({
            "category": "Contact Details",
            "title": "Geographic Location Not Detected",
            "description": "City and State or Country helps ATS filter candidates for location-specific or timezone requirements.",
            "recommendation": "Include City, State (e.g. 'San Francisco, CA' or 'London, UK') in your header."
        })

    contact_score = (contact_points / max_contact_points) * 100.0

    # -------------------------------------------------------------------------
    # 4. Layout & Formatting Risk Assessment (20% weight)
    # -------------------------------------------------------------------------
    layout_score = 100.0

    # Unusual symbols / graphical icon bullets
    found_symbols = [sym for sym in PROBLEMATIC_SYMBOLS if sym in raw_text]
    if found_symbols:
        layout_score -= 15.0
        warning_checks.append({
            "category": "Layout & Formatting",
            "title": "Non-Standard Graphic Bullet Characters",
            "description": f"Found decorative glyphs ({', '.join(found_symbols[:4])}). Some older ATS parsers render these as question marks or corrupt text.",
            "recommendation": "Use standard round bullet points (•) or hyphens (-)."
        })
        prioritized_fixes.append("Replace decorative graphic symbols with standard bullets.")

    # Complex table artifacts (many pipe dividers in text lines)
    table_lines = [line for line in raw_text.split("\n") if line.count("|") >= 3]
    if len(table_lines) >= 3:
        layout_score -= 15.0
        warning_checks.append({
            "category": "Layout & Formatting",
            "title": "Multi-Column Table Layout Detected",
            "description": "Multi-column tables can cause ATS parsers to read horizontally across columns rather than vertically down sections.",
            "recommendation": "Use clean, single-column linear layouts without nested tables or multi-column grids."
        })
        prioritized_fixes.append("Simplify multi-column tables into a single-column layout.")

    # Document Length
    if total_words < 180:
        layout_score -= 25.0
        warning_checks.append({
            "category": "Layout & Formatting",
            "title": "Resume Length is Unusually Brief",
            "description": f"Document contains only {total_words} words. Most ATS systems look for 400-800 words of substantiated experience.",
            "recommendation": "Elaborate on project contributions, responsibilities, and tooling."
        })
    elif total_words > 1200:
        layout_score -= 10.0
        warning_checks.append({
            "category": "Layout & Formatting",
            "title": "Resume Word Count is High",
            "description": f"Document contains {total_words} words. Resumes over 1,000 words risk poor recruiter scanability.",
            "recommendation": "Condense older roles and keep document within 1-2 focused pages."
        })
    else:
        passed_checks.append({
            "category": "Layout & Formatting",
            "title": "Optimal Word Count Range",
            "description": f"Document has {total_words} words, which fits cleanly into a 1-2 page ATS profile."
        })

    layout_score = max(10.0, layout_score)

    # -------------------------------------------------------------------------
    # 5. File Format & Standard Compatibility (10% weight)
    # -------------------------------------------------------------------------
    file_score = 100.0
    ext = file_name.lower().split(".")[-1] if "." in file_name else ""
    if ext in ["pdf", "docx"]:
        passed_checks.append({
            "category": "File Format",
            "title": f"ATS-Standard File Extension (.{ext.upper()})",
            "description": f"Standard .{ext} format accepted by 99% of Applicant Tracking Systems."
        })
    else:
        file_score = 70.0
        warning_checks.append({
            "category": "File Format",
            "title": f"Non-Standard Upload Format (.{ext})",
            "description": "While plain text (.txt) is parseable, most corporate ATS portals expect PDF or DOCX.",
            "recommendation": "Submit resumes in standard PDF or DOCX format."
        })

    # -------------------------------------------------------------------------
    # Overall ATS Score Computation
    # -------------------------------------------------------------------------
    w = ATS_COMPATIBILITY_WEIGHTS
    overall_ats = (
        (text_extraction_score * w["text_extraction_reliability"]) +
        (heading_score * w["standard_section_headings"]) +
        (contact_score * w["contact_info_completeness"]) +
        (layout_score * w["layout_formatting_risk"]) +
        (file_score * w["file_format_and_length"])
    )
    overall_ats = round(max(0.0, min(100.0, overall_ats)), 1)

    if overall_ats >= 85:
        category = "High ATS Compatibility"
        summary = "Excellent parsing readiness. Document uses standard headings, clean text streams, and accessible contact fields."
    elif overall_ats >= 65:
        category = "Moderate ATS Compatibility"
        summary = "Good overall structure, but minor formatting or heading risks may cause partial data misreading in older ATS portals."
    else:
        category = "High Parsing Risk"
        summary = "Significant ATS parsing risks detected. Important sections or contact details may fail to import into recruiter databases."

    return {
        "ats_score": overall_ats,
        "score_category": category,
        "summary": summary,
        "breakdown": {
            "text_extraction": round(text_extraction_score, 1),
            "section_headings": round(heading_score, 1),
            "contact_info": round(contact_score, 1),
            "layout_formatting": round(layout_score, 1),
            "file_format": round(file_score, 1)
        },
        "weights": {k: int(v * 100) for k, v in w.items()},
        "passed_checks": passed_checks,
        "warning_checks": warning_checks,
        "risk_checks": risk_checks,
        "prioritized_fixes": prioritized_fixes[:5],
        "disclaimer": (
            "Disclaimer: ATS Compatibility measures technical parseability and structural adherence "
            "to common applicant tracking guidelines. It is not an endorsement or score from any "
            "proprietary vendor (such as Workday, Taleo, or Greenhouse)."
        )
    }
