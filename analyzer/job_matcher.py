"""
Job Description Matching & Keyword Analysis Engine
--------------------------------------------------
Compares candidate resume against target job description.
Separates required vs preferred requirements, expands synonyms,
maps evidence snippets, and calculates an explainable Job Match Score.
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from config import JOB_MATCH_WEIGHTS, SYNONYM_DICTIONARY
from analyzer.similarity import calculate_tfidf_similarity
from analyzer.skill_extractor import SkillExtractor


def expand_synonyms(skill_name: str) -> Set[str]:
    """
    Expands a skill name into its known canonical synonyms and abbreviations.
    Example: 'k8s' -> {'k8s', 'kubernetes'}
    """
    cleaned = skill_name.lower().strip()
    synonyms = {cleaned}

    # Check direct dictionary mapping
    canonical = SYNONYM_DICTIONARY.get(cleaned, cleaned)
    synonyms.add(canonical)

    # Reverse lookup for all aliases of this canonical skill
    for alias, can in SYNONYM_DICTIONARY.items():
        if can == canonical:
            synonyms.add(alias)

    return synonyms


def partition_jd_requirements(jd_text: str, extractor: SkillExtractor) -> Tuple[Set[str], Set[str]]:
    """
    Partitions skills identified in the Job Description into
    'Required / Minimum Qualifications' and 'Preferred / Nice-to-Have'.
    """
    if not jd_text:
        return set(), set()

    lines = jd_text.split("\n")
    required_text = []
    preferred_text = []
    general_text = []

    current_mode = "general"

    for line in lines:
        lower = line.lower()
        if any(h in lower for h in ["preferred qualification", "nice to have", "bonus points", "bonus skills", "preferred skills"]):
            current_mode = "preferred"
            continue
        elif any(h in lower for h in ["required qualification", "must have", "minimum qualification", "basic qualification", "requirements"]):
            current_mode = "required"
            continue

        if current_mode == "preferred":
            preferred_text.append(line)
        elif current_mode == "required":
            required_text.append(line)
        else:
            general_text.append(line)

    # Extract skills from each partitioned block
    req_skills_data = extractor.extract_skills("\n".join(required_text))["all_skills"]
    pref_skills_data = extractor.extract_skills("\n".join(preferred_text))["all_skills"]
    gen_skills_data = extractor.extract_skills("\n".join(general_text))["all_skills"]

    # If explicit sections were found, assign general skills to required by default
    if req_skills_data or pref_skills_data:
        all_required = req_skills_data.union(gen_skills_data.difference(pref_skills_data))
        all_preferred = pref_skills_data
    else:
        # Default split: primary technical skills as required
        all_required = gen_skills_data
        all_preferred = set()

    return all_required, all_preferred


def map_skill_evidence(skill: str, resume_text: str) -> List[str]:
    """
    Finds sentence or bullet point evidence where a skill is mentioned in the resume.
    """
    if not skill or not resume_text:
        return []

    aliases = expand_synonyms(skill)
    evidence = []
    lines = [line.strip().lstrip("•-* ") for line in resume_text.split("\n") if line.strip()]

    for line in lines:
        line_lower = line.lower()
        for alias in aliases:
            if re.search(rf"\b{re.escape(alias)}\b", line_lower):
                evidence.append(line)
                break
        if len(evidence) >= 2:
            break

    return evidence


def detect_keyword_stuffing(resume_text: str, detected_skills: Set[str]) -> List[Dict[str, any]]:
    """
    Detects potential keyword stuffing where terms are repeated excessively
    without corresponding contextual action verbs.
    """
    if not resume_text or not detected_skills:
        return []

    words = resume_text.lower().split()
    total_words = max(1, len(words))
    stuffing_warnings = []

    for skill in detected_skills:
        aliases = expand_synonyms(skill)
        count = 0
        for alias in aliases:
            count += len(re.findall(rf"\b{re.escape(alias)}\b", resume_text, re.IGNORECASE))

        # If a single skill accounts for > 2.5% of total resume word count (and appears > 6 times)
        density = count / total_words
        if count >= 7 and density > 0.025:
            stuffing_warnings.append({
                "skill": skill,
                "count": count,
                "density_pct": round(density * 100, 2),
                "warning": f"'{skill}' appears {count} times ({round(density*100, 1)}% density). Avoid artificial repetition."
            })

    return stuffing_warnings


def match_resume_to_job(
    resume_text: str,
    job_description: str,
    target_job_title: str = "",
    extractor: Optional[SkillExtractor] = None
) -> Dict[str, any]:
    """
    Performs comprehensive job description matching:
    - Required vs Preferred skill coverage
    - Semantic TF-IDF alignment
    - Evidence mapping
    - Keyword stuffing check
    - Explainable Job Match Score (0-100)
    """
    if not job_description or not job_description.strip():
        return {
            "has_job_description": False,
            "job_match_score": 0.0,
            "message": "No job description provided. Paste a target job description to calculate role alignment."
        }

    if extractor is None:
        extractor = SkillExtractor()

    # 1. Extract and partition JD skills
    req_jd_skills, pref_jd_skills = partition_jd_requirements(job_description, extractor)
    all_jd_skills = req_jd_skills.union(pref_jd_skills)
    resume_skills_data = extractor.extract_skills(resume_text)
    resume_skills = resume_skills_data["all_skills"]

    # 2. Match with synonym support
    matched_required = set()
    missing_required = set()

    for r_skill in req_jd_skills:
        aliases = expand_synonyms(r_skill)
        if any(any(re.search(rf"\b{re.escape(a)}\b", resume_text, re.IGNORECASE) for a in aliases) for _ in [1]):
            matched_required.add(r_skill)
        else:
            missing_required.add(r_skill)

    matched_preferred = set()
    missing_preferred = set()

    for p_skill in pref_jd_skills:
        aliases = expand_synonyms(p_skill)
        if any(any(re.search(rf"\b{re.escape(a)}\b", resume_text, re.IGNORECASE) for a in aliases) for _ in [1]):
            matched_preferred.add(p_skill)
        else:
            missing_preferred.add(p_skill)

    # 3. Calculate coverage ratios
    req_ratio = len(matched_required) / len(req_jd_skills) if req_jd_skills else 1.0
    pref_ratio = len(matched_preferred) / len(pref_jd_skills) if pref_jd_skills else 1.0

    # 4. Semantic TF-IDF similarity
    tfidf_score, top_keywords = calculate_tfidf_similarity(resume_text, job_description)

    # 5. Role & Title alignment
    experience_alignment = 80.0
    if target_job_title:
        title_lower = target_job_title.lower()
        if title_lower in resume_text.lower():
            experience_alignment = 100.0
        else:
            # Check for partial title words (e.g. 'Backend', 'Python', 'Engineer')
            title_words = [w for w in title_lower.split() if len(w) > 3]
            matched_words = [w for w in title_words if w in resume_text.lower()]
            if matched_words:
                experience_alignment = 75.0 + (len(matched_words) / len(title_words) * 20.0)
            else:
                experience_alignment = 50.0

    # 6. Weighted Job Match Score
    w = JOB_MATCH_WEIGHTS
    overall_match = (
        ((req_ratio * 100.0) * w["required_skills"]) +
        ((pref_ratio * 100.0) * w["preferred_skills"]) +
        ((tfidf_score * 100.0) * w["semantic_tfidf"]) +
        (experience_alignment * w["experience_alignment"])
    )
    overall_match = round(max(0.0, min(100.0, overall_match)), 1)

    # 7. Map evidence for matched skills
    evidence_map = {}
    for skill in list(matched_required) + list(matched_preferred):
        snippets = map_skill_evidence(skill, resume_text)
        if snippets:
            evidence_map[skill] = snippets[0]

    # 8. Check for keyword stuffing
    stuffing = detect_keyword_stuffing(resume_text, resume_skills)

    if overall_match >= 80:
        fit = "Strong Match"
        summary = "High alignment with required technical tools and job responsibilities."
    elif overall_match >= 60:
        fit = "Moderate Match"
        summary = "Good foundation with core requirements, but several target qualifications are missing."
    else:
        fit = "Low Match"
        summary = "Substantial gaps in required skills and terminology for this specific job posting."

    return {
        "has_job_description": True,
        "job_match_score": overall_match,
        "fit_level": fit,
        "summary": summary,
        "required_skills": {
            "matched": sorted(list(matched_required)),
            "missing": sorted(list(missing_required)),
            "total": len(req_jd_skills),
            "coverage_pct": round(req_ratio * 100, 1)
        },
        "preferred_skills": {
            "matched": sorted(list(matched_preferred)),
            "missing": sorted(list(missing_preferred)),
            "total": len(pref_jd_skills),
            "coverage_pct": round(pref_ratio * 100, 1)
        },
        "tfidf_score_pct": round(tfidf_score * 100, 1),
        "experience_alignment_pct": round(experience_alignment, 1),
        "top_keywords": top_keywords,
        "evidence_map": evidence_map,
        "keyword_stuffing_warnings": stuffing,
        "weights": {k: int(v * 100) for k, v in w.items()},
        "disclaimer": (
            "Disclaimer: Job Description Match measures vocabulary and skill overlap. "
            "It is a targeted preparation guide, not an automated hiring probability."
        )
    }
