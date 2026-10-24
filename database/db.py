"""
SQLite Database Module
----------------------
Manages persistence for resume analysis records using SQLite.
All database operations utilize parameterized queries to prevent SQL injection.
Sensitive full resume text is excluded to protect candidate privacy.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from config import DB_PATH


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.
    Ensures parent directories exist before connecting.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Enables column access by dictionary-style key names
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    """
    Initializes the database schema if it does not already exist.

    Table Schema: 'analyses'
    -----------------------
    - id: INTEGER (Primary Key, Auto-incremented)
    - timestamp: TEXT (ISO 8601 creation timestamp)
    - resume_name: TEXT (Original file name or candidate label)
    - job_title: TEXT (Target job title or role tag)
    - overall_score: REAL (Weighted hybrid score 0-100)
    - tfidf_score: REAL (TF-IDF cosine similarity 0-100)
    - skill_score: REAL (Direct skill overlap score 0-100)
    - matched_skills: TEXT (JSON serialized list of matching skills)
    - missing_skills: TEXT (JSON serialized list of missing skills)
    - matched_count: INTEGER (Count of matched skills)
    - missing_count: INTEGER (Count of missing skills)
    - notes: TEXT (User notes or status)
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        resume_name TEXT NOT NULL,
        job_title TEXT,
        overall_score REAL NOT NULL,
        tfidf_score REAL NOT NULL,
        skill_score REAL NOT NULL,
        matched_skills TEXT NOT NULL,
        missing_skills TEXT NOT NULL,
        matched_count INTEGER NOT NULL,
        missing_count INTEGER NOT NULL,
        notes TEXT
    );
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()


def save_analysis(
    resume_name: str,
    job_title: str,
    overall_score: float,
    tfidf_score: float,
    skill_score: float,
    matched_skills: List[str],
    missing_skills: List[str],
    notes: str = "",
    db_path: Path = DB_PATH
) -> int:
    """
    Inserts a new analysis record using safe parameterized SQL.

    Returns:
        int: The auto-generated row ID of the inserted record.
    """
    init_db(db_path)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    matched_json = json.dumps(matched_skills)
    missing_json = json.dumps(missing_skills)

    insert_query = """
    INSERT INTO analyses (
        timestamp, resume_name, job_title, overall_score,
        tfidf_score, skill_score, matched_skills, missing_skills,
        matched_count, missing_count, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            insert_query,
            (
                timestamp,
                resume_name,
                job_title or "Unspecified Position",
                round(float(overall_score), 1),
                round(float(tfidf_score), 1),
                round(float(skill_score), 1),
                matched_json,
                missing_json,
                len(matched_skills),
                len(missing_skills),
                notes
            )
        )
        conn.commit()
        return cursor.lastrowid


def get_all_analyses(db_path: Path = DB_PATH) -> List[Dict[str, any]]:
    """
    Retrieves all analysis records sorted in descending order of creation time.
    """
    init_db(db_path)
    query = "SELECT * FROM analyses ORDER BY id DESC;"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

    results = []
    for row in rows:
        item = dict(row)
        try:
            item["matched_skills"] = json.loads(item["matched_skills"])
            item["missing_skills"] = json.loads(item["missing_skills"])
        except Exception:
            item["matched_skills"] = []
            item["missing_skills"] = []
        results.append(item)

    return results


def get_analysis_by_id(analysis_id: int, db_path: Path = DB_PATH) -> Optional[Dict[str, any]]:
    """
    Retrieves a single analysis record by its primary key ID.
    """
    init_db(db_path)
    query = "SELECT * FROM analyses WHERE id = ?;"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (analysis_id,))
        row = cursor.fetchone()

    if not row:
        return None

    item = dict(row)
    try:
        item["matched_skills"] = json.loads(item["matched_skills"])
        item["missing_skills"] = json.loads(item["missing_skills"])
    except Exception:
        item["matched_skills"] = []
        item["missing_skills"] = []

    return item


def delete_analysis(analysis_id: int, db_path: Path = DB_PATH) -> bool:
    """
    Deletes a specific analysis record by ID using parameterized query.
    """
    init_db(db_path)
    query = "DELETE FROM analyses WHERE id = ?;"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (analysis_id,))
        conn.commit()
        return cursor.rowcount > 0


def clear_all_analyses(db_path: Path = DB_PATH) -> bool:
    """
    Deletes all records from the analyses table.
    """
    init_db(db_path)
    query = "DELETE FROM analyses;"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        return True


def get_history_summary_stats(db_path: Path = DB_PATH) -> Dict[str, any]:
    """
    Computes quick aggregate stats for overview metric cards on the dashboard.
    """
    init_db(db_path)
    query = """
    SELECT 
        COUNT(*) as total_count,
        AVG(overall_score) as avg_score,
        MAX(overall_score) as max_score,
        MIN(overall_score) as min_score
    FROM analyses;
    """

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        row = cursor.fetchone()

    if not row or row["total_count"] == 0:
        return {
            "total_analyses": 0,
            "avg_score": 0.0,
            "max_score": 0.0,
            "min_score": 0.0
        }

    return {
        "total_analyses": int(row["total_count"]),
        "avg_score": round(float(row["avg_score"]), 1),
        "max_score": round(float(row["max_score"]), 1),
        "min_score": round(float(row["min_score"]), 1)
    }
