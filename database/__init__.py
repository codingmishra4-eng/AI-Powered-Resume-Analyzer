"""
Database Package
----------------
SQLite local storage for analysis history and session metrics.
"""

from .db import (
    init_db,
    save_analysis,
    get_all_analyses,
    get_analysis_by_id,
    delete_analysis,
    clear_all_analyses,
    get_history_summary_stats,
)

__all__ = [
    "init_db",
    "save_analysis",
    "get_all_analyses",
    "get_analysis_by_id",
    "delete_analysis",
    "clear_all_analyses",
    "get_history_summary_stats",
]
