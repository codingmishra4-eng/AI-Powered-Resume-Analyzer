"""
Resume Quality Analyzer Module
------------------------------
Calculates an explainable Resume Quality Score (0-100) evaluating content
completeness, work experience achievements, quantified metrics, action verbs,
skills evidence, readability, and grammar consistency.
"""

import re
from typing import Dict, List, Set, Tuple
from config import RESUME_QUALITY_WEIGHTS


# Action verbs that demonstrate active ownership and technical execution
STRONG_ACTION_VERBS: Set[str] = {
    "accelerated", "accomplished", "achieved", "analyzed", "architected",
    "automated", "built", "centralized", "championed", "collaborated",
    "composed", "configured", "constructed", "created", "debugged",
    "decreased", "delivered", "deployed", "designed", "developed",
    "devised", "diagnosed", "directed", "documented", "drove",
    "engineered", "enhanced", "established", "executed", "expanded",
    "expedited", "formulated", "generated", "implemented", "improved",
    "increased", "initiated", "innovated", "installed", "integrated",
    "launched", "lead", "led", "managed", "maximized", "mentored",
    "migrated", "minimized", "modernized", "negotiated", "optimized",
    "orchestrated", "overhauled", "pioneered", "produced", "programmed",
    "reduced", "refactored", "resolved", "restructured", "revamped",
    "scaled", "spearheaded", "standardized", "streamlined", "strengthened",
    "transformed", "troubleshot", "upgraded"
}

# Weak, passive, or vague phrases that weaken resume impact
WEAK_PHRASES: List[str] = [
    "responsible for", "duties included", "helped with", "worked on",
    "assisted in", "participated in", "tasked with", "handled duties",
    "involved in", "tried to", "attempted to"
]

# Fluff buzzwords that recruiters view as filler without evidence
BUZZWORDS: List[str] = [
    "team player", "hard worker", "go-getter", "self-starter",
    "out of the box", "synergy", "ninja", "rockstar", "guru",
    "detail-oriented", "results-driven", "fast learner"
]


def audit_bullet_points(bullets: List[str]) -> Dict[str, any]:
    """
    Audits individual resume bullet points for action verbs, quantified metrics,
    weak phrasing, and length.
    """
    if not bullets:
        return {
            "total_bullets": 0,
            "metric_bullets": 0,
            "metric_ratio": 0.0,
            "action_verb_bullets": 0,
            "action_verb_ratio": 0.0,
            "weak_bullets": [],
            "metric_examples": [],
            "weak_examples": []
        }

    metric_pattern = r"(?:\b\d+(?:\.\d+)?%|\$\d+(?:,\d+)*(?:\.\d+)?[kKmMbB]?|\b\d+(?:\.\d+)?[kKmMbB]\b|\b\d+\+?\s*(?:[a-zA-Z]+\s+)?(?:users|clients|requests|transactions|percent|ms|seconds|hours|x\b|engineers|members|features))"

    metric_count = 0
    verb_count = 0
    weak_bullets = []
    metric_examples = []

    for b in bullets:
        clean = b.strip()
        if not clean:
            continue

        # Check for numbers/metrics
        metrics = re.findall(metric_pattern, clean, re.IGNORECASE)
        if metrics:
            metric_count += 1
            if len(metric_examples) < 5:
                metric_examples.append(clean)

        # Check for first word as strong action verb
        first_word = re.sub(r"[^a-zA-Z]", "", clean.split()[0]).lower() if clean.split() else ""
        if first_word in STRONG_ACTION_VERBS:
            verb_count += 1

        # Check for weak phrases
        clean_lower = clean.lower()
        for phrase in WEAK_PHRASES:
            if phrase in clean_lower:
                weak_bullets.append((clean, phrase))
                break

    total = len(bullets)
    return {
        "total_bullets": total,
        "metric_bullets": metric_count,
        "metric_ratio": round(metric_count / total, 2) if total > 0 else 0.0,
        "action_verb_bullets": verb_count,
        "action_verb_ratio": round(verb_count / total, 2) if total > 0 else 0.0,
        "weak_bullets": weak_bullets,
        "metric_examples": metric_examples,
        "weak_examples": [wb[0] for wb in weak_bullets[:4]]
    }


def analyze_resume_quality(
    raw_text: str,
    parsed_sections: Dict[str, str],
    structured_data: Dict[str, any],
    detected_skills: Set[str]
) -> Dict[str, any]:
    """
    Computes a transparent Resume Quality Score (0-100) and actionable
    prioritized findings.
    """
    findings: List[Dict[str, any]] = []

    # 1. Content Completeness (15% weight)
    completeness_score = 100.0
    missing_sections = [s for s, content in parsed_sections.items() if content == "Not Detected"]

    if "Experience" in missing_sections:
        completeness_score -= 40.0
        findings.append({
            "title": "Missing Work Experience Section",
            "priority": "High",
            "section": "Experience",
            "evidence": "Section Not Detected",
            "why_it_matters": "Work history is the primary criterion hiring managers and ATS screen for.",
            "recommendation": "Add a dedicated 'WORK EXPERIENCE' section detailing past roles, achievements, and dates."
        })

    if "Education" in missing_sections:
        completeness_score -= 20.0
        findings.append({
            "title": "Missing Education Section",
            "priority": "High",
            "section": "Education",
            "evidence": "Section Not Detected",
            "why_it_matters": "Most corporate positions have educational or equivalent accreditation requirements.",
            "recommendation": "Add an 'EDUCATION' section listing your degree, institution, and graduation year."
        })

    if "Skills" in missing_sections:
        completeness_score -= 25.0
        findings.append({
            "title": "Missing Skills Section",
            "priority": "High",
            "section": "Skills",
            "evidence": "Section Not Detected",
            "why_it_matters": "A distinct skills section enables both human recruiters and ATS keyword scanners to quickly index your technical stack.",
            "recommendation": "Create a clear 'TECHNICAL SKILLS' section categorized by Languages, Frameworks, and Tools."
        })

    if "Summary" in missing_sections:
        completeness_score -= 15.0
        findings.append({
            "title": "No Professional Summary Included",
            "priority": "Medium",
            "section": "Summary",
            "evidence": "Section Not Detected",
            "why_it_matters": "A concise 2-3 line summary sets the narrative for your career seniority and specializations.",
            "recommendation": "Add a 'PROFESSIONAL SUMMARY' highlighting your years of experience, core tech stack, and key accomplishments."
        })

    completeness_score = max(0.0, completeness_score)

    # 2. Work Experience & Achievements (25% weight)
    experience_score = 100.0
    all_bullets: List[str] = []
    for role in structured_data.get("experience", []):
        all_bullets.extend(role.get("bullets", []))

    bullet_audit = audit_bullet_points(all_bullets)

    # Metric check
    if bullet_audit["total_bullets"] > 0:
        if bullet_audit["metric_ratio"] < 0.25:
            experience_score -= 30.0
            findings.append({
                "title": "Low Quantifiable Impact (Needs Numbers)",
                "priority": "High",
                "section": "Experience",
                "evidence": f"Only {bullet_audit['metric_bullets']} of {bullet_audit['total_bullets']} bullet points ({int(bullet_audit['metric_ratio']*100)}%) contain quantifiable metrics.",
                "why_it_matters": "Resumes with quantified outcomes receive 40% higher recruiter callback rates because numbers prove scale and business impact.",
                "recommendation": "Use the Google formula: 'Accomplished [X] by doing [Z] as measured by [Y]' (e.g. 'Improved query latency by 35%' or 'Managed 2M+ daily requests')."
            })
        else:
            findings.append({
                "title": "Excellent Quantifiable Metrics",
                "priority": "Low",
                "section": "Experience",
                "evidence": f"{bullet_audit['metric_bullets']} bullets contain concrete numbers or percentages.",
                "why_it_matters": "Measurable numbers establish credibility and real-world impact.",
                "recommendation": "Continue using numbers to substantiate your career highlights."
            })

        # Action verbs check
        if bullet_audit["action_verb_ratio"] < 0.60:
            experience_score -= 20.0
            findings.append({
                "title": "Strengthen Bullet Point Action Verbs",
                "priority": "Medium",
                "section": "Experience",
                "evidence": f"Only {int(bullet_audit['action_verb_ratio']*100)}% of bullets begin with strong action verbs.",
                "why_it_matters": "Starting bullets with powerful verbs ('Architected', 'Spearheaded', 'Engineered') demonstrates proactive ownership.",
                "recommendation": "Begin each bullet with a distinct past-tense action verb instead of passive descriptions."
            })

        # Weak phrasing check
        if bullet_audit["weak_bullets"]:
            experience_score -= 15.0
            examples = [f"'{wb[1]}'" for wb in bullet_audit["weak_bullets"][:3]]
            findings.append({
                "title": f"Passive Phrases Detected ({', '.join(examples)})",
                "priority": "Medium",
                "section": "Experience",
                "evidence": f"Found in {len(bullet_audit['weak_bullets'])} bullet point(s).",
                "why_it_matters": "Phrases like 'responsible for' sound like job duty lists rather than active personal achievements.",
                "recommendation": "Replace 'Responsible for X' with 'Engineered X' or 'Led X'."
            })
    else:
        experience_score = 15.0

    experience_score = max(0.0, experience_score)

    # 3. Skills & Evidence (20% weight)
    skills_score = 100.0
    if len(detected_skills) <= 1:
        skills_score = 20.0
        findings.append({
            "title": "Sparse Skill Catalog",
            "priority": "High",
            "section": "Skills",
            "evidence": f"Only {len(detected_skills)} recognized skill(s) detected.",
            "why_it_matters": "ATS algorithms match resumes against job descriptions based on recognized skill keywords.",
            "recommendation": "Explicitly list your programming languages, frameworks, cloud services, and databases."
        })
    elif len(detected_skills) < 5:
        skills_score -= 30.0
        findings.append({
            "title": "Sparse Skill Catalog",
            "priority": "High",
            "section": "Skills",
            "evidence": f"Only {len(detected_skills)} recognized technical skills detected.",
            "why_it_matters": "ATS algorithms match resumes against job descriptions based on recognized skill keywords.",
            "recommendation": "Explicitly list your programming languages, frameworks, cloud services, and databases."
        })
    elif len(detected_skills) > 35:
        skills_score -= 15.0
        findings.append({
            "title": "Possible Skill Stuffing / Overcrowding",
            "priority": "Medium",
            "section": "Skills",
            "evidence": f"{len(detected_skills)} skills listed. Excessively long skill lists can appear diluted.",
            "why_it_matters": "Recruiters prefer a focused, highly relevant set of competencies over a generic kitchen-sink list.",
            "recommendation": "Group skills into Core (proficient) vs Familiar, and remove tools you haven't used recently."
        })

    # Check if skills appear in experience bullets (demonstrated evidence)
    skills_in_bullets = 0
    bullets_text = " ".join(all_bullets).lower()
    for s in detected_skills:
        if s.lower() in bullets_text:
            skills_in_bullets += 1

    evidence_ratio = (skills_in_bullets / len(detected_skills)) if detected_skills else 0.0
    if evidence_ratio < 0.25 and len(detected_skills) >= 6:
        skills_score -= 20.0
        findings.append({
            "title": "Skills Listed Without Contextual Evidence",
            "priority": "Medium",
            "section": "Experience",
            "evidence": f"Only {skills_in_bullets} of {len(detected_skills)} skills ({int(evidence_ratio*100)}%) appear inside project or work experience descriptions.",
            "why_it_matters": "Recruiters discount skills that appear solely in a keyword list without proof of usage in a project.",
            "recommendation": "Weave your top skills into your experience bullet points showing how you applied them."
        })

    skills_score = max(0.0, skills_score)

    # 4. Professional Summary & Clarity (15% weight)
    summary_score = 100.0
    summary_text = parsed_sections.get("Summary", "")

    if summary_text and summary_text != "Not Detected":
        summary_words = len(summary_text.split())
        if summary_words < 15:
            summary_score -= 25.0
            findings.append({
                "title": "Summary is Too Brief",
                "priority": "Low",
                "section": "Summary",
                "evidence": f"Summary is {summary_words} words.",
                "why_it_matters": "A 1-sentence summary fails to establish your career trajectory and domain depth.",
                "recommendation": "Aim for 3-4 impactful sentences (40-80 words) summarizing years of experience, core stack, and standout achievements."
            })
        elif summary_words > 140:
            summary_score -= 20.0
            findings.append({
                "title": "Summary is Overly Verbose",
                "priority": "Medium",
                "section": "Summary",
                "evidence": f"Summary is {summary_words} words.",
                "why_it_matters": "Recruiters spend 6-8 seconds on initial review. Long summaries get skipped.",
                "recommendation": "Condense your summary to 3-4 concise, high-impact sentences."
            })

        # Check for first-person pronouns
        pronouns_found = re.findall(r"\b(I|me|my|mine|myself)\b", summary_text, re.IGNORECASE)
        if pronouns_found:
            summary_score -= 15.0
            findings.append({
                "title": "First-Person Pronouns in Summary",
                "priority": "Low",
                "section": "Summary",
                "evidence": f"Detected: {', '.join(set(pronouns_found))}",
                "why_it_matters": "Standard professional resume style uses implied first-person without explicit 'I' or 'my'.",
                "recommendation": "Rewrite sentences in implied third person (e.g. 'Senior Software Engineer with 5+ years...' instead of 'I am a senior engineer...')."
            })

        # Check for buzzwords
        found_buzz = [bw for bw in BUZZWORDS if bw in summary_text.lower()]
        if found_buzz:
            summary_score -= 15.0
            findings.append({
                "title": f"Generic Buzzwords Detected ({', '.join(found_buzz)})",
                "priority": "Low",
                "section": "Summary",
                "evidence": f"Found: {', '.join(found_buzz)}",
                "why_it_matters": "Cliche phrases like 'hard worker' or 'team player' add zero informational value.",
                "recommendation": "Replace buzzwords with concrete examples of collaboration and technical achievements."
            })
    else:
        summary_score = 40.0

    summary_score = max(0.0, summary_score)

    # 5. Grammar & Readability (10% weight)
    grammar_score = 100.0

    # Repeated consecutive words (e.g., 'the the', 'and and')
    repeated_words = re.findall(r"\b([a-zA-Z]+)\s+\1\b", raw_text, re.IGNORECASE)
    if repeated_words:
        grammar_score -= 20.0
        findings.append({
            "title": f"Repeated Consecutive Words ({', '.join(set(repeated_words)[:3])})",
            "priority": "Medium",
            "section": "Content",
            "evidence": f"Duplicate word tokens: {', '.join(set(repeated_words))}",
            "why_it_matters": "Accidental duplicate words indicate lack of careful proofreading.",
            "recommendation": "Carefully remove accidental repeated words."
        })

    # Sentence length / readability
    sentences = re.split(r"[.!?]\s+", raw_text)
    long_sentences = [s for s in sentences if len(s.split()) > 35]
    if len(long_sentences) >= 3:
        grammar_score -= 15.0
        findings.append({
            "title": "Overly Long / Run-on Sentences",
            "priority": "Low",
            "section": "Readability",
            "evidence": f"Found {len(long_sentences)} sentences exceeding 35 words.",
            "why_it_matters": "Long run-on sentences decrease readability on mobile devices and fast recruiter scans.",
            "recommendation": "Break complex compound sentences into punchy, distinct bullet points."
        })

    grammar_score = max(0.0, grammar_score)

    # 6. Structure & Formatting (15% weight)
    structure_score = 100.0
    words_count = len(raw_text.split())

    if words_count < 50:
        structure_score = 30.0
    elif words_count < 100:
        structure_score -= 30.0
    elif words_count < 180:
        structure_score -= 15.0
    elif words_count > 1100:
        structure_score -= 15.0

    # Check bullet consistency (do bullets consistently end with a period or not)
    if all_bullets:
        end_with_period = sum(1 for b in all_bullets if b.strip().endswith("."))
        period_ratio = end_with_period / len(all_bullets)
        if 0.20 < period_ratio < 0.80:
            structure_score -= 10.0
            findings.append({
                "title": "Inconsistent Bullet Point Punctuation",
                "priority": "Low",
                "section": "Formatting",
                "evidence": f"{int(period_ratio*100)}% of bullets end with periods; the rest do not.",
                "why_it_matters": "Consistency in punctuation reflects attention to detail.",
                "recommendation": "Adopt a single punctuation convention: either end all bullets with a period or none of them."
            })

    structure_score = max(0.0, structure_score)

    # -------------------------------------------------------------------------
    # Composite Quality Score Calculation
    # -------------------------------------------------------------------------
    w = RESUME_QUALITY_WEIGHTS
    overall_quality = (
        (completeness_score * w["content_completeness"]) +
        (experience_score * w["work_experience_achievements"]) +
        (skills_score * w["skills_and_evidence"]) +
        (summary_score * w["summary_and_clarity"]) +
        (grammar_score * w["grammar_and_readability"]) +
        (structure_score * w["structure_and_formatting"])
    )
    overall_quality = round(max(0.0, min(100.0, overall_quality)), 1)

    # Sort findings by priority: High -> Medium -> Low
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    findings.sort(key=lambda item: priority_order.get(item.get("priority", "Low"), 3))

    if overall_quality >= 80:
        rating = "Strong Resume"
        summary_msg = "Outstanding resume quality with strong action verbs, quantifiable metrics, and well-structured sections."
    elif overall_quality >= 60:
        rating = "Good Foundation (Optimization Needed)"
        summary_msg = "Solid core experience, but improving quantifiable achievements and eliminating passive phrasing will significantly boost results."
    else:
        rating = "Needs Substantial Improvement"
        summary_msg = "Several core sections, metrics, or structural components require attention to pass competitive screening."

    return {
        "quality_score": overall_quality,
        "rating": rating,
        "summary": summary_msg,
        "breakdown": {
            "content_completeness": round(completeness_score, 1),
            "work_experience_achievements": round(experience_score, 1),
            "skills_and_evidence": round(skills_score, 1),
            "summary_and_clarity": round(summary_score, 1),
            "grammar_and_readability": round(grammar_score, 1),
            "structure_and_formatting": round(structure_score, 1)
        },
        "weights": {k: int(v * 100) for k, v in w.items()},
        "bullet_audit": bullet_audit,
        "findings": findings,
        "high_priority_count": sum(1 for f in findings if f["priority"] == "High"),
        "total_issues_count": len([f for f in findings if f["priority"] in ["High", "Medium"]])
    }
