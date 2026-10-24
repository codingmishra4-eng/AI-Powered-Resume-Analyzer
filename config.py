"""
ResumeIQ Configuration Module
-----------------------------
Centralized configuration settings for ResumeIQ application:
paths, file constraints, matching weights, and UI theme constants.
"""

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
APP_TAGLINE = "AI-Powered Resume Analyzer & Job Match Platform"
APP_VERSION = "1.0.0"

# File Upload Constraints
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# Scoring Weights
# The overall compatibility score combines:
# 1. TF-IDF Cosine Similarity (Textual/Semantic match across description and resume)
# 2. Skill Overlap Ratio (Direct match of extracted technical and soft skills)
SCORING_WEIGHTS = {
    "tfidf_weight": 0.40,
    "skill_weight": 0.60
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
