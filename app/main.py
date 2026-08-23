"""
Advanced ATS Resume Scanner System — FastAPI application.

Endpoints:
    POST /api/resume/parse
        Upload + parse a resume and return extracted profile.

    POST /api/job/analyze
        Analyze a job description.

    POST /api/ats/score
        Full ATS report: resume + JD -> score + AI analysis.

    POST /api/skills/gap
        Skill-gap analysis.

    POST /api/recommendations
        Resume improvement recommendations.

    GET /api/history
        List past analyses.

    GET /api/history/{analysis_id}
        Fetch one past analysis.

    GET /api/health
        Health check.
"""

import os
from typing import Any

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
)

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ============================================================
# EXISTING APPLICATION MODULES
# ============================================================

from app.parser import parse_document
from app.extractor import extract_resume_profile
from app.jd_analyzer import analyze_job_description
from app.scorer import generate_ats_report
from app.quality import analyze_resume_quality

from app.recommender import (
    generate_recommendations,
    overall_candidate_assessment,
    suggest_job_categories,
)

from app.database import (
    init_db,
    save_analysis,
    get_history,
    get_analysis_by_id,
)


# ============================================================
# CENTRALIZED GROQ LLM
# ============================================================
#
# IMPORTANT:
# Groq API handling now belongs to app.llm.
#
# Do NOT create another Groq client here.
# Do NOT call client.chat.completions.create() here.
# Do NOT json.loads() the raw Groq response here.
#
# app.llm already handles:
#   - API key
#   - model
#   - JSON response
#   - <think> blocks
#   - JSON parsing
#   - fallback handling
#
# ============================================================

from app.llm import (
    analyze_with_llm,
    test_groq_connection,
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Advanced ATS Resume Scanner System",
    description=(
        "Analyzes resumes against job descriptions and generates "
        "ATS compatibility reports with Groq-powered AI analysis."
    ),
    version="1.2.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE STARTUP
# ============================================================

@app.on_event("startup")
def on_startup():
    init_db()


# ============================================================
# REQUEST MODELS
# ============================================================

class JobDescriptionIn(BaseModel):
    text: str
    job_title: str | None = None


# ============================================================
# GROQ CONFIGURATION
# ============================================================

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "qwen/qwen3.6-27b",
)


def _groq_configured() -> bool:
    """
    Check whether a Groq API key is configured.

    Actual Groq connectivity is handled by app.llm.
    """

    return bool(
        os.getenv("GROQ_API_KEY")
    )


# ============================================================
# GROQ AI ANALYSIS
# ============================================================

def _run_llm_analysis(
    resume_text: str,
    jd_text: str,
    ats_report: dict,
    quality_report: dict,
    resume_profile: dict,
    jd_profile: dict,
) -> dict:
    """
    Run centralized Groq AI analysis.

    The deterministic ATS engine remains the source of truth.

    app.llm handles:
        - Groq API connection
        - prompt construction
        - structured JSON
        - reasoning-block removal
        - JSON parsing
        - fallback handling

    This function exists only as a compatibility layer so the
    rest of the existing ATS pipeline does not need to change.
    """

    try:

        result = analyze_with_llm(
            resume_text=resume_text,
            jd_text=jd_text,
            ats_report=ats_report,
        )

        return result

    except Exception as exc:

        return {
            "summary": "LLM analysis unavailable.",
            "strengths": [],
            "gaps": [],
            "recommendations": [],
            "error": type(exc).__name__,
            "details": str(exc),
        }


# ============================================================
# QUALITY REPORT COMPATIBILITY
# ============================================================

def _normalize_quality_report(
    quality_report: dict,
) -> dict:
    """
    Normalize quality report keys so older/newer modules remain
    compatible.

    Existing quality.py currently returns:
        overall_quality_score

    database.py expects:
        quality_score

    recommender.py may expect:
        grammar_style

    This adapter prevents those differences from breaking the
    complete ATS pipeline.
    """

    if "quality_score" not in quality_report:

        quality_report["quality_score"] = (
            quality_report.get(
                "overall_quality_score",
                0.0,
            )
        )

    if "overall_quality_score" not in quality_report:

        quality_report["overall_quality_score"] = (
            quality_report.get(
                "quality_score",
                0.0,
            )
        )

    if "grammar_style" not in quality_report:

        quality_report["grammar_style"] = {
            "issues": []
        }

    return quality_report


# ============================================================
# FULL ANALYSIS
# ============================================================

def _run_full_analysis(
    resume_text: str,
    jd_text: str,
    job_title: str | None = None,
) -> dict:
    """
    Run the complete ATS analysis pipeline.

    Pipeline:

    Resume
        ↓
    Resume Profile Extraction
        ↓
    JD Analysis
        ↓
    ATS Scoring
        ↓
    Resume Quality
        ↓
    Recommendations
        ↓
    Candidate Assessment
        ↓
    Job Category Suggestions
        ↓
    Groq AI Analysis
    """

    # --------------------------------------------------------
    # 1. RESUME PROFILE
    # --------------------------------------------------------

    resume_profile = extract_resume_profile(
        resume_text
    )

    # --------------------------------------------------------
    # 2. JOB DESCRIPTION PROFILE
    # --------------------------------------------------------

    jd_profile = analyze_job_description(
        jd_text,
        job_title,
    )

    # --------------------------------------------------------
    # 3. ATS SCORE
    # --------------------------------------------------------

    ats_report = generate_ats_report(
        resume_profile,
        resume_text,
        jd_profile,
        jd_text,
    )

    # --------------------------------------------------------
    # 4. RESUME QUALITY
    # --------------------------------------------------------

    quality_report = analyze_resume_quality(
        resume_text,
        resume_profile.get(
            "sections_detected",
            [],
        ),
    )

    quality_report = _normalize_quality_report(
        quality_report
    )

    # --------------------------------------------------------
    # 5. RECOMMENDATIONS
    # --------------------------------------------------------

    recommendations = generate_recommendations(
        ats_report,
        quality_report,
        resume_profile,
    )

    # --------------------------------------------------------
    # 6. OVERALL ASSESSMENT
    # --------------------------------------------------------

    assessment = overall_candidate_assessment(
        ats_report,
        quality_report,
    )

    # --------------------------------------------------------
    # 7. JOB CATEGORIES
    # --------------------------------------------------------

    job_categories = suggest_job_categories(
        resume_profile.get(
            "skills",
            [],
        )
    )

    # --------------------------------------------------------
    # 8. GROQ AI ANALYSIS
    # --------------------------------------------------------

    llm_analysis = _run_llm_analysis(
        resume_text=resume_text,
        jd_text=jd_text,
        ats_report=ats_report,
        quality_report=quality_report,
        resume_profile=resume_profile,
        jd_profile=jd_profile,
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    return {
        "resume_profile": resume_profile,

        "job_description_profile": jd_profile,

        "ats_report": ats_report,

        "quality_report": quality_report,

        "recommendations": recommendations,

        "overall_assessment": assessment,

        "suggested_job_categories": job_categories,

        "ai_analysis": llm_analysis,
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():
    """
    Health check.

    This reports whether the API key is configured.
    It does not call Groq on every health request.
    """

    return {
        "status": "ok",

        "groq_available": True,

        "groq_configured": _groq_configured(),

        "groq_model": GROQ_MODEL,
    }


# ============================================================
# GROQ TEST ENDPOINT
# ============================================================

@app.get("/api/health/groq")
def groq_health():
    """
    Explicitly test the Groq connection.
    """

    success = test_groq_connection()

    return {
        "status": (
            "ok"
            if success
            else "error"
        ),
        "provider": "groq",
        "model": GROQ_MODEL,
        "connected": success,
    }


# ============================================================
# RESUME PARSER
# ============================================================

@app.post("/api/resume/parse")
async def parse_resume(
    file: UploadFile = File(...),
):
    """
    Upload a resume and extract structured information.
    """

    content = await file.read()

    try:

        text = parse_document(
            file.filename,
            content,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    if not text.strip():

        raise HTTPException(
            status_code=422,
            detail=(
                "Could not extract any text "
                "from this file."
            ),
        )

    profile = extract_resume_profile(
        text
    )

    return {
        "filename": file.filename,
        "raw_text": text,
        "profile": profile,
    }


# ============================================================
# JOB DESCRIPTION ANALYZER
# ============================================================

@app.post("/api/job/analyze")
def analyze_job(
    payload: JobDescriptionIn,
):
    """
    Analyze a job description.
    """

    if not payload.text.strip():

        raise HTTPException(
            status_code=422,
            detail=(
                "Job description text is empty."
            ),
        )

    return analyze_job_description(
        payload.text,
        payload.job_title,
    )


# ============================================================
# ATS SCORE
# ============================================================

@app.post("/api/ats/score")
async def ats_score(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    job_title: str | None = Form(None),
    save_to_history: bool = Form(True),
):
    """
    Generate the complete ATS report.
    """

    # --------------------------------------------------------
    # READ RESUME
    # --------------------------------------------------------

    content = await file.read()

    try:

        resume_text = parse_document(
            file.filename,
            content,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not resume_text.strip():

        raise HTTPException(
            status_code=422,
            detail=(
                "Could not extract any text "
                "from this resume."
            ),
        )

    if not job_description.strip():

        raise HTTPException(
            status_code=422,
            detail=(
                "Job description text is empty."
            ),
        )

    # --------------------------------------------------------
    # FULL ANALYSIS
    # --------------------------------------------------------

    try:

        result = _run_full_analysis(
            resume_text,
            job_description,
            job_title,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"ATS analysis failed: "
                f"{type(exc).__name__}: {str(exc)}"
            ),
        )

    # --------------------------------------------------------
    # SAVE HISTORY
    # --------------------------------------------------------

    analysis_id = None

    if save_to_history:

        analysis_id = save_analysis(
            result,

            candidate_name=(
                result[
                    "resume_profile"
                ].get(
                    "contact",
                    {}
                ).get("name")
            ),

            resume_filename=file.filename,

            job_title=job_title,
        )

    # --------------------------------------------------------
    # ADD ANALYSIS ID
    # --------------------------------------------------------

    result["analysis_id"] = analysis_id

    return result


# ============================================================
# SKILL GAP ANALYSIS
# ============================================================

@app.post("/api/skills/gap")
async def skills_gap(
    file: UploadFile = File(...),
    job_description: str = Form(...),
):
    """
    Compare resume skills with JD skills.
    """

    content = await file.read()

    try:

        resume_text = parse_document(
            file.filename,
            content,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    if not resume_text.strip():

        raise HTTPException(
            status_code=422,
            detail=(
                "Could not extract any text "
                "from this resume."
            ),
        )

    if not job_description.strip():

        raise HTTPException(
            status_code=422,
            detail=(
                "Job description text is empty."
            ),
        )

    # --------------------------------------------------------
    # PROFILES
    # --------------------------------------------------------

    resume_profile = extract_resume_profile(
        resume_text
    )

    jd_profile = analyze_job_description(
        job_description
    )

    # --------------------------------------------------------
    # ATS REPORT
    # --------------------------------------------------------

    ats_report = generate_ats_report(
        resume_profile,
        resume_text,
        jd_profile,
        job_description,
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "matched_skills": (
            ats_report.get(
                "matched_skills",
                [],
            )
        ),

        "partially_matched_skills": (
            ats_report.get(
                "partially_matched_skills",
                [],
            )
        ),

        "missing_skills": (
            ats_report.get(
                "missing_skills",
                [],
            )
        ),

        "missing_keywords": (
            ats_report.get(
                "missing_keywords",
                [],
            )
        ),
    }


# ============================================================
# RECOMMENDATIONS
# ============================================================

@app.post("/api/recommendations")
async def recommendations_endpoint(
    file: UploadFile = File(...),
    job_description: str = Form(...),
):
    """
    Generate resume improvement recommendations.
    """

    content = await file.read()

    try:

        resume_text = parse_document(
            file.filename,
            content,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    if not resume_text.strip():

        raise HTTPException(
            status_code=422,
            detail=(
                "Could not extract any text "
                "from this resume."
            ),
        )

    if not job_description.strip():

        raise HTTPException(
            status_code=422,
            detail=(
                "Job description text is empty."
            ),
        )

    # --------------------------------------------------------
    # PROFILES
    # --------------------------------------------------------

    resume_profile = extract_resume_profile(
        resume_text
    )

    jd_profile = analyze_job_description(
        job_description
    )

    # --------------------------------------------------------
    # ATS REPORT
    # --------------------------------------------------------

    ats_report = generate_ats_report(
        resume_profile,
        resume_text,
        jd_profile,
        job_description,
    )

    # --------------------------------------------------------
    # QUALITY
    # --------------------------------------------------------

    quality_report = analyze_resume_quality(
        resume_text,
        resume_profile.get(
            "sections_detected",
            [],
        ),
    )

    quality_report = _normalize_quality_report(
        quality_report
    )

    # --------------------------------------------------------
    # RECOMMENDATIONS
    # --------------------------------------------------------

    recommendations = generate_recommendations(
        ats_report,
        quality_report,
        resume_profile,
    )

    # --------------------------------------------------------
    # ASSESSMENT
    # --------------------------------------------------------

    assessment = overall_candidate_assessment(
        ats_report,
        quality_report,
    )

    # --------------------------------------------------------
    # JOB CATEGORIES
    # --------------------------------------------------------

    job_categories = suggest_job_categories(
        resume_profile.get(
            "skills",
            [],
        )
    )

    # --------------------------------------------------------
    # GROQ AI
    # --------------------------------------------------------

    llm_analysis = _run_llm_analysis(
        resume_text=resume_text,
        jd_text=job_description,
        ats_report=ats_report,
        quality_report=quality_report,
        resume_profile=resume_profile,
        jd_profile=jd_profile,
    )

    return {
        "recommendations": recommendations,

        "overall_assessment": assessment,

        "suggested_job_categories": job_categories,

        "ai_analysis": llm_analysis,
    }


# ============================================================
# HISTORY
# ============================================================

@app.get("/api/history")
def history(
    limit: int = 50,
    offset: int = 0,
):
    """
    Return previous ATS analyses.
    """

    return {
        "results": get_history(
            limit=limit,
            offset=offset,
        )
    }


# ============================================================
# HISTORY DETAIL
# ============================================================

@app.get("/api/history/{analysis_id}")
def history_detail(
    analysis_id: int,
):
    """
    Return a single stored ATS analysis.
    """

    record = get_analysis_by_id(
        analysis_id
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail="Analysis not found.",
        )

    return record