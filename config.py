"""
ResumeIQ Configuration Module
-----------------------------
Centralized configuration settings for ResumeIQ application:
file constraints, scoring models, synonym dictionaries, theme constants, and AI provider settings.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "sample_data"
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "resume_iq.db"
SKILLS_FILE = DATA_DIR / "skills_data.json"
ASSETS_DIR = BASE_DIR / "assets"
CSS_PATH = ASSETS_DIR / "styles.css"

# Application Metadata
APP_NAME = "ResumeIQ"
APP_TAGLINE = "AI-Powered ATS Resume Analyzer & Job Match Platform"
APP_VERSION = "2.0.0"

# File Upload Constraints
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# -----------------------------------------------------------------------------
# Distinct Scoring Weights Architecture
# These three scores serve fundamentally different purposes and are never interchangeable:
# 1. Resume Quality Score: How well the resume is written, structured, and quantified.
# 2. ATS Compatibility Score: How reliably an Applicant Tracking System can parse the file.
# 3. Job Match Score: How closely candidate skills and experience match the target job post.
# -----------------------------------------------------------------------------
RESUME_QUALITY_WEIGHTS = {
    "content_completeness": 0.15,
    "work_experience_achievements": 0.25,
    "skills_and_evidence": 0.20,
    "summary_and_clarity": 0.15,
    "grammar_and_readability": 0.10,
    "structure_and_formatting": 0.15
}

ATS_COMPATIBILITY_WEIGHTS = {
    "text_extraction_reliability": 0.25,
    "standard_section_headings": 0.25,
    "contact_info_completeness": 0.20,
    "layout_formatting_risk": 0.20,
    "file_format_and_length": 0.10
}

JOB_MATCH_WEIGHTS = {
    "required_skills": 0.45,
    "preferred_skills": 0.15,
    "semantic_tfidf": 0.20,
    "experience_alignment": 0.20
}

# Legacy scoring weights backwards compatibility
SCORING_WEIGHTS = {
    "tfidf_weight": 0.40,
    "skill_weight": 0.60
}

# Configurable Synonym & Abbreviation Mapping for Semantic Keyword Matching
SYNONYM_DICTIONARY = {
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "py": "python",
    "python": "python",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "aws": "amazon web services",
    "amazon web services": "aws",
    "gcp": "google cloud",
    "google cloud": "gcp",
    "azure": "microsoft azure",
    "microsoft azure": "azure",
    "ml": "machine learning",
    "machine learning": "ml",
    "ai": "artificial intelligence",
    "artificial intelligence": "ai",
    "nlp": "natural language processing",
    "natural language processing": "nlp",
    "ci/cd": "continuous integration",
    "continuous integration": "ci/cd",
    "tdd": "test driven development",
    "oop": "object oriented programming",
    "react.js": "react",
    "vue.js": "vue",
    "node": "node.js",
    "node.js": "node.js"
}

# AI Assistant Settings (Server-side Configurable)
AI_CONFIG = {
    "default_provider": os.getenv("AI_PROVIDER", "local"),  # "local", "gemini", or "openai"
    "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "gemini_model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
    "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini")
}

# UI Theme Palette (Cohesive Slate & Indigo/Electric Blue Dark Theme)
THEME_COLORS = {
    "bg_dark": "#0F172A",        # Slate 900
    "card_bg": "#1E293B",        # Slate 800
    "card_border": "#334155",    # Slate 700
    "text_primary": "#F8FAFC",   # Slate 50
    "text_secondary": "#94A3B8", # Slate 400
    "accent_primary": "#6366F1", # Indigo 500
    "accent_secondary": "#3B82F6", # Blue 500
    "success": "#10B981",        # Emerald 500
    "warning": "#F59E0B",        # Amber 500
    "danger": "#EF4444",         # Red 500
    "info": "#06B6D4"            # Cyan 500
}
