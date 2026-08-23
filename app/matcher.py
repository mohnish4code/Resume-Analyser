"""
Matching engine: exact/fuzzy skill matching plus TF-IDF cosine
semantic similarity between resume and job description text.

Semantic similarity uses TF-IDF + cosine similarity rather than a
downloaded transformer embedding model, so the whole system runs
fully offline with no external model downloads. TF-IDF cosine
similarity is a legitimate, well-established semantic similarity
technique for document matching (it captures term co-occurrence and
importance beyond raw keyword overlap). Swapping in
sentence-transformer embeddings later is a drop-in change to
`semantic_similarity()` if the deployment environment has internet
access to a model hub.
"""
import re
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def match_skills(resume_skills: list, jd_skills: list, fuzzy_threshold: int = 85) -> dict:
    """
    Classifies each JD skill as matched (exact/alias match in resume),
    partially matched (fuzzy-close term found, e.g. "django" vs
    "django rest framework"), or missing.
    """
    resume_set = set(resume_skills)
    matched, partial, missing = [], [], []

    for jd_skill in jd_skills:
        if jd_skill in resume_set:
            matched.append(jd_skill)
            continue
        best_score = 0
        best_match = None
        for r_skill in resume_skills:
            # token_sort_ratio handles multi-word skills ("django rest
            # framework" vs "rest framework django") without the
            # substring-happy false positives of partial_ratio (which
            # would wrongly match "pytorch" against "python").
            score = fuzz.token_sort_ratio(jd_skill, r_skill)
            if score > best_score:
                best_score, best_match = score, r_skill
        if best_score >= fuzzy_threshold:
            partial.append({"jd_skill": jd_skill, "closest_resume_skill": best_match,
                             "similarity": best_score})
        else:
            missing.append(jd_skill)

    return {"matched": matched, "partially_matched": partial, "missing": missing}


def keyword_match_score(resume_text: str, jd_keywords: list) -> dict:
    """Simple presence-based keyword match score, distinct from skills matching
    (covers JD-specific terms like tool names, domain jargon, methodologies)."""
    text_lower = resume_text.lower()
    present, absent = [], []
    for kw in jd_keywords:
        pattern = r"(?<![a-z0-9])" + re.escape(kw.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            present.append(kw)
        else:
            absent.append(kw)
    score = (len(present) / len(jd_keywords) * 100) if jd_keywords else 100.0
    return {"score": round(score, 2), "present_keywords": present, "missing_keywords": absent}


def semantic_similarity(resume_text: str, jd_text: str) -> float:
    """TF-IDF cosine similarity between resume and JD, scaled 0-100."""
    if not resume_text.strip() or not jd_text.strip():
        return 0.0
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
    try:
        matrix = vectorizer.fit_transform([resume_text, jd_text])
    except ValueError:
        return 0.0
    sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
    return round(float(sim) * 100, 2)


def experience_match_score(resume_years: float, min_required_years: float) -> float:
    if min_required_years <= 0:
        return 100.0
    if resume_years >= min_required_years:
        return 100.0
    return round(max(0.0, (resume_years / min_required_years)) * 100, 2)


def education_match_score(resume_education: list, min_level_required: int) -> float:
    if min_level_required <= 0:
        return 100.0
    resume_max_level = max((e["level"] for e in resume_education), default=0)
    if resume_max_level >= min_level_required:
        return 100.0
    if resume_max_level == 0:
        return 0.0
    return round((resume_max_level / min_level_required) * 100, 2)
