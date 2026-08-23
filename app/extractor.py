"""
Resume information extraction.

Responsibilities:
- Detect resume sections
- Extract contact information
- Extract technical skills
- Extract education
- Extract work experience
- Extract projects
- Extract research publications
- Extract certifications
- Extract achievements

The extractor is intentionally deterministic and offline-friendly.
"""

import re
from rapidfuzz import fuzz

from app.skills_db import (
    ALL_SKILLS,
    SKILL_ALIASES,
    EDUCATION_LEVELS,
    DEGREE_FIELDS,
)


# ============================================================
# SECTION HEADERS
# ============================================================

SECTION_HEADERS = {
    "professional_summary": [
        "professional summary",
        "profile summary",
        "career summary",
        "summary",
        "objective",
        "career objective",
        "profile",
    ],

    "skills": [
        "skills",
        "technical skills",
        "technical skill",
        "core skills",
        "core competencies",
        "key skills",
        "technologies",
        "technical expertise",
    ],

    "education": [
        "education",
        "educational background",
        "academic background",
        "academic qualifications",
        "qualifications",
    ],

    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "professional employment",
    ],

    "projects": [
        "projects",
        "academic projects",
        "personal projects",
        "technical projects",
        "key projects",
    ],

    "research_publication": [
        "research publication",
        "research publications",
        "publications",
        "publication",
        "research",
        "papers",
        "research papers",
    ],

    "certifications": [
        "certifications",
        "certification",
        "certificates",
        "licenses",
    ],

    "achievements": [
        "achievements",
        "achievement",
        "awards",
        "honors",
        "accomplishments",
    ],
}


# ============================================================
# REGEX
# ============================================================

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?"
    r"\(?\d{3,4}\)?[-.\s]?"
    r"\d{3,4}[-.\s]?"
    r"\d{3,4}"
)

LINKEDIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_/]+",
    re.I,
)

GITHUB_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-_/]+",
    re.I,
)

YEAR_RANGE_RE = re.compile(
    r"\b(19\d{2}|20\d{2})\s*"
    r"(?:-|–|—|to)\s*"
    r"(19\d{2}|20\d{2}|present|current|now)\b",
    re.I,
)

YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_line(line: str) -> str:
    """
    Normalize a line so section-header detection is reliable.
    """
    line = line.strip()

    # Remove markdown-style bullets
    line = re.sub(r"^[•●▪◦*-]\s*", "", line)

    # Remove trailing colon
    line = line.rstrip(":")

    # Normalize whitespace
    line = re.sub(r"\s+", " ", line)

    return line.strip()


def normalize_section_name(line: str) -> str:
    """
    Normalize a possible section heading.
    """
    line = normalize_line(line).lower()

    # Remove common punctuation
    line = re.sub(r"[|]+", " ", line)
    line = re.sub(r"\s+", " ", line)

    return line.strip()


# ============================================================
# SECTION DETECTION
# ============================================================

def detect_section_header(line: str) -> str | None:
    """
    Return the internal section name if a line is a recognized
    section heading.
    """

    normalized = normalize_section_name(line)

    if not normalized:
        return None

    # Exact matching is preferred.
    for section, aliases in SECTION_HEADERS.items():
        for alias in aliases:
            if normalized == alias.lower():
                return section

    return None


def split_into_sections(text: str) -> dict:
    """
    Split resume text into logical sections.

    Important:
    A section ends as soon as another recognized section header
    appears. This prevents Projects from consuming Research
    Publication, Certifications, etc.
    """

    lines = text.splitlines()

    sections = {
        "header": []
    }

    current_section = "header"

    for line in lines:
        cleaned = line.strip()

        if not cleaned:
            continue

        detected = detect_section_header(cleaned)

        if detected:
            current_section = detected
            sections.setdefault(current_section, [])
            continue

        sections.setdefault(current_section, [])
        sections[current_section].append(cleaned)

    # Convert lists to strings
    result = {}

    for section, lines_list in sections.items():
        content = "\n".join(lines_list).strip()

        if content:
            result[section] = content

    return result


# ============================================================
# CONTACT INFORMATION
# ============================================================

def extract_contact_info(text: str) -> dict:
    """
    Extract name, email, phone, LinkedIn and GitHub.
    """

    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)
    linkedin_match = LINKEDIN_RE.search(text)
    github_match = GITHUB_RE.search(text)

    name = None

    # Usually the candidate name is in the first few lines.
    for line in text.splitlines()[:8]:

        candidate = line.strip()

        if not candidate:
            continue

        if EMAIL_RE.search(candidate):
            continue

        if PHONE_RE.search(candidate):
            continue

        if "linkedin.com" in candidate.lower():
            continue

        if "github.com" in candidate.lower():
            continue

        # Avoid treating headings as names.
        if detect_section_header(candidate):
            continue

        words = candidate.split()

        if 2 <= len(words) <= 5:

            valid_name = True

            for word in words:
                cleaned = re.sub(r"[^A-Za-z'-]", "", word)

                if not cleaned:
                    continue

                if not cleaned[0].isupper():
                    valid_name = False
                    break

            if valid_name:
                name = candidate
                break

    return {
        "name": name,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "linkedin": linkedin_match.group(0) if linkedin_match else None,
        "github": github_match.group(0) if github_match else None,
    }


# ============================================================
# SKILL NORMALIZATION
# ============================================================

def normalize_skill(token: str) -> str:
    """
    Convert aliases into canonical skill names.
    """

    token = token.lower().strip()

    return SKILL_ALIASES.get(token, token)


def _clean_skill_text(text: str) -> str:
    """
    Normalize text for skill matching while preserving:
    +, #, ., -, / characters useful in technology names.
    """

    text = text.lower()

    text = text.replace("–", "-")
    text = text.replace("—", "-")

    text = re.sub(r"[^\w+#./ -]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text


def extract_skills(text: str, fuzzy_threshold: int = 88) -> list:
    """
    Extract skills from the supplied text.

    Uses:
    1. Exact canonical skill matching
    2. Alias matching
    3. Light fuzzy matching

    This function is also used by jd_analyzer.py, so it must remain
    generic and accept arbitrary text.
    """

    normalized_text = _clean_skill_text(text)

    found = set()

    # --------------------------------------------------------
    # Exact canonical skill matching
    # --------------------------------------------------------

    for skill in ALL_SKILLS:

        skill_normalized = _clean_skill_text(skill)

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(skill_normalized)
            + r"(?![a-z0-9])"
        )

        if re.search(pattern, normalized_text):
            canonical = SKILL_ALIASES.get(skill, skill)
            found.add(canonical)

    # --------------------------------------------------------
    # Alias matching
    # --------------------------------------------------------

    for alias, canonical in SKILL_ALIASES.items():

        alias_normalized = _clean_skill_text(alias)

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(alias_normalized)
            + r"(?![a-z0-9])"
        )

        if re.search(pattern, normalized_text):
            found.add(canonical)

    # --------------------------------------------------------
    # Fuzzy matching
    #
    # Only apply to relatively short chunks so entire sentences
    # are never accidentally classified as skills.
    # --------------------------------------------------------

    chunks = re.split(r"[,;\n•|/]", normalized_text)

    for chunk in chunks:

        chunk = chunk.strip()

        if not chunk:
            continue

        if len(chunk) > 50:
            continue

        for skill in ALL_SKILLS:

            canonical = SKILL_ALIASES.get(skill, skill)

            if canonical in found:
                continue

            score = fuzz.ratio(chunk, _clean_skill_text(skill))

            if score >= fuzzy_threshold:
                found.add(canonical)

    return sorted(found)


# ============================================================
# EDUCATION
# ============================================================

def _extract_year_range(text: str):
    """
    Extract start/end years from a local education block.
    """

    match = YEAR_RANGE_RE.search(text)

    if not match:
        return None, None

    start_year = int(match.group(1))

    end_raw = match.group(2).lower()

    if end_raw in {"present", "current", "now"}:
        end_year = None
    else:
        end_year = int(end_raw)

    return start_year, end_year


def _find_education_field(window: str) -> str | None:
    """
    Find the most specific education field.

    Longer phrases are checked first so:
    'electronics & computer engineering'
    is preferred over just:
    'electronics'
    """

    normalized = window.lower()

    normalized = normalized.replace("&", "and")

    # Longest fields first.
    fields = sorted(
        DEGREE_FIELDS,
        key=len,
        reverse=True,
    )

    for field in fields:

        field_normalized = field.lower().replace("&", "and")

        if field_normalized in normalized:
            return field

    # Special handling for the common resume spelling.
    if (
        "electronics" in normalized
        and "computer engineering" in normalized
    ):
        return "electronics & computer engineering"

    return None


def extract_education(text: str) -> list:
    """
    Extract education entries.

    Returns:
    - degree
    - level
    - field
    - start_year
    - end_year
    - cgpa when available
    """

    results = []

    # Search primarily in the education section if present.
    sections = split_into_sections(text)

    education_text = sections.get("education", text)

    lower_text = education_text.lower()

    for degree, level in EDUCATION_LEVELS.items():

        pattern = (
            r"(?<![a-z])"
            + re.escape(degree.lower())
            + r"(?![a-z])"
        )

        for match in re.finditer(pattern, lower_text):

            start = max(0, match.start() - 120)
            end = min(len(education_text), match.end() + 180)

            window = education_text[start:end]

            field = _find_education_field(window)

            start_year, end_year = _extract_year_range(window)

            if not start_year:

                years = [
                    int(y)
                    for y in YEAR_RE.findall(window)
                ]

                if years:
                    start_year = years[0]

                    if len(years) > 1:
                        end_year = years[1]

            cgpa = None

            cgpa_match = re.search(
                r"(?:cgpa|gpa)\s*[:\-]?\s*"
                r"(\d+(?:\.\d+)?)",
                window,
                re.I,
            )

            if cgpa_match:
                cgpa = float(cgpa_match.group(1))

            results.append(
                {
                    "degree": degree,
                    "level": level,
                    "field": field,
                    "start_year": start_year,
                    "end_year": end_year,
                    "cgpa": cgpa,
                }
            )

    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    deduplicated = {}

    for item in results:

        key = (
            item["degree"],
            item.get("field"),
        )

        if key not in deduplicated:
            deduplicated[key] = item

    return sorted(
        deduplicated.values(),
        key=lambda x: -x["level"],
    )


# ============================================================
# EXPERIENCE
# ============================================================

def _calculate_year_ranges(text: str) -> float:
    """
    Calculate total duration from year ranges in an actual
    experience section.
    """

    spans = []

    for match in YEAR_RANGE_RE.finditer(text):

        start = int(match.group(1))

        end_raw = match.group(2).lower()

        if end_raw in {"present", "current", "now"}:
            # Use a conservative current-year calculation.
            from datetime import datetime
            end = datetime.now().year
        else:
            end = int(end_raw)

        if end >= start:
            spans.append((start, end))

    if not spans:
        return 0.0

    # Merge overlapping periods.
    spans.sort()

    merged = [spans[0]]

    for start, end in spans[1:]:

        previous_start, previous_end = merged[-1]

        if start <= previous_end:
            merged[-1] = (
                previous_start,
                max(previous_end, end),
            )
        else:
            merged.append((start, end))

    total = sum(
        end - start
        for start, end in merged
    )

    return float(total)


def extract_experience_entries(sections: dict) -> list:
    """
    Extract actual experience entries from the experience section.

    If there is no Experience section, return an empty list.
    """

    block = sections.get("experience", "")

    if not block:
        return []

    lines = [
        line.strip()
        for line in block.splitlines()
        if line.strip()
    ]

    return lines


def estimate_experience_years(text: str, sections: dict | None = None) -> float:
    """
    Estimate professional experience.

    IMPORTANT:
    Education/project dates are never used.

    If a dedicated Experience section exists, only that section
    is considered.

    If no Experience section exists, explicit phrases such as
    '2 years of experience' may be used from the complete text.
    """

    if sections is not None:

        experience_block = sections.get("experience", "")

        if experience_block:

            range_years = _calculate_year_ranges(
                experience_block
            )

            if range_years > 0:
                return range_years

            explicit = re.search(
                r"(\d+(?:\.\d+)?)\+?\s*years?\s+"
                r"(?:of\s+)?experience",
                experience_block,
                re.I,
            )

            if explicit:
                return float(explicit.group(1))

            return 0.0

    # No experience section.
    # Only accept explicit experience claims.
    explicit = re.search(
        r"(\d+(?:\.\d+)?)\+?\s*years?\s+"
        r"(?:of\s+)?experience",
        text,
        re.I,
    )

    if explicit:
        return float(explicit.group(1))

    return 0.0


# ============================================================
# PROJECTS
# ============================================================

def _looks_like_project_heading(line: str) -> bool:
    """
    Detect project heading lines.

    Typical format:
    GitHub AI Repository Analyzer | Python, FastAPI, React
    Netflix Customer Churn Prediction | Python, TensorFlow
    """

    line = line.strip()

    if not line:
        return False

    # Project headings generally contain "|".
    if "|" in line:
        return True

    return False


def extract_projects(sections: dict) -> list:
    """
    Extract project entries only from the Projects section.

    Research Publication, Certifications, etc. are already separated
    by split_into_sections(), so they cannot leak into this list.
    """

    block = sections.get("projects", "")

    if not block:
        return []

    lines = [
        line.strip()
        for line in block.splitlines()
        if line.strip()
    ]

    projects = []
    current_project = []

    for line in lines:

        if _looks_like_project_heading(line):

            if current_project:
                projects.append(
                    "\n".join(current_project).strip()
                )

            current_project = [line]

        else:

            if current_project:
                current_project.append(line)

            else:
                # If a PDF parser breaks the heading formatting,
                # keep the text rather than losing it.
                current_project = [line]

    if current_project:
        projects.append(
            "\n".join(current_project).strip()
        )

    return projects


# ============================================================
# RESEARCH PUBLICATIONS
# ============================================================

def extract_research_publications(sections: dict) -> list:
    """
    Extract research/publication entries.
    """

    block = sections.get("research_publication", "")

    if not block:
        return []

    lines = [
        line.strip()
        for line in block.splitlines()
        if line.strip()
    ]

    if not lines:
        return []

    # Keep the publication as a structured text block.
    return [
        "\n".join(lines)
    ]


# ============================================================
# PROFESSIONAL SUMMARY
# ============================================================

def extract_professional_summary(sections: dict) -> str | None:
    """
    Extract the professional summary.
    """

    summary = sections.get("professional_summary", "")

    if not summary:
        return None

    return summary.strip()


# ============================================================
# CERTIFICATIONS
# ============================================================

def extract_certifications(sections: dict) -> list:

    block = sections.get("certifications", "")

    if not block:
        return []

    lines = []

    for line in block.splitlines():

        cleaned = line.strip("•●▪◦- \t")

        if cleaned:
            lines.append(cleaned)

    return lines


# ============================================================
# ACHIEVEMENTS
# ============================================================

def extract_achievements(sections: dict) -> list:

    block = sections.get("achievements", "")

    if not block:
        return []

    lines = []

    for line in block.splitlines():

        cleaned = line.strip("•●▪◦- \t")

        if cleaned:
            lines.append(cleaned)

    return lines


# ============================================================
# MAIN RESUME PROFILE
# ============================================================

def extract_resume_profile(text: str) -> dict:
    """
    Main extraction pipeline.
    """

    sections = split_into_sections(text)

    contact = extract_contact_info(text)

    # --------------------------------------------------------
    # Skills
    #
    # Scan the entire resume because technologies can appear
    # inside project tech stacks.
    # --------------------------------------------------------

    skills = extract_skills(text)

    # --------------------------------------------------------
    # Education
    # --------------------------------------------------------

    education = extract_education(text)

    # --------------------------------------------------------
    # Experience
    #
    # IMPORTANT: only actual experience section is considered.
    # --------------------------------------------------------

    experience_entries = extract_experience_entries(
        sections
    )

    experience_years = estimate_experience_years(
        text,
        sections=sections,
    )

    # --------------------------------------------------------
    # Projects
    # --------------------------------------------------------

    projects = extract_projects(sections)

    # --------------------------------------------------------
    # Research
    # --------------------------------------------------------

    research_publications = extract_research_publications(
        sections
    )

    # --------------------------------------------------------
    # Certifications
    # --------------------------------------------------------

    certifications = extract_certifications(
        sections
    )

    # --------------------------------------------------------
    # Achievements
    # --------------------------------------------------------

    achievements = extract_achievements(
        sections
    )

    # --------------------------------------------------------
    # Professional summary
    # --------------------------------------------------------

    professional_summary = extract_professional_summary(
        sections
    )

    # --------------------------------------------------------
    # Return profile
    # --------------------------------------------------------

    return {
        "contact": contact,

        "professional_summary": professional_summary,

        "skills": skills,

        "education": education,

        "experience_years": experience_years,

        "experience": experience_entries,

        "projects": projects,

        "research_publications": research_publications,

        "certifications": certifications,

        "achievements": achievements,

        "sections_detected": [
            key
            for key in sections
            if key != "header" and sections[key]
        ],

        "raw_length_chars": len(text),
    }