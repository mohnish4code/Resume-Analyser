"""
Simple Job Description Analyzer.

Input:
    Plain-text job description

Output:
    - job title
    - required skills
    - preferred skills
    - responsibilities
    - experience
    - education

Also provides flat compatibility fields used by the ATS scorer.
"""

import re

from app.extractor import extract_skills


SECTION_HEADINGS = {
    "required": [
        "required skills",
        "required qualifications",
        "requirements",
        "must have",
        "mandatory skills",
        "mandatory requirements",
    ],
    "preferred": [
        "preferred skills",
        "preferred qualifications",
        "nice to have",
        "good to have",
        "desired skills",
        "bonus",
    ],
    "responsibilities": [
        "responsibilities",
        "key responsibilities",
        "job responsibilities",
        "what you'll do",
        "what you will do",
        "roles and responsibilities",
    ],
    "education": [
        "education",
        "educational qualifications",
        "qualification",
        "qualifications",
        "eligibility",
    ],
    "experience": [
        "experience",
        "work experience",
        "experience required",
    ],
}


EDUCATION_KEYWORDS = [
    "b.tech",
    "btech",
    "b.e",
    "be",
    "m.tech",
    "mtech",
    "m.e",
    "me",
    "mca",
    "msc",
    "m.sc",
    "bsc",
    "b.sc",
    "computer science",
    "information technology",
    "electronics",
    "data science",
    "artificial intelligence",
]


EDUCATION_LEVELS = {
    "btech": 3,
    "b.e": 3,
    "be": 3,
    "bsc": 3,
    "b.sc": 3,
    "mtech": 4,
    "m.tech": 4,
    "m.e": 4,
    "me": 4,
    "mca": 4,
    "msc": 4,
    "m.sc": 4,
}


DISPLAY_NAMES = {
    "b.tech": "BTech",
    "btech": "BTech",
    "b.e": "BE",
    "be": "BE",
    "m.tech": "MTech",
    "mtech": "MTech",
    "m.e": "ME",
    "me": "ME",
    "mca": "MCA",
    "msc": "MSc",
    "m.sc": "MSc",
    "bsc": "BSc",
    "b.sc": "BSc",
    "computer science": "Computer Science",
    "information technology": "Information Technology",
    "electronics": "Electronics",
    "data science": "Data Science",
    "artificial intelligence": "Artificial Intelligence",
}


def _clean_text(text: str) -> str:
    """Normalize JD whitespace."""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    lines = []

    for line in text.split("\n"):
        line = line.strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


def _find_section_heading(line: str):
    """Return the logical section name for a heading."""

    normalized = line.lower().strip()

    normalized = normalized.rstrip(":")
    normalized = re.sub(r"^[•●▪◦\-*]+\s*", "", normalized)

    for section, headings in SECTION_HEADINGS.items():
        for heading in headings:
            if normalized == heading:
                return section

    return None


def _extract_sections(text: str) -> dict:
    """Split JD into logical sections."""

    lines = _clean_text(text).split("\n")

    sections = {
        "required": [],
        "preferred": [],
        "responsibilities": [],
        "education": [],
        "experience": [],
        "other": [],
    }

    current_section = "other"

    for line in lines:

        heading = _find_section_heading(line)

        if heading:
            current_section = heading
            continue

        sections[current_section].append(line)

    return {
        key: "\n".join(value).strip()
        for key, value in sections.items()
    }


def _extract_experience(text: str) -> dict:
    """Extract minimum and maximum years of experience."""

    patterns = [
        r"(\d+)\s*\+\s*years?",
        r"(\d+)\s*-\s*(\d+)\s*years?",
        r"minimum\s+(\d+)\s*years?",
        r"at least\s+(\d+)\s*years?",
        r"(\d+)\s*years?\s+(?:of\s+)?experience",
    ]

    minimum = 0
    maximum = None

    for pattern in patterns:

        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            continue

        groups = match.groups()

        try:
            minimum = int(groups[0])
        except (ValueError, TypeError):
            continue

        if len(groups) > 1 and groups[1]:
            try:
                maximum = int(groups[1])
            except (ValueError, TypeError):
                maximum = None

        break

    return {
        "min_years": minimum,
        "max_years": maximum,
    }


def _extract_education(text: str) -> list:
    """Extract education requirements."""

    text_lower = text.lower()

    found = []

    for keyword in EDUCATION_KEYWORDS:

        pattern = (
            r"(?<![a-z])"
            + re.escape(keyword)
            + r"(?![a-z])"
        )

        if re.search(pattern, text_lower):

            value = DISPLAY_NAMES.get(keyword, keyword)

            if value not in found:
                found.append(value)

    return found


def _education_level(education: list) -> int:
    """Return highest detected education level."""

    level = 0

    for education_name in education:

        normalized = education_name.lower()

        for degree, degree_level in EDUCATION_LEVELS.items():

            if normalized == DISPLAY_NAMES.get(
                degree,
                degree
            ).lower():

                level = max(level, degree_level)

    return level


def _education_degree(education: list) -> str | None:
    """Return highest detected degree."""

    priority = [
        ("MTech", 4),
        ("ME", 4),
        ("MCA", 4),
        ("MSc", 4),
        ("BTech", 3),
        ("BE", 3),
        ("BSc", 3),
    ]

    for degree, _ in priority:

        if degree in education:
            return degree

    return None


def _extract_responsibilities(text: str) -> list:
    """Convert responsibility section into a clean list."""

    if not text:
        return []

    responsibilities = []

    for line in text.split("\n"):

        line = line.strip()

        if not line:
            continue

        line = re.sub(
            r"^[•●▪◦\-*]+\s*",
            "",
            line,
        )

        if line:
            responsibilities.append(line)

    return responsibilities


def _extract_title_from_text(text: str) -> str | None:
    """Try to extract a job title from the JD."""

    patterns = [
        r"looking for\s+(?:a|an)?\s*"
        r"([A-Za-z0-9/& -]+?)"
        r"(?:\s+who|\s+to|\.)",

        r"role\s*[:\-]\s*"
        r"([A-Za-z0-9/& -]+)",

        r"position\s*[:\-]\s*"
        r"([A-Za-z0-9/& -]+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            title = match.group(1).strip()

            if 2 <= len(title.split()) <= 8:
                return title

    return None


def analyze_job_description(
    text: str,
    job_title: str | None = None,
) -> dict:
    """
    Analyze a plain-text job description.
    """

    if not text or not text.strip():

        return {
            "job_title": job_title,
            "required_skills": [],
            "preferred_skills": [],
            "responsibilities": [],

            "experience": {
                "min_years": 0,
                "max_years": None,
            },

            "education": [],

            # Scorer compatibility
            "min_experience_years": 0,
            "min_education_level": 0,
            "min_education_degree": None,
        }

    clean_text = _clean_text(text)

    sections = _extract_sections(clean_text)

    # =========================================================
    # SKILLS
    # =========================================================

    required_skills = set()
    preferred_skills = set()

    if sections["required"]:
        required_skills = set(
            extract_skills(sections["required"])
        )

    if sections["preferred"]:
        preferred_skills = set(
            extract_skills(sections["preferred"])
        )

    # If there is no explicit Required Skills section,
    # extract skills from the complete JD.
    if not required_skills:

        all_skills = set(
            extract_skills(clean_text)
        )

        required_skills = (
            all_skills - preferred_skills
        )

    # Never allow the same skill in both lists.
    preferred_skills -= required_skills

    # =========================================================
    # RESPONSIBILITIES
    # =========================================================

    responsibilities = _extract_responsibilities(
        sections["responsibilities"]
    )

    # =========================================================
    # EXPERIENCE
    # =========================================================

    experience = _extract_experience(clean_text)

    # =========================================================
    # EDUCATION
    # =========================================================

    education = _extract_education(
        sections["education"]
    )

    # Fallback: inspect complete JD.
    if not education:

        education = _extract_education(
            clean_text
        )

    min_education_level = _education_level(
        education
    )

    min_education_degree = _education_degree(
        education
    )

    # =========================================================
    # JOB TITLE
    # =========================================================

    final_job_title = job_title

    if not final_job_title:

        final_job_title = _extract_title_from_text(
            clean_text
        )

    # =========================================================
    # FINAL RESPONSE
    # =========================================================

    return {
        "job_title": final_job_title,

        "required_skills": sorted(
            required_skills
        ),

        "preferred_skills": sorted(
            preferred_skills
        ),

        "responsibilities": responsibilities,

        "experience": experience,

        "education": education,

        # -----------------------------------------------------
        # Compatibility fields for scorer.py
        # -----------------------------------------------------

        "min_experience_years": experience[
            "min_years"
        ],

        "max_experience_years": experience[
            "max_years"
        ],

        "min_education_level": min_education_level,

        "min_education_degree": min_education_degree,
    }