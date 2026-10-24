"""
SQLite Database Module
----------------------
Manages persistence for resume analysis records, distinct score breakdowns,
and resume versions using SQLite. All database operations utilize parameterized
queries to prevent SQL injection. Sensitive full resume text is excluded to
protect candidate privacy.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from config import APP_VERSION, DB_PATH


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
    Initializes database tables and runs schema migrations if needed.
    """
    create_analyses_table = """
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        resume_name TEXT NOT NULL,
        job_title TEXT,
        overall_score REAL NOT NULL,
        quality_score REAL DEFAULT 0.0,
        ats_score REAL DEFAULT 0.0,
        job_match_score REAL DEFAULT 0.0,
        tfidf_score REAL NOT NULL,
        skill_score REAL NOT NULL,
        matched_skills TEXT NOT NULL,
        missing_skills TEXT NOT NULL,
        matched_count INTEGER NOT NULL,
        missing_count INTEGER NOT NULL,
        quality_breakdown TEXT DEFAULT '{}',
        ats_breakdown TEXT DEFAULT '{}',
        job_match_breakdown TEXT DEFAULT '{}',
        version_label TEXT DEFAULT 'v1.0',
        scoring_model_version TEXT DEFAULT '2.0.0',
        notes TEXT
    );
    """

    create_versions_table = """
    CREATE TABLE IF NOT EXISTS resume_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        resume_name TEXT NOT NULL,
        version_label TEXT NOT NULL,
        structured_data TEXT NOT NULL,
        notes TEXT
    );
    """

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(create_analyses_table)
        cursor.execute(create_versions_table)

        # Migration check: Ensure new columns exist if table was created in v1
        cursor.execute("PRAGMA table_info(analyses);")
        columns = [row["name"] for row in cursor.fetchall()]

        new_columns = [
            ("quality_score", "REAL DEFAULT 0.0"),
            ("ats_score", "REAL DEFAULT 0.0"),
            ("job_match_score", "REAL DEFAULT 0.0"),
            ("quality_breakdown", "TEXT DEFAULT '{}'"),
            ("ats_breakdown", "TEXT DEFAULT '{}'"),
            ("job_match_breakdown", "TEXT DEFAULT '{}'"),
            ("version_label", "TEXT DEFAULT 'v1.0'"),
            ("scoring_model_version", "TEXT DEFAULT '2.0.0'"),
        ]

        for col_name, col_type in new_columns:
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE analyses ADD COLUMN {col_name} {col_type};")

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
    quality_score: float = 0.0,
    ats_score: float = 0.0,
    job_match_score: float = 0.0,
    quality_breakdown: Optional[Dict] = None,
    ats_breakdown: Optional[Dict] = None,
    job_match_breakdown: Optional[Dict] = None,
    version_label: str = "v1.0",
    db_path: Path = DB_PATH
) -> int:
    """
    Inserts a new analysis record using safe parameterized SQL.
    Supports both legacy calls and upgraded multi-score records.
    """
    init_db(db_path)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    matched_json = json.dumps(matched_skills)
    missing_json = json.dumps(missing_skills)
    quality_json = json.dumps(quality_breakdown or {})
    ats_json = json.dumps(ats_breakdown or {})
    job_match_json = json.dumps(job_match_breakdown or {})

    insert_query = """
    INSERT INTO analyses (
        timestamp, resume_name, job_title, overall_score,
        quality_score, ats_score, job_match_score,
        tfidf_score, skill_score, matched_skills, missing_skills,
        matched_count, missing_count, quality_breakdown,
        ats_breakdown, job_match_breakdown, version_label,
        scoring_model_version, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
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
                round(float(quality_score), 1),
                round(float(ats_score), 1),
                round(float(job_match_score), 1),
                round(float(tfidf_score), 1),
                round(float(skill_score), 1),
                matched_json,
                missing_json,
                len(matched_skills),
                len(missing_skills),
                quality_json,
                ats_json,
                job_match_json,
                version_label,
                APP_VERSION,
                notes
            )
        )
        conn.commit()
        return cursor.lastrowid


def save_resume_version(
    resume_name: str,
    version_label: str,
    structured_data: Dict[str, any],
    notes: str = "",
    db_path: Path = DB_PATH
) -> int:
    """
    Saves a snapshot version of the structured resume for historical comparison.
    """
    init_db(db_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_json = json.dumps(structured_data)

    query = """
    INSERT INTO resume_versions (timestamp, resume_name, version_label, structured_data, notes)
    VALUES (?, ?, ?, ?, ?);
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (timestamp, resume_name, version_label, data_json, notes))
        conn.commit()
        return cursor.lastrowid


def get_resume_versions(resume_name: Optional[str] = None, db_path: Path = DB_PATH) -> List[Dict[str, any]]:
    """
    Retrieves saved resume versions, optionally filtered by resume name.
    """
    init_db(db_path)
    if resume_name:
        query = "SELECT * FROM resume_versions WHERE resume_name = ? ORDER BY id DESC;"
        params = (resume_name,)
    else:
        query = "SELECT * FROM resume_versions ORDER BY id DESC;"
        params = ()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    results = []
    for r in rows:
        item = dict(r)
        try:
            item["structured_data"] = json.loads(item["structured_data"])
        except Exception:
            item["structured_data"] = {}
        results.append(item)
    return results


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
            item["quality_breakdown"] = json.loads(item.get("quality_breakdown", "{}"))
            item["ats_breakdown"] = json.loads(item.get("ats_breakdown", "{}"))
            item["job_match_breakdown"] = json.loads(item.get("job_match_breakdown", "{}"))
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
        item["quality_breakdown"] = json.loads(item.get("quality_breakdown", "{}"))
        item["ats_breakdown"] = json.loads(item.get("ats_breakdown", "{}"))
        item["job_match_breakdown"] = json.loads(item.get("job_match_breakdown", "{}"))
    except Exception:
        item["matched_skills"] = []
        item["missing_skills"] = []

    return item


def compare_analysis_records(id_a: int, id_b: int, db_path: Path = DB_PATH) -> Optional[Dict[str, any]]:
    """
    Compares two analysis records to show score deltas and added/removed skills.
    """
    rec_a = get_analysis_by_id(id_a, db_path)
    rec_b = get_analysis_by_id(id_b, db_path)

    if not rec_a or not rec_b:
        return None

    skills_a = set(rec_a.get("matched_skills", []))
    skills_b = set(rec_b.get("matched_skills", []))

    newly_added = sorted(list(skills_b.difference(skills_a)))
    removed = sorted(list(skills_a.difference(skills_b)))

    return {
        "record_a": rec_a,
        "record_b": rec_b,
        "overall_score_delta": round(rec_b["overall_score"] - rec_a["overall_score"], 1),
        "quality_score_delta": round(rec_b.get("quality_score", 0.0) - rec_a.get("quality_score", 0.0), 1),
        "ats_score_delta": round(rec_b.get("ats_score", 0.0) - rec_a.get("ats_score", 0.0), 1),
        "job_match_delta": round(rec_b.get("job_match_score", 0.0) - rec_a.get("job_match_score", 0.0), 1),
        "newly_added_skills": newly_added,
        "removed_skills": removed
    }


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
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analyses;")
        cursor.execute("DELETE FROM resume_versions;")
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
        MIN(overall_score) as min_score,
        AVG(quality_score) as avg_quality,
        AVG(ats_score) as avg_ats
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
            "min_score": 0.0,
            "avg_quality": 0.0,
            "avg_ats": 0.0
        }

    return {
        "total_analyses": int(row["total_count"]),
        "avg_score": round(float(row["avg_score"] or 0.0), 1),
        "max_score": round(float(row["max_score"] or 0.0), 1),
        "min_score": round(float(row["min_score"] or 0.0), 1),
        "avg_quality": round(float(row["avg_quality"] or 0.0), 1),
        "avg_ats": round(float(row["avg_ats"] or 0.0), 1)
    }
