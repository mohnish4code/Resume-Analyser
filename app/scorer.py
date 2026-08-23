"""
ATS scoring engine.

Combines:
- skill matching
- experience compatibility
- education compatibility
- keyword matching
- semantic similarity

into one explainable ATS score.
"""

from app.matcher import (
    match_skills,
    keyword_match_score,
    semantic_similarity,
    experience_match_score,
    education_match_score,
)


# ============================================================
# SCORE WEIGHTS
# ============================================================

WEIGHTS = {
    "skills_match": 0.35,
    "experience_match": 0.15,
    "education_match": 0.10,
    "keyword_match": 0.15,
    "semantic_similarity": 0.25,
}


# ============================================================
# HELPERS
# ============================================================

def _safe_float(value, default=0.0):
    """
    Convert a value to float safely.
    """
    try:
        if value is None:
            return default

        if isinstance(value, bool):
            return float(value)

        return float(value)

    except (TypeError, ValueError):
        return default


def _get_jd_education_level(jd_profile: dict) -> int:
    """
    Extract the required education level from JD profile.

    Supports both formats:

    New format:
        {
            "education": {
                "min_level": 3
            }
        }

    Older format:
        {
            "min_education_level": 3
        }

    Also protects against accidental list values.
    """

    education = jd_profile.get("education")

    # --------------------------------------------------------
    # Preferred format
    # --------------------------------------------------------

    if isinstance(education, dict):

        min_level = education.get("min_level")

        if isinstance(min_level, (int, float)):
            return int(min_level)

        # Sometimes analyzer may return requirements
        requirements = education.get("requirements")

        if isinstance(requirements, list):

            levels = []

            for requirement in requirements:

                if isinstance(requirement, dict):

                    level = requirement.get("level")

                    if isinstance(level, (int, float)):
                        levels.append(int(level))

            if levels:
                return min(levels)

    # --------------------------------------------------------
    # Backward compatibility
    # --------------------------------------------------------

    min_level = jd_profile.get("min_education_level")

    if isinstance(min_level, (int, float)):
        return int(min_level)

    # --------------------------------------------------------
    # If something accidentally returns a list
    # --------------------------------------------------------

    if isinstance(min_level, list):

        levels = []

        for item in min_level:

            if isinstance(item, dict):

                level = item.get("level")

                if isinstance(level, (int, float)):
                    levels.append(int(level))

            elif isinstance(item, (int, float)):
                levels.append(int(item))

        if levels:
            return min(levels)

    return 0


def _get_jd_education_degree(jd_profile: dict):
    """
    Safely extract the minimum education degree.
    """

    education = jd_profile.get("education")

    if isinstance(education, dict):

        degree = education.get("min_degree")

        if degree:
            return degree

    return jd_profile.get("min_education_degree")


# ============================================================
# SKILL SCORE
# ============================================================

def compute_skills_match_score(
    matched: list,
    partially_matched: list,
    missing: list,
) -> float:
    """
    Calculate percentage based on:

    matched            = 100%
    partially matched  = 50%
    missing            = 0%
    """

    matched = matched or []
    partially_matched = partially_matched or []
    missing = missing or []

    total = (
        len(matched)
        + len(partially_matched)
        + len(missing)
    )

    if total == 0:
        return 100.0

    score = (
        len(matched) * 1.0
        + len(partially_matched) * 0.5
    ) / total * 100

    return round(score, 2)


# ============================================================
# MAIN ATS REPORT
# ============================================================

def generate_ats_report(
    resume_profile: dict,
    resume_text: str,
    jd_profile: dict,
    jd_text: str,
) -> dict:

    # --------------------------------------------------------
    # Resume skills
    # --------------------------------------------------------

    resume_skills = resume_profile.get("skills", [])

    if not isinstance(resume_skills, list):
        resume_skills = []


    # --------------------------------------------------------
    # JD skills
    # --------------------------------------------------------

    jd_required = jd_profile.get("required_skills", [])
    jd_preferred = jd_profile.get("preferred_skills", [])

    if not isinstance(jd_required, list):
        jd_required = []

    if not isinstance(jd_preferred, list):
        jd_preferred = []


    # Remove duplicates while preserving order
    all_jd_skills = list(
        dict.fromkeys(
            jd_required + jd_preferred
        )
    )


    # --------------------------------------------------------
    # SKILL MATCH
    # --------------------------------------------------------

    skill_match = match_skills(
        resume_skills,
        all_jd_skills,
    )

    matched = skill_match.get("matched", [])
    partially_matched = skill_match.get(
        "partially_matched",
        [],
    )
    missing = skill_match.get("missing", [])

    skills_score = compute_skills_match_score(
        matched,
        partially_matched,
        missing,
    )


    # --------------------------------------------------------
    # EXPERIENCE MATCH
    # --------------------------------------------------------

    resume_experience = _safe_float(
        resume_profile.get(
            "experience_years",
            0,
        )
    )

    jd_experience = _safe_float(
        jd_profile.get(
            "min_experience_years",
            0,
        )
    )

    # Support newer nested structure
    experience = jd_profile.get("experience")

    if isinstance(experience, dict):

        jd_experience = _safe_float(
            experience.get(
                "min_years",
                jd_experience,
            )
        )

    exp_score = experience_match_score(
        resume_experience,
        jd_experience,
    )


    # --------------------------------------------------------
    # EDUCATION MATCH
    # --------------------------------------------------------

    resume_education = resume_profile.get(
        "education",
        [],
    )

    if not isinstance(resume_education, list):
        resume_education = []

    jd_education_level = _get_jd_education_level(
        jd_profile
    )

    edu_score = education_match_score(
        resume_education,
        jd_education_level,
    )

    jd_degree = _get_jd_education_degree(
        jd_profile
    )


    # --------------------------------------------------------
    # KEYWORD MATCH
    # --------------------------------------------------------

    keyword_result = keyword_match_score(
        resume_text,
        all_jd_skills,
    )

    keyword_score = _safe_float(
        keyword_result.get("score", 0)
    )

    present_keywords = keyword_result.get(
        "present_keywords",
        [],
    )

    missing_keywords = keyword_result.get(
        "missing_keywords",
        [],
    )


    # --------------------------------------------------------
    # SEMANTIC SIMILARITY
    # --------------------------------------------------------

    semantic_score = _safe_float(
        semantic_similarity(
            resume_text,
            jd_text,
        )
    )


    # --------------------------------------------------------
    # OVERALL SCORE
    # --------------------------------------------------------

    overall = (
        WEIGHTS["skills_match"]
        * skills_score

        + WEIGHTS["experience_match"]
        * exp_score

        + WEIGHTS["education_match"]
        * edu_score

        + WEIGHTS["keyword_match"]
        * keyword_score

        + WEIGHTS["semantic_similarity"]
        * semantic_score
    )

    overall = round(
        min(
            100.0,
            max(
                0.0,
                overall,
            ),
        ),
        2,
    )


    # --------------------------------------------------------
    # SCORE BREAKDOWN
    # --------------------------------------------------------

    breakdown = [

        {
            "component": "Skills Match",
            "weight": WEIGHTS["skills_match"],
            "score": skills_score,
            "contribution": round(
                WEIGHTS["skills_match"]
                * skills_score,
                2,
            ),
            "explanation": (
                f"{len(matched)} matched, "
                f"{len(partially_matched)} partial, "
                f"{len(missing)} missing "
                f"out of {len(all_jd_skills)} JD skills."
            ),
        },

        {
            "component": "Experience Match",
            "weight": WEIGHTS["experience_match"],
            "score": exp_score,
            "contribution": round(
                WEIGHTS["experience_match"]
                * exp_score,
                2,
            ),
            "explanation": (
                f"Resume shows approximately "
                f"{resume_experience} years vs "
                f"{jd_experience} years required."
            ),
        },

        {
            "component": "Education Match",
            "weight": WEIGHTS["education_match"],
            "score": edu_score,
            "contribution": round(
                WEIGHTS["education_match"]
                * edu_score,
                2,
            ),
            "explanation": (
                f"Required education level: "
                f"{jd_degree or jd_education_level or 'none specified'}."
            ),
        },

        {
            "component": "Keyword Match",
            "weight": WEIGHTS["keyword_match"],
            "score": keyword_score,
            "contribution": round(
                WEIGHTS["keyword_match"]
                * keyword_score,
                2,
            ),
            "explanation": (
                f"{len(present_keywords)}/"
                f"{len(all_jd_skills) or 1} "
                f"JD keywords found in resume."
            ),
        },

        {
            "component": "Semantic Similarity",
            "weight": WEIGHTS["semantic_similarity"],
            "score": semantic_score,
            "contribution": round(
                WEIGHTS["semantic_similarity"]
                * semantic_score,
                2,
            ),
            "explanation": (
                "TF-IDF cosine similarity "
                "between resume and job description."
            ),
        },
    ]


    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {

        "overall_ats_score": overall,

        "skills_match_score": skills_score,

        "experience_match_score": exp_score,

        "education_match_score": edu_score,

        "keyword_match_score": keyword_score,

        "semantic_similarity_score": semantic_score,

        "matched_skills": matched,

        "partially_matched_skills": partially_matched,

        "missing_skills": missing,

        "missing_keywords": missing_keywords,

        "score_breakdown": breakdown,
    }