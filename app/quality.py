"""
Resume quality analysis.

Evaluates basic resume quality signals:
- readability
- section completeness
- contact information
- resume length
- ATS-friendly formatting

The readability check is fault-tolerant. If textstat/NLTK
resources such as cmudict are unavailable, the ATS pipeline
continues without crashing.
"""

import re

import textstat


def readability_analysis(text: str) -> dict:
    """
    Calculate readability metrics safely.
    """

    if not text or not text.strip():
        return {
            "flesch_reading_ease": 0.0,
            "readability_level": "Unknown",
            "error": "No text available for readability analysis.",
        }

    try:
        ease = textstat.flesch_reading_ease(text)

        if ease >= 80:
            level = "Very Easy"
        elif ease >= 70:
            level = "Easy"
        elif ease >= 60:
            level = "Standard"
        elif ease >= 50:
            level = "Fairly Difficult"
        elif ease >= 30:
            level = "Difficult"
        else:
            level = "Very Difficult"

        return {
            "flesch_reading_ease": round(float(ease), 2),
            "readability_level": level,
            "error": None,
        }

    except (LookupError, OSError, RuntimeError):
        return {
            "flesch_reading_ease": None,
            "readability_level": "Unavailable",
            "error": "Readability analysis unavailable.",
        }


def section_analysis(text: str, sections_detected: list) -> dict:
    """
    Analyse resume section completeness.
    """

    expected_sections = [
        "contact",
        "professional_summary",
        "skills",
        "education",
        "experience",
        "projects",
        "achievements",
        "certifications",
    ]

    detected = {
        str(section).strip().lower()
        for section in (sections_detected or [])
    }

    present = [
        section
        for section in expected_sections
        if section in detected
    ]

    missing = [
        section
        for section in expected_sections
        if section not in detected
    ]

    completeness = (
        round(
            len(present) / len(expected_sections) * 100,
            2,
        )
        if expected_sections
        else 100.0
    )

    return {
        "present_sections": present,
        "missing_sections": missing,
        "completeness_score": completeness,
    }


def contact_analysis(text: str) -> dict:
    """
    Check for common contact information.
    """

    email_found = bool(
        re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            text,
        )
    )

    phone_found = bool(
        re.search(
            r"(?:\+?\d[\d\s().-]{8,}\d)",
            text,
        )
    )

    linkedin_found = "linkedin.com" in text.lower()
    github_found = "github.com" in text.lower()

    checks = {
        "email": email_found,
        "phone": phone_found,
        "linkedin": linkedin_found,
        "github": github_found,
    }

    score = round(
        sum(checks.values()) / len(checks) * 100,
        2,
    )

    return {
        "checks": checks,
        "contact_score": score,
    }


def length_analysis(text: str) -> dict:
    """
    Analyse resume length.
    """

    words = re.findall(r"\b\w+\b", text)

    word_count = len(words)
    character_count = len(text)

    if word_count < 150:
        assessment = "Short"
    elif word_count <= 700:
        assessment = "Good"
    elif word_count <= 1000:
        assessment = "Long"
    else:
        assessment = "Very Long"

    return {
        "word_count": word_count,
        "character_count": character_count,
        "assessment": assessment,
    }


def formatting_analysis(text: str) -> dict:
    """
    Basic ATS-friendly formatting checks.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    bullet_lines = sum(
        1
        for line in lines
        if line.startswith(("-", "•", "–", "*"))
    )

    heading_candidates = [
        "summary",
        "objective",
        "skills",
        "education",
        "experience",
        "projects",
        "achievements",
        "certifications",
        "research",
    ]

    lower_text = text.lower()

    detected_heading_count = sum(
        1
        for heading in heading_candidates
        if heading in lower_text
    )

    return {
        "line_count": len(lines),
        "bullet_line_count": bullet_lines,
        "section_heading_count": detected_heading_count,
        "ats_friendly": detected_heading_count >= 3,
    }


def analyze_resume_quality(
    text: str,
    sections_detected: list,
) -> dict:
    """
    Generate the complete resume-quality report.
    """

    readability = readability_analysis(text)

    sections = section_analysis(
        text,
        sections_detected,
    )

    contact = contact_analysis(text)

    length = length_analysis(text)

    formatting = formatting_analysis(text)

    quality_components = [
        sections["completeness_score"],
        contact["contact_score"],
    ]

    formatting_score = (
        100.0
        if formatting["ats_friendly"]
        else 60.0
    )

    quality_components.append(formatting_score)

    overall_quality_score = round(
        sum(quality_components) / len(quality_components),
        2,
    )

    return {
        "quality_score": overall_quality_score,
        "overall_quality_score": overall_quality_score,

        "readability": readability,

        "sections": sections,

        # Compatibility aliases for recommender/database.
        "structure": {
            "sections_present": sections["present_sections"],
            "sections_missing": sections["missing_sections"],
            "completeness_score": sections["completeness_score"],
        },

        "contact": contact,

        "length": length,

        "formatting": formatting,

        "grammar_style": {
            "issues": [],
            "score": 100.0,
        },
    }