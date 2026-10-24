"""
Unit Tests for Skill Extractor Module
-------------------------------------
Tests taxonomy-based skill extraction, word boundary accuracy,
multi-word skill matching, and gap analysis logic.
"""

import pytest
from analyzer.skill_extractor import SkillExtractor


@pytest.fixture
def extractor():
    """Provides a fresh SkillExtractor instance."""
    return SkillExtractor()


def test_skill_extraction_basic(extractor):
    """Test standard skill extraction from text."""
    sample = "Experienced in Python, PostgreSQL, and Docker containerization."
    result = extractor.extract_skills(sample)

    assert "Python" in result["all_skills"]
    assert "PostgreSQL" in result["all_skills"]
    assert "Docker" in result["all_skills"]
    assert result["total_count"] >= 3


def test_special_characters_and_word_boundaries(extractor):
    """Ensure C++, C#, Go match properly without false positives on words like 'going'."""
    sample = "We are coding in C++ and C# for high-performance modules. Going forward, we plan to scale."
    result = extractor.extract_skills(sample)

    assert "C++" in result["all_skills"]
    assert "C#" in result["all_skills"]
    # 'Going' should NOT trigger 'Go'
    assert "Go" not in result["all_skills"]


def test_multi_word_skills(extractor):
    """Ensure multi-word skills like 'Machine Learning' and 'GitHub Actions' are recognized."""
    sample = "Specialist in Machine Learning, Natural Language Processing, and GitHub Actions."
    result = extractor.extract_skills(sample)

    assert "Machine Learning" in result["all_skills"]
    assert "GitHub Actions" in result["all_skills"]


def test_add_custom_skill(extractor):
    """Verify adding custom skills dynamically."""
    custom_name = "SolanaWeb3"
    assert extractor.add_custom_skill(custom_name, "Blockchain") is True

    # Re-adding the same should return False
    assert extractor.add_custom_skill(custom_name, "Blockchain") is False

    # Check extraction of the new skill
    sample = "Building smart contracts on SolanaWeb3."
    res = extractor.extract_skills(sample)
    assert custom_name in res["all_skills"]


def test_compare_skills_gap_analysis(extractor):
    """Verify matched, missing, additional, and prioritized skill calculations."""
    resume_skills = {"Python", "FastAPI", "PostgreSQL", "Docker", "Git"}
    job_skills = {"Python", "FastAPI", "Docker", "Kubernetes", "Redis", "Kafka"}

    gap = extractor.compare_skills(resume_skills, job_skills)

    assert gap["matched_count"] == 3
    assert set(gap["matched_skills"]) == {"Python", "FastAPI", "Docker"}

    assert gap["missing_count"] == 3
    assert set(gap["missing_skills"]) == {"Kubernetes", "Redis", "Kafka"}

    assert gap["additional_skills"] == ["Git", "PostgreSQL"]
    assert gap["overlap_ratio"] == 0.5
    assert gap["overlap_percentage"] == 50.0

    # Priorities should include missing technical skills
    assert len(gap["suggested_priorities"]) > 0
    assert any(s in gap["suggested_priorities"] for s in ["Kubernetes", "Redis"])
