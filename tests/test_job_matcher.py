"""
Unit Tests for Job Description Matcher Module
---------------------------------------------
Tests requirement partitioning, synonym expansion, evidence mapping,
keyword stuffing detection, and match score calculations.
"""

import pytest
from analyzer.job_matcher import (
    detect_keyword_stuffing,
    expand_synonyms,
    match_resume_to_job,
    partition_jd_requirements,
)
from analyzer.skill_extractor import SkillExtractor


def test_expand_synonyms():
    """Verify alias mapping for technologies like K8s, JS, Postgres."""
    k8s_aliases = expand_synonyms("k8s")
    assert "kubernetes" in k8s_aliases
    assert "k8s" in k8s_aliases

    js_aliases = expand_synonyms("javascript")
    assert "js" in js_aliases

    aws_aliases = expand_synonyms("aws")
    assert "amazon web services" in aws_aliases


def test_partition_jd_requirements():
    """Verify separating required from preferred job qualifications."""
    jd_text = """
    REQUIRED QUALIFICATIONS:
    - 4+ years of Python engineering
    - Proven experience with FastAPI and PostgreSQL
    - Hands-on experience with Docker

    NICE TO HAVE / PREFERRED:
    - Experience with Kubernetes cluster management
    - Knowledge of GraphQL
    """
    extractor = SkillExtractor()
    req_skills, pref_skills = partition_jd_requirements(jd_text, extractor)

    assert "Python" in req_skills
    assert "FastAPI" in req_skills
    assert "PostgreSQL" in req_skills
    assert "Docker" in req_skills

    assert "Kubernetes" in pref_skills
    assert "GraphQL" in pref_skills


def test_match_resume_to_job_empty_jd():
    """Verify empty job description returns explicit un-evaluated status."""
    res = match_resume_to_job("Python developer with Docker", "")
    assert res["has_job_description"] is False
    assert res["job_match_score"] == 0.0


def test_match_resume_to_job_matched_flow():
    """Verify end-to-end matching with evidence mapping and coverage percentages."""
    resume_text = """
    ALEX RIVERA
    Senior Python engineer specializing in FastAPI and PostgreSQL.
    Architected microservices using Docker containers and deployed on AWS.
    Managed Redis cache clusters.
    """
    jd_text = """
    Required Qualifications:
    - Strong proficiency in Python and FastAPI
    - Relational database experience with PostgreSQL
    - Containerization experience with Docker

    Nice to have:
    - Redis caching
    - Kubernetes orchestration
    """

    res = match_resume_to_job(resume_text, jd_text, target_job_title="Python Engineer")

    assert res["has_job_description"] is True
    assert res["job_match_score"] >= 70.0
    assert "Python" in res["required_skills"]["matched"]
    assert "FastAPI" in res["required_skills"]["matched"]
    assert "Docker" in res["required_skills"]["matched"]
    assert "Kubernetes" in res["preferred_skills"]["missing"]
    assert len(res["evidence_map"]) >= 2


def test_detect_keyword_stuffing():
    """Verify detection of suspicious repetitive keyword density."""
    stuffed_resume = "Python Python Python Python Python Python Python Python developer building systems."
    stuffing = detect_keyword_stuffing(stuffed_resume, {"Python"})
    assert len(stuffing) >= 1
    assert stuffing[0]["skill"] == "Python"
