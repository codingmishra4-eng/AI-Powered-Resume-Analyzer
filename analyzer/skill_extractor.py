"""
Skill Extractor Module
----------------------
Extracts, categorizes, and compares technical and soft skills from text
using a configurable taxonomy dictionary and robust pattern matching.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from config import SKILLS_FILE

# Default built-in taxonomy fallback in case skills_data.json is not present
FALLBACK_TAXONOMY: Dict[str, List[str]] = {
    "Programming Languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "C", "Go",
        "Rust", "Ruby", "PHP", "Swift", "Kotlin", "SQL", "HTML", "CSS", "Bash"
    ],
    "Frameworks & Libraries": [
        "Django", "Flask", "FastAPI", "React", "Angular", "Vue", "Node.js",
        "Express", "Spring Boot", "Next.js", "Tailwind CSS", "Bootstrap",
        "Streamlit", "REST API", "GraphQL"
    ],
    "Databases & Storage": [
        "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Elasticsearch"
    ],
    "Cloud & DevOps": [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI/CD", "Jenkins",
        "GitHub Actions", "Terraform", "Linux", "Git"
    ],
    "AI & Data Science": [
        "Machine Learning", "Deep Learning", "NLP", "Pandas", "NumPy",
        "Scikit-Learn", "TensorFlow", "PyTorch"
    ],
    "Engineering Practices": [
        "Agile", "Scrum", "Unit Testing", "Microservices", "System Design", "Code Review"
    ],
    "Soft Skills": [
        "Problem Solving", "Communication", "Team Collaboration", "Leadership"
    ]
}


class SkillExtractor:
    """
    SkillExtractor parses documents against a categorized skill taxonomy.
    Features:
    - Case-insensitive regex matching with word boundary protections
    - Preservation of multi-word skills (e.g. 'Machine Learning', 'REST API')
    - Configurable custom taxonomy loading and updating
    """

    def __init__(self, taxonomy_path: Path = SKILLS_FILE):
        self.taxonomy_path = taxonomy_path
        self.taxonomy: Dict[str, List[str]] = self._load_taxonomy()
        self._compiled_patterns = self._compile_skill_patterns()

    def _load_taxonomy(self) -> Dict[str, List[str]]:
        """Loads skill taxonomy from JSON file or falls back to built-in dictionary."""
        if os.path.exists(self.taxonomy_path):
            try:
                with open(self.taxonomy_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and data:
                        return data
            except Exception:
                pass
        return FALLBACK_TAXONOMY

    def _compile_skill_patterns(self) -> Dict[str, Tuple[re.Pattern, str]]:
        """
        Compiles regex patterns for each canonical skill name.
        Uses boundaries appropriate for both standard words and symbols like C++ / C# / .NET.
        """
        compiled = {}
        for category, skills in self.taxonomy.items():
            for skill in skills:
                escaped = re.escape(skill)
                # If skill ends with non-word symbol like ++ or #, standard \b boundary won't match at end
                if skill.endswith("++") or skill.endswith("#"):
                    pattern = rf"(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])"
                else:
                    pattern = rf"\b{escaped}\b"
                
                regex = re.compile(pattern, re.IGNORECASE)
                compiled[skill] = (regex, category)
        return compiled

    def add_custom_skill(self, skill_name: str, category: str = "Custom Skills") -> bool:
        """
        Adds a new skill to the taxonomy dynamically.

        Parameters:
            skill_name (str): The name of the skill.
            category (str): The category name.

        Returns:
            bool: True if added, False if already exists.
        """
        clean_name = skill_name.strip()
        if not clean_name:
            return False

        if category not in self.taxonomy:
            self.taxonomy[category] = []

        # Check if already present (case-insensitive)
        existing = [s.lower() for s in self.taxonomy[category]]
        if clean_name.lower() in existing:
            return False

        self.taxonomy[category].append(clean_name)
        # Recompile patterns
        self._compiled_patterns = self._compile_skill_patterns()
        return True

    def extract_skills(self, text: str) -> Dict[str, any]:
        """
        Extracts all recognized skills from the given text.

        Parameters:
            text (str): Resume or Job Description text.

        Returns:
            Dict containing:
            - 'all_skills': Set of matched skill canonical names
            - 'by_category': Dict mapping category -> list of matched skills
            - 'total_count': Total unique skills identified
        """
        if not text:
            return {
                "all_skills": set(),
                "by_category": {},
                "total_count": 0
            }

        found_skills: Set[str] = set()
        by_category: Dict[str, List[str]] = {}

        for skill, (regex, category) in self._compiled_patterns.items():
            if regex.search(text):
                found_skills.add(skill)
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(skill)

        # Sort skills within each category alphabetically
        for cat in by_category:
            by_category[cat].sort()

        return {
            "all_skills": found_skills,
            "by_category": by_category,
            "total_count": len(found_skills)
        }

    def compare_skills(self, resume_skills: Set[str], job_skills: Set[str]) -> Dict[str, any]:
        """
        Performs skill gap analysis comparing candidate's resume skills
        against the job description's requested skills.

        Parameters:
            resume_skills (Set[str]): Skills extracted from resume.
            job_skills (Set[str]): Skills extracted from job description.

        Returns:
            Dict containing:
            - 'matched_skills': Skills found in both
            - 'missing_skills': Skills required in JD but missing in resume
            - 'additional_skills': Skills in resume not requested in JD
            - 'overlap_ratio': Float between 0.0 and 1.0 (or percentage 0-100)
            - 'suggested_priorities': Ordered list of critical missing skills
        """
        matched = sorted(list(resume_skills.intersection(job_skills)))
        missing = sorted(list(job_skills.difference(resume_skills)))
        additional = sorted(list(resume_skills.difference(job_skills)))

        total_required = len(job_skills)
        if total_required > 0:
            overlap_ratio = len(matched) / total_required
            overlap_percentage = round(overlap_ratio * 100, 1)
        else:
            # If job description mentions no specific catalog skills, neutral overlap
            overlap_ratio = 1.0 if len(resume_skills) > 0 else 0.0
            overlap_percentage = 100.0 if len(resume_skills) > 0 else 0.0

        # Suggested learning priorities:
        # Prioritize missing technical skills (Programming Languages, Databases, Cloud/DevOps)
        # over generic soft skills
        priority_categories = [
            "Programming Languages",
            "Databases & Data Storage",
            "Cloud & DevOps",
            "Web Frameworks & Libraries",
            "AI & Data Science"
        ]

        prioritized_missing = []
        for cat in priority_categories:
            cat_skills = self.taxonomy.get(cat, [])
            for skill in missing:
                if skill in cat_skills and skill not in prioritized_missing:
                    prioritized_missing.append(skill)

        # Add remaining missing skills
        for skill in missing:
            if skill not in prioritized_missing:
                prioritized_missing.append(skill)

        return {
            "matched_skills": matched,
            "missing_skills": missing,
            "additional_skills": additional,
            "matched_count": len(matched),
            "missing_count": len(missing),
            "total_required": total_required,
            "overlap_ratio": overlap_ratio,
            "overlap_percentage": overlap_percentage,
            "suggested_priorities": prioritized_missing[:6]  # Top recommendations
        }
