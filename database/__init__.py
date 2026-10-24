"""
Database Package
----------------
SQLite local storage for analysis history, versions, and session metrics.
"""

from .db import (
    init_db,
    save_analysis,
    save_resume_version,
    get_resume_versions,
    get_all_analyses,
    get_analysis_by_id,
    compare_analysis_records,
    delete_analysis,
    clear_all_analyses,
    get_history_summary_stats,
)

__all__ = [
    "init_db",
    "save_analysis",
    "save_resume_version",
    "get_resume_versions",
    "get_all_analyses",
    "get_analysis_by_id",
    "compare_analysis_records",
    "delete_analysis",
    "clear_all_analyses",
    "get_history_summary_stats",
]
