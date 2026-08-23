"""
Rule-based recommendation engine.

Turns the ATS report and resume quality analysis into:
- prioritized improvement recommendations
- overall candidate assessment
- suggested job categories
"""

from app.skills_db import SKILL_TAXONOMY


CATEGORY_SKILL_MAP = {
    "Machine Learning / AI Engineer": SKILL_TAXONOMY["ml_ai"],

    "Backend Developer": (
        SKILL_TAXONOMY["web_frameworks"]
        + SKILL_TAXONOMY["databases"]
    ),

    "Frontend Developer": [
        "react",
        "angular",
        "vue.js",
        "javascript",
        "typescript",
        "next.js",
    ],

    "Full Stack Developer": (
        SKILL_TAXONOMY["web_frameworks"]
        + ["javascript", "react"]
    ),

    "Data Scientist / Analyst": (
        SKILL_TAXONOMY["ml_ai"]
        + [
            "excel",
            "tableau",
            "power bi",
            "sql",
        ]
    ),

    "DevOps / Cloud Engineer": (
        SKILL_TAXONOMY["cloud_devops"]
    ),

    "Database Administrator": (
        SKILL_TAXONOMY["databases"]
    ),

    "Business Analyst": (
        SKILL_TAXONOMY["business_tools"]
        + [
            "communication",
            "project management",
        ]
    ),
}


def suggest_job_categories(
    resume_skills: list,
    top_n: int = 3,
) -> list:

    resume_set = {
        str(skill).lower().strip()
        for skill in (resume_skills or [])
    }

    scored = []

    for category, cat_skills in CATEGORY_SKILL_MAP.items():

        cat_set = {
            str(skill).lower().strip()
            for skill in cat_skills
        }

        if not cat_set:
            continue

        overlap = resume_set & cat_set

        score = round(
            len(overlap) / len(cat_set) * 100,
            1,
        )

        if score > 0:
            scored.append(
                {
                    "category": category,
                    "match_score": score,
                    "matching_skills": sorted(overlap),
                }
            )

    scored.sort(
        key=lambda x: -x["match_score"]
    )

    return scored[:top_n]


def generate_recommendations(
    ats_report: dict,
    quality_report: dict,
    resume_profile: dict,
) -> list:

    recs = []

    # ---------------------------------------------------------
    # 1. Missing skills
    # ---------------------------------------------------------

    missing = ats_report.get(
        "missing_skills",
        [],
    )

    if missing:

        top_missing = missing[:8]

        recs.append(
            {
                "priority": "high",
                "category": "Skills Gap",
                "recommendation": (
                    "Add or highlight these missing skills "
                    "if you genuinely have them: "
                    + ", ".join(top_missing)
                    + "."
                ),
            }
        )

    # ---------------------------------------------------------
    # 2. Partially matched skills
    # ---------------------------------------------------------

    partial = ats_report.get(
        "partially_matched_skills",
        [],
    )

    if partial:

        names = []

        for item in partial[:5]:

            if isinstance(item, dict):

                name = item.get(
                    "jd_skill",
                    item.get("skill", ""),
                )

            else:
                name = str(item)

            if name:
                names.append(name)

        if names:

            recs.append(
                {
                    "priority": "medium",
                    "category": "Skill Phrasing",
                    "recommendation": (
                        "Use exact JD terminology for "
                        "these near-matches so ATS keyword "
                        "scanners can recognize them: "
                        + ", ".join(names)
                        + "."
                    ),
                }
            )

    # ---------------------------------------------------------
    # 3. Experience
    # ---------------------------------------------------------

    if ats_report.get(
        "experience_match_score",
        100,
    ) < 70:

        recs.append(
            {
                "priority": "high",
                "category": "Experience",
                "recommendation": (
                    "Your listed experience duration is "
                    "below the JD requirement. Emphasize "
                    "relevant internships, freelance work, "
                    "research, or project experience."
                ),
            }
        )

    # ---------------------------------------------------------
    # 4. Education
    # ---------------------------------------------------------

    if ats_report.get(
        "education_match_score",
        100,
    ) < 100:

        recs.append(
            {
                "priority": "medium",
                "category": "Education",
                "recommendation": (
                    "Make sure your highest degree and "
                    "field of study are clearly stated "
                    "in the Education section."
                ),
            }
        )

    # ---------------------------------------------------------
    # 5. Grammar / style
    # ---------------------------------------------------------

    grammar_style = quality_report.get(
        "grammar_style",
        {},
    )

    grammar_issues = grammar_style.get(
        "issues",
        [],
    )

    for issue in grammar_issues:

        recs.append(
            {
                "priority": "medium",
                "category": "Resume Quality",
                "recommendation": str(issue),
            }
        )

    # ---------------------------------------------------------
    # 6. Missing sections
    # ---------------------------------------------------------

    sections = quality_report.get(
        "sections",
        {},
    )

    missing_sections = sections.get(
        "missing_sections",
        [],
    )

    # Backward compatibility
    if not missing_sections:

        structure = quality_report.get(
            "structure",
            {},
        )

        missing_sections = structure.get(
            "sections_missing",
            [],
        )

    for section in missing_sections:

        recs.append(
            {
                "priority": "high",
                "category": "Structure",
                "recommendation": (
                    f"Consider adding a clearly labeled "
                    f"'{str(section).title()}' section so "
                    "ATS parsers can extract the information "
                    "reliably."
                ),
            }
        )

    # ---------------------------------------------------------
    # 7. Readability
    # ---------------------------------------------------------

    readability = quality_report.get(
        "readability",
        {},
    )

    readability_error = readability.get(
        "error"
    )

    # Don't create a recommendation merely because
    # an optional NLTK resource is unavailable.
    # That is an infrastructure issue, not a resume issue.

    # ---------------------------------------------------------
    # 8. Strong overall score
    # ---------------------------------------------------------

    overall_score = ats_report.get(
        "overall_ats_score",
        0,
    )

    if overall_score >= 85:

        recs.append(
            {
                "priority": "low",
                "category": "Overall",
                "recommendation": (
                    "Strong match. Focus on minor tailoring "
                    "and make sure the resume mirrors the "
                    "most important terminology from the JD."
                ),
            }
        )

    # ---------------------------------------------------------
    # Sort recommendations
    # ---------------------------------------------------------

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    recs.sort(
        key=lambda r: priority_order.get(
            r.get("priority"),
            3,
        )
    )

    return recs


def overall_candidate_assessment(
    ats_report: dict,
    quality_report: dict,
) -> dict:

    score = ats_report.get(
        "overall_ats_score",
        0,
    )

    if score >= 85:

        verdict = (
            "Excellent match — strongly recommend "
            "for shortlisting."
        )

    elif score >= 70:

        verdict = (
            "Good match — recommend for review "
            "with minor gaps to note."
        )

    elif score >= 50:

        verdict = (
            "Moderate match — meets some requirements; "
            "notable gaps exist."
        )

    else:

        verdict = (
            "Weak match — significant gaps against "
            "this job description."
        )

    quality_score = quality_report.get(
        "quality_score",
        quality_report.get(
            "overall_quality_score",
            0,
        ),
    )

    return {
        "verdict": verdict,

        "overall_ats_score": score,

        "resume_quality_score": quality_score,

        "key_strengths": ats_report.get(
            "matched_skills",
            [],
        )[:6],

        "key_gaps": ats_report.get(
            "missing_skills",
            [],
        )[:6],
    }