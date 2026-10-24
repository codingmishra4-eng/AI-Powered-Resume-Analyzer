"""
ResumeIQ Analyzer Package
-------------------------
Core NLP, extraction, similarity, ATS diagnostics, quality scoring,
AI assistant, and resume builder engine.
"""

from .text_preprocessing import clean_text, tokenize_text, remove_stopwords, preprocess_for_tfidf
from .resume_parser import (
    extract_text_from_file,
    parse_resume_sections,
    extract_contact_info,
    extract_candidate_name,
    extract_location,
    parse_full_resume_structure,
)
from .skill_extractor import SkillExtractor
from .similarity import calculate_similarity, calculate_tfidf_similarity, compute_match_details
from .recommendations import generate_recommendations
from .ats_analyzer import analyze_ats_compatibility
from .quality_analyzer import analyze_resume_quality, audit_bullet_points
from .job_matcher import match_resume_to_job, expand_synonyms, detect_keyword_stuffing
from .ai_assistant import ResumeAssistant
from .resume_builder import (
    generate_docx_resume,
    generate_pdf_resume,
    generate_analysis_report,
    verify_generated_resume_extractability,
)

__all__ = [
    "clean_text",
    "tokenize_text",
    "remove_stopwords",
    "preprocess_for_tfidf",
    "extract_text_from_file",
    "parse_resume_sections",
    "extract_contact_info",
    "extract_candidate_name",
    "extract_location",
    "parse_full_resume_structure",
    "SkillExtractor",
    "calculate_similarity",
    "calculate_tfidf_similarity",
    "compute_match_details",
    "generate_recommendations",
    "analyze_ats_compatibility",
    "analyze_resume_quality",
    "audit_bullet_points",
    "match_resume_to_job",
    "expand_synonyms",
    "detect_keyword_stuffing",
    "ResumeAssistant",
    "generate_docx_resume",
    "generate_pdf_resume",
    "generate_analysis_report",
    "verify_generated_resume_extractability",
]
