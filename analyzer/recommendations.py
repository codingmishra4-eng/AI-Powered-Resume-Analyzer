"""
Resume Recommendations Module
-----------------------------
Generates deterministic, rule-based improvement suggestions based on
actual parsed resume data, section completeness, metric presence, and skill gaps.
Never hallucinates fake accomplishments or unverified experience.
"""

import re
from typing import Dict, List, Optional


# Strong action verbs recommended for high-impact resume bullet points
STRONG_ACTION_VERBS = {
    "architected", "accelerated", "automated", "built", "spearheaded", "designed",
    "deployed", "developed", "engineered", "implemented", "optimized", "orchestrated",
    "scaled", "streamlined", "mentored", "reduced", "increased", "generated"
}

# Passive or weak phrases to avoid in resume bullet points
WEAK_PHRASES = [
    "responsible for", "duties included", "helped with", "worked on",
    "assisted in", "participated in", "tasked with"
]


def check_quantifiable_metrics(text: str) -> Dict[str, any]:
    """
    Checks if the resume contains quantifiable achievements (numbers, percentages, metrics).
    """
    # Regex searching for percentages, metrics like 2M+, 10x, 35%, $50K, numbers with metrics
    metric_pattern = r"(?:\b\d+(?:\.\d+)?%|\$\d+(?:,\d+)*(?:\.\d+)?[kKmMbB]?|\b\d+\+?\s*(?:users|clients|requests|transactions|percent|ms|seconds|hours|x\b))"
    found_metrics = re.findall(metric_pattern, text, re.IGNORECASE)

    has_metrics = len(found_metrics) >= 3
    return {
        "has_metrics": has_metrics,
        "count": len(found_metrics),
        "examples": found_metrics[:5]
    }


def check_weak_phrasing(text: str) -> List[str]:
    """
    Identifies passive or weak phrases that weaken resume impact.
    """
    text_lower = text.lower()
    detected_weak = []
    for phrase in WEAK_PHRASES:
        if phrase in text_lower:
            detected_weak.append(phrase)
    return detected_weak


def generate_recommendations(
    resume_text: str,
    sections: Dict[str, str],
    contact_info: Dict[str, Optional[str]],
    skill_comparison: Dict[str, any]
) -> List[Dict[str, str]]:
    """
    Generates actionable, categorized suggestions tailored to the resume and target job.

    Categories:
    - High Priority (Skill Gaps, Missing Contact Info)
    - Content & Impact (Quantifiable metrics, Action verbs)
    - Structure & Completeness (Missing sections, Word count)
    - Professional Polish (Formatting, Tone)

    Returns:
        List of dicts: [{"category": str, "title": str, "advice": str, "priority": str}]
    """
    recommendations: List[Dict[str, str]] = []

    # 1. High Priority: Missing Target Skills
    missing_skills = skill_comparison.get("missing_skills", [])
    priorities = skill_comparison.get("suggested_priorities", [])
    if priorities:
        skills_str = ", ".join(priorities[:4])
        recommendations.append({
            "category": "Skill Alignment",
            "priority": "High",
            "title": "Address Key Missing Skills",
            "advice": (
                f"The job description highlights requirements in: {skills_str}. "
                "If you possess hands-on familiarity or academic coursework with any of these, "
                "ensure they are explicitly listed in your Skills section and referenced in project bullet points."
            )
        })

    # 2. Content & Impact: Quantifiable Metrics
    metrics_info = check_quantifiable_metrics(resume_text)
    if not metrics_info["has_metrics"]:
        recommendations.append({
            "category": "Impact & Outcomes",
            "priority": "High",
            "title": "Add Measurable Business Outcomes",
            "advice": (
                f"Only {metrics_info['count']} metric indicators were detected. "
                "Hiring managers look for tangible results. Frame bullet points using the "
                "X-Y-Z formula: 'Accomplished [X] as measured by [Y], by doing [Z]' "
                "(e.g., 'Reduced API query latency by 35% through Redis caching layers')."
            )
        })
    else:
        recommendations.append({
            "category": "Impact & Outcomes",
            "priority": "Low",
            "title": "Solid Use of Quantifiable Metrics",
            "advice": (
                f"Great job including measurable metrics ({metrics_info['count']} detected, e.g. "
                f"{', '.join(metrics_info['examples'][:3])}). Keep these prominent in your top roles."
            )
        })

    # 3. Phrasing & Action Verbs
    weak_found = check_weak_phrasing(resume_text)
    if weak_found:
        phrases_str = ", ".join([f"'{p}'" for p in weak_found[:3]])
        recommendations.append({
            "category": "Action Orientation",
            "priority": "Medium",
            "title": "Replace Passive Phrasing with Action Verbs",
            "advice": (
                f"Detected passive phrasing like {phrases_str}. Replace these with authoritative "
                "action verbs such as 'Architected', 'Implemented', 'Orchestrated', or 'Spearheaded' "
                "to convey proactive ownership."
            )
        })

    # 4. Structure & Section Completeness
    missing_sections = [name for name, content in sections.items() if content == "Not Detected"]
    if missing_sections:
        # Prioritize core missing sections
        essential_missing = [s for s in missing_sections if s in ["Experience", "Education", "Skills", "Projects"]]
        if essential_missing:
            recommendations.append({
                "category": "Resume Structure",
                "priority": "High",
                "title": f"Missing Core Section: {', '.join(essential_missing)}",
                "advice": (
                    f"The parser could not detect: {', '.join(essential_missing)}. "
                    "Ensure you use conventional headings like 'WORK EXPERIENCE', 'EDUCATION', "
                    "or 'TECHNICAL SKILLS' so Applicant Tracking Systems (ATS) can parse your resume reliably."
                )
            })

    # 5. Contact Information Checks
    missing_contacts = []
    if not contact_info.get("email"):
        missing_contacts.append("Email Address")
    if not contact_info.get("phone"):
        missing_contacts.append("Phone Number")
    if not contact_info.get("linkedin"):
        missing_contacts.append("LinkedIn Profile")
    if not contact_info.get("github"):
        missing_contacts.append("GitHub / Portfolio")

    if missing_contacts:
        recommendations.append({
            "category": "Contact Details",
            "priority": "Medium",
            "title": "Complete Header Contact Links",
            "advice": (
                f"Could not reliably detect: {', '.join(missing_contacts)}. "
                "For technical roles, recruiter reach-out improves significantly when clickable "
                "GitHub and LinkedIn profiles are placed in the header."
            )
        })

    # 6. Length and Depth Check
    word_count = len(resume_text.split())
    if word_count < 150:
        recommendations.append({
            "category": "Document Depth",
            "priority": "High",
            "title": "Expand Resume Detail",
            "advice": (
                f"Resume word count is low ({word_count} words). Elaborate on project architectures, "
                "responsibilities, technologies used, and challenges solved."
            )
        })
    elif word_count > 1100:
        recommendations.append({
            "category": "Document Depth",
            "priority": "Medium",
            "title": "Streamline Content for Conciseness",
            "advice": (
                f"Resume word count is high ({word_count} words). Aim for a tightly focused 1-2 page document "
                "(typically 400-800 words), pruning dated roles or redundant bullet points."
            )
        })

    return recommendations
