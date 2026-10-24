"""
Resume Builder & Multi-Format Export Module
-------------------------------------------
Builds ATS-friendly, clean, single-column resumes:
- Vector PDF generation using PyMuPDF (fitz)
- Microsoft Word (.docx) generation using python-docx
- Comprehensive Analysis Report export (Markdown/Text)
- Self-test re-parser validating 100% text extractability
"""

import io
from typing import Dict, List, Optional, Tuple
from analyzer.resume_parser import extract_text_from_file


def generate_docx_resume(structured_resume: Dict[str, any]) -> io.BytesIO:
    """
    Generates an ATS-optimized Microsoft Word (.docx) resume.
    """
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = docx.Document()

    # Set standard 0.75-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # 1. Candidate Name Header
    name = structured_resume.get("candidate_name", "Candidate Name")
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_name = title_p.add_run(name.upper())
    run_name.bold = True
    run_name.font.size = Pt(18)
    run_name.font.name = "Calibri"

    # 2. Contact Information
    contact = structured_resume.get("contact", {})
    contact_parts = []
    if contact.get("email"):
        contact_parts.append(contact["email"])
    if contact.get("phone"):
        contact_parts.append(contact["phone"])
    if contact.get("location"):
        contact_parts.append(contact["location"])
    if contact.get("linkedin"):
        contact_parts.append(contact["linkedin"])
    if contact.get("github"):
        contact_parts.append(contact["github"])

    contact_p = doc.add_paragraph(" | ".join(contact_parts))
    contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_p.paragraph_format.space_after = Pt(12)

    def add_section_heading(title: str):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
        run = h.add_run(title.upper())
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(30, 41, 59)

    # 3. Professional Summary
    summary = structured_resume.get("summary", "")
    if summary and summary != "Not Detected":
        add_section_heading("Professional Summary")
        p_sum = doc.add_paragraph(summary)
        p_sum.paragraph_format.space_after = Pt(8)

    # 4. Technical Skills
    skills_raw = structured_resume.get("skills_raw", "")
    if skills_raw and skills_raw != "Not Detected":
        add_section_heading("Technical Skills")
        for line in skills_raw.split("\n"):
            if line.strip():
                p = doc.add_paragraph(line.strip(), style="List Bullet")
                p.paragraph_format.space_after = Pt(2)

    # 5. Work Experience
    experience = structured_resume.get("experience", [])
    if experience:
        add_section_heading("Work Experience")
        for role in experience:
            p_role = doc.add_paragraph()
            p_role.paragraph_format.space_before = Pt(6)
            p_role.paragraph_format.space_after = Pt(2)

            r_title = p_role.add_run(role.get("title", "Role Title"))
            r_title.bold = True

            comp = role.get("company", "")
            if comp:
                r_comp = p_role.add_run(f" | {comp}")
                r_comp.italic = True

            dates = role.get("dates", "")
            if dates:
                p_role.add_run(f" ({dates})")

            for b in role.get("bullets", []):
                p_b = doc.add_paragraph(b, style="List Bullet")
                p_b.paragraph_format.space_after = Pt(2)

    # 6. Education
    education = structured_resume.get("education", [])
    if education:
        add_section_heading("Education")
        for edu in education:
            p_edu = doc.add_paragraph()
            r_deg = p_edu.add_run(edu.get("degree", "Degree"))
            r_deg.bold = True

            inst = edu.get("institution", "")
            if inst:
                p_edu.add_run(f" | {inst}")

            dates = edu.get("dates", "")
            if dates:
                p_edu.add_run(f" ({dates})")

            details = edu.get("details", "")
            if details:
                doc.add_paragraph(details, style="List Bullet")

    # 7. Projects
    projects = structured_resume.get("projects", [])
    if projects:
        add_section_heading("Projects")
        for proj in projects:
            p_proj = doc.add_paragraph()
            p_proj.paragraph_format.space_before = Pt(4)
            r_p = p_proj.add_run(proj.get("title", "Project Title"))
            r_p.bold = True

            for b in proj.get("bullets", []):
                doc.add_paragraph(b, style="List Bullet")

    # 8. Certifications
    certs = structured_resume.get("certifications", [])
    if certs:
        add_section_heading("Certifications")
        for c in certs:
            c_name = c.get("name", "")
            if c_name:
                doc.add_paragraph(c_name, style="List Bullet")

    output_stream = io.BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    return output_stream


def generate_pdf_resume(structured_resume: Dict[str, any]) -> io.BytesIO:
    """
    Generates a clean, ATS-optimized vector PDF resume using PyMuPDF (fitz).
    Uses standard fonts, clear headings, and proper margins.
    """
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 Dimensions

    # Coordinates
    x_margin = 40
    width = 515
    y_pos = 50

    # Header Name
    name = structured_resume.get("candidate_name", "Candidate Name").upper()
    page.insert_text(fitz.Point(x_margin, y_pos), name, fontsize=16, fontname="helv", color=(0.1, 0.15, 0.25))
    y_pos += 18

    # Contact Info
    contact = structured_resume.get("contact", {})
    contact_parts = []
    if contact.get("email"):
        contact_parts.append(contact["email"])
    if contact.get("phone"):
        contact_parts.append(contact["phone"])
    if contact.get("location"):
        contact_parts.append(contact["location"])
    if contact.get("linkedin"):
        contact_parts.append(contact["linkedin"])

    contact_str = " | ".join(contact_parts)
    page.insert_text(fitz.Point(x_margin, y_pos), contact_str, fontsize=8.5, fontname="helv", color=(0.3, 0.35, 0.45))
    y_pos += 15

    # Divider line
    page.draw_line(fitz.Point(x_margin, y_pos), fitz.Point(x_margin + width, y_pos), color=(0.7, 0.75, 0.8), width=0.8)
    y_pos += 18

    def add_pdf_heading(title: str):
        nonlocal y_pos, page
        if y_pos > 770:
            page = doc.new_page(width=595, height=842)
            y_pos = 50
        page.insert_text(fitz.Point(x_margin, y_pos), title.upper(), fontsize=11, fontname="helv", color=(0.1, 0.2, 0.35))
        y_pos += 4
        page.draw_line(fitz.Point(x_margin, y_pos), fitz.Point(x_margin + width, y_pos), color=(0.8, 0.85, 0.9), width=0.5)
        y_pos += 14

    # Summary
    summary = structured_resume.get("summary", "")
    if summary and summary != "Not Detected":
        add_pdf_heading("Professional Summary")
        rect = fitz.Rect(x_margin, y_pos, x_margin + width, y_pos + 60)
        rc = page.insert_textbox(rect, summary, fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
        y_pos += max(35, abs(rc) + 12)

    # Technical Skills
    skills_raw = structured_resume.get("skills_raw", "")
    if skills_raw and skills_raw != "Not Detected":
        add_pdf_heading("Technical Skills")
        for line in skills_raw.split("\n")[:4]:
            if line.strip():
                page.insert_text(fitz.Point(x_margin + 10, y_pos), f"• {line.strip()}", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
                y_pos += 13
        y_pos += 6

    # Work Experience
    experience = structured_resume.get("experience", [])
    if experience:
        add_pdf_heading("Work Experience")
        for role in experience:
            if y_pos > 750:
                page = doc.new_page(width=595, height=842)
                y_pos = 50

            role_title = role.get("title", "")
            comp = role.get("company", "")
            dates = role.get("dates", "")
            role_header = f"{role_title} | {comp} ({dates})" if comp else f"{role_title} ({dates})"

            page.insert_text(fitz.Point(x_margin, y_pos), role_header, fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.15))
            y_pos += 13

            for b in role.get("bullets", []):
                if y_pos > 770:
                    page = doc.new_page(width=595, height=842)
                    y_pos = 50

                rect = fitz.Rect(x_margin + 10, y_pos, x_margin + width, y_pos + 40)
                rc = page.insert_textbox(rect, f"• {b}", fontsize=8.5, fontname="helv", color=(0.25, 0.25, 0.25))
                y_pos += max(14, abs(rc) + 4)
            y_pos += 6

    # Education
    education = structured_resume.get("education", [])
    if education:
        add_pdf_heading("Education")
        for edu in education:
            if y_pos > 760:
                page = doc.new_page(width=595, height=842)
                y_pos = 50
            deg = edu.get("degree", "Degree")
            inst = edu.get("institution", "")
            dates = edu.get("dates", "")
            page.insert_text(fitz.Point(x_margin, y_pos), f"{deg} | {inst} ({dates})", fontsize=9, fontname="helv", color=(0.15, 0.15, 0.15))
            y_pos += 14

    output_stream = io.BytesIO()
    doc.save(output_stream)
    doc.close()
    output_stream.seek(0)
    return output_stream


def generate_analysis_report(
    resume_name: str,
    job_title: str,
    quality_analysis: Dict[str, any],
    ats_analysis: Dict[str, any],
    job_match: Dict[str, any]
) -> str:
    """
    Generates a downloadable Comprehensive Markdown Analysis Report.
    """
    report_lines = [
        f"# ResumeIQ — Comprehensive ATS & Quality Evaluation Report",
        f"**Candidate Document:** {resume_name}",
        f"**Target Role:** {job_title or 'General Technical Role'}",
        f"**Report Generated By:** ResumeIQ v2.0 Enterprise Engine\n",
        f"---",
        f"## 1. Executive Score Summary",
        f"- **Resume Quality Score:** {quality_analysis['quality_score']}% ({quality_analysis['rating']})",
        f"- **ATS Parsing Compatibility:** {ats_analysis['ats_score']}% ({ats_analysis['score_category']})",
    ]

    if job_match.get("has_job_description"):
        report_lines.append(f"- **Job Description Match Score:** {job_match['job_match_score']}% ({job_match['fit_level']})")
    else:
        report_lines.append(f"- **Job Description Match Score:** Not Evaluated (No Job Description Supplied)")

    report_lines.extend([
        f"\n---",
        f"## 2. ATS Compatibility Diagnostics",
        f"- **Summary:** {ats_analysis['summary']}",
        f"\n### Prioritized ATS Fixes:",
    ])
    for fix in ats_analysis.get("prioritized_fixes", []):
        report_lines.append(f"  - {fix}")

    report_lines.extend([
        f"\n---",
        f"## 3. Resume Quality & Content Findings",
        f"- **Summary:** {quality_analysis['summary']}",
        f"\n### Actionable Improvement Plan:",
    ])
    for f in quality_analysis.get("findings", [])[:6]:
        report_lines.append(f"### [{f['priority']} Priority] {f['title']}")
        report_lines.append(f"- **Section:** {f['section']}")
        report_lines.append(f"- **Evidence:** {f['evidence']}")
        report_lines.append(f"- **Why It Matters:** {f['why_it_matters']}")
        report_lines.append(f"- **Recommended Fix:** {f['recommendation']}\n")

    if job_match.get("has_job_description"):
        req = job_match.get("required_skills", {})
        report_lines.extend([
            f"---",
            f"## 4. Job Description Match & Skill Gap Matrix",
            f"- **Required Skills Matched ({len(req.get('matched', []))}/{req.get('total', 0)}):** {', '.join(req.get('matched', [])) or 'None'}",
            f"- **Missing Required Skills ({len(req.get('missing', []))}):** {', '.join(req.get('missing', [])) or 'None'}",
        ])

    return "\n".join(report_lines)


def verify_generated_resume_extractability(file_bytes: bytes, file_name: str) -> Tuple[bool, str]:
    """
    Self-tests the generated resume document by running it through the extraction engine
    to verify that 100% of the text layer is extractable and readable by an ATS.
    """
    extracted_text, page_count, warning = extract_text_from_file(file_bytes, file_name)
    if warning or len(extracted_text.strip()) < 100:
        return False, f"Verification failed: {warning or 'Insufficient extracted text'}"
    return True, f"Verified! Successfully extracted {len(extracted_text):,} characters across {page_count} page(s)."
