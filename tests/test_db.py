"""
Unit Tests for Database Module
------------------------------
Tests SQLite schema creation, record insertion, querying,
deletion, and summary metric aggregations using temporary test databases.
"""

from pathlib import Path
import pytest
from database.db import (
    clear_all_analyses,
    delete_analysis,
    get_all_analyses,
    get_analysis_by_id,
    get_history_summary_stats,
    init_db,
    save_analysis,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Creates a temporary SQLite database path for isolated testing."""
    test_db_path = tmp_path / "test_resume_iq.db"
    init_db(test_db_path)
    return test_db_path


def test_init_db(temp_db: Path):
    """Ensure database file is created and accessible."""
    assert temp_db.exists()


def test_save_and_retrieve_analysis(temp_db: Path):
    """Test saving a record and retrieving it with deserialized skill lists."""
    rec_id = save_analysis(
        resume_name="candidate_cv.pdf",
        job_title="Backend Python Developer",
        overall_score=82.5,
        tfidf_score=78.0,
        skill_score=85.0,
        matched_skills=["Python", "FastAPI", "Docker"],
        missing_skills=["Kubernetes"],
        notes="First interview run",
        db_path=temp_db,
    )
    assert rec_id == 1

    records = get_all_analyses(temp_db)
    assert len(records) == 1
    item = records[0]
    assert item["id"] == 1
    assert item["resume_name"] == "candidate_cv.pdf"
    assert item["overall_score"] == 82.5
    assert item["matched_skills"] == ["Python", "FastAPI", "Docker"]
    assert item["missing_skills"] == ["Kubernetes"]
    assert item["matched_count"] == 3
    assert item["missing_count"] == 1
    assert item["notes"] == "First interview run"


def test_get_analysis_by_id(temp_db: Path):
    """Test fetching specific record by ID."""
    rec_id = save_analysis(
        resume_name="test.pdf",
        job_title="Data Scientist",
        overall_score=90.0,
        tfidf_score=88.0,
        skill_score=92.0,
        matched_skills=["Pandas", "Scikit-Learn"],
        missing_skills=[],
        db_path=temp_db,
    )
    item = get_analysis_by_id(rec_id, temp_db)
    assert item is not None
    assert item["job_title"] == "Data Scientist"

    # Non-existent ID
    none_item = get_analysis_by_id(9999, temp_db)
    assert none_item is None


def test_delete_analysis(temp_db: Path):
    """Test deleting single record."""
    id1 = save_analysis("r1.pdf", "Role 1", 70.0, 70.0, 70.0, [], [], db_path=temp_db)
    id2 = save_analysis("r2.pdf", "Role 2", 80.0, 80.0, 80.0, [], [], db_path=temp_db)

    assert len(get_all_analyses(temp_db)) == 2
    deleted = delete_analysis(id1, temp_db)
    assert deleted is True

    remaining = get_all_analyses(temp_db)
    assert len(remaining) == 1
    assert remaining[0]["id"] == id2


def test_clear_all_analyses(temp_db: Path):
    """Test wiping all historical records."""
    save_analysis("r1.pdf", "Role 1", 70.0, 70.0, 70.0, [], [], db_path=temp_db)
    save_analysis("r2.pdf", "Role 2", 80.0, 80.0, 80.0, [], [], db_path=temp_db)

    clear_all_analyses(temp_db)
    assert len(get_all_analyses(temp_db)) == 0


def test_summary_stats(temp_db: Path):
    """Test summary aggregations."""
    # Empty stats
    empty_stats = get_history_summary_stats(temp_db)
    assert empty_stats["total_analyses"] == 0
    assert empty_stats["avg_score"] == 0.0

    # Populated stats
    save_analysis("r1.pdf", "Role 1", 60.0, 60.0, 60.0, [], [], db_path=temp_db)
    save_analysis("r2.pdf", "Role 2", 80.0, 80.0, 80.0, [], [], db_path=temp_db)

    stats = get_history_summary_stats(temp_db)
    assert stats["total_analyses"] == 2
    assert stats["avg_score"] == 70.0
    assert stats["max_score"] == 80.0
    assert stats["min_score"] == 60.0
