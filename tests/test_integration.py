"""
End-to-End Integration Test
---------------------------
Simulates the full workflow:
1. Load PDF / DOCX sample files
2. Validate inputs
3. Extract text
4. Extract contact details and sections
5. Extract and compare skills
6. Compute TF-IDF cosine similarity & hybrid match
7. Generate recommendations
8. Save, retrieve, and delete from SQLite database
"""

from pathlib import Path
from utils.validators import validate_file_upload, validate_job_description
from analyzer.resume_parser import (
    extract_contact_info,
    extract_text_from_file,
    parse_resume_sections,
)
from analyzer.skill_extractor import SkillExtractor
from analyzer.similarity import compute_match_details
from analyzer.recommendations import generate_recommendations
from database.db import (
    delete_analysis,
    get_all_analyses,
    get_history_summary_stats,
    init_db,
    save_analysis,
)
from config import DATA_DIR


def test_full_analysis_workflow_pdf(tmp_path: Path):
    """End-to-end integration test from PDF upload to database persistence."""
    pdf_path = DATA_DIR / "sample_resume.pdf"
    jd_path = DATA_DIR / "sample_job_description.txt"

    assert pdf_path.exists()
    assert jd_path.exists()

    # Step 1: File validation
    is_valid_file, msg = validate_file_upload(pdf_path.name, pdf_path.stat().st_size)
    assert is_valid_file is True
    assert msg == ""

    # Step 2: Job description validation
    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()
    is_valid_jd, msg = validate_job_description(jd_text)
    assert is_valid_jd is True

    # Step 3: Extract text from PDF
    resume_text, pages, warning = extract_text_from_file(str(pdf_path), pdf_path.name)
    assert len(resume_text) > 200
    assert pages >= 1
    assert warning == ""

    # Step 4: Extract contact details and parse sections
    contact = extract_contact_info(resume_text)
    assert contact["email"] is not None
    assert "alex.rivera@example.com" in contact["email"]
    assert contact["phone"] is not None

    sections = parse_resume_sections(resume_text)
    assert sections["Skills"] != "Not Detected"
    assert sections["Experience"] != "Not Detected"

    # Step 5: Skill Extraction & Comparison
    extractor = SkillExtractor()
    resume_skills = extractor.extract_skills(resume_text)
    jd_skills = extractor.extract_skills(jd_text)

    gap = extractor.compare_skills(resume_skills["all_skills"], jd_skills["all_skills"])
    assert gap["matched_count"] > 0
    assert gap["total_required"] > 0
    assert "Python" in gap["matched_skills"]
    assert "FastAPI" in gap["matched_skills"]

    # Step 6: Similarity & Hybrid Score
    match_details = compute_match_details(resume_text, jd_text, gap)
    assert match_details["overall_score"] > 40.0
    assert match_details["fit_level"] in ["High Match", "Moderate Match", "Needs Development"]
    assert len(match_details["top_shared_keywords"]) > 0

    # Step 7: Recommendations
    recs = generate_recommendations(resume_text, sections, contact, gap)
    assert len(recs) >= 1

    # Step 8: Database operations with temporary database
    db_file = tmp_path / "integration_test.db"
    init_db(db_file)

    rec_id = save_analysis(
        resume_name=pdf_path.name,
        job_title="Senior Python Backend Engineer",
        overall_score=match_details["overall_score"],
        tfidf_score=match_details["tfidf_score_pct"],
        skill_score=match_details["skill_score_pct"],
        matched_skills=gap["matched_skills"],
        missing_skills=gap["missing_skills"],
        notes="Automated PDF End-to-End Test",
        db_path=db_file,
    )
    assert rec_id == 1

    all_analyses = get_all_analyses(db_file)
    assert len(all_analyses) == 1
    assert all_analyses[0]["id"] == rec_id
    assert all_analyses[0]["resume_name"] == pdf_path.name

    stats = get_history_summary_stats(db_file)
    assert stats["total_analyses"] == 1
    assert stats["avg_score"] == match_details["overall_score"]

    # Delete record
    deleted = delete_analysis(rec_id, db_file)
    assert deleted is True
    assert len(get_all_analyses(db_file)) == 0


def test_full_analysis_workflow_docx(tmp_path: Path):
    """End-to-end integration test from DOCX upload."""
    docx_path = DATA_DIR / "sample_resume.docx"
    jd_path = DATA_DIR / "sample_job_description.txt"

    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    # Extract text from DOCX
    resume_text, pages, warning = extract_text_from_file(str(docx_path), docx_path.name)
    assert len(resume_text) > 200
    assert "FastAPI" in resume_text

    # Extract skills
    extractor = SkillExtractor()
    resume_skills = extractor.extract_skills(resume_text)
    jd_skills = extractor.extract_skills(jd_text)
    gap = extractor.compare_skills(resume_skills["all_skills"], jd_skills["all_skills"])

    assert gap["matched_count"] > 0
    assert "Docker" in gap["matched_skills"]
