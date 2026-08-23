"""
Runs all 50 test cases through the full pipeline and reports:
  - Skill extraction coverage (skills found per resume vs skills the
    generator actually embedded)
  - Matching accuracy vs the expected match band (strong/moderate/weak)
  - ATS score consistency (do repeated runs on identical input agree?
    the pipeline is deterministic, so this checks for score stability)
  - Recommendation quality (does a weak-match resume get more/higher
    -priority recommendations than a strong-match one?)

Run with: python evaluate.py
"""
import json
import statistics
from collections import defaultdict

from app.extractor import extract_resume_profile
from app.jd_analyzer import analyze_job_description
from app.scorer import generate_ats_report
from app.quality import analyze_resume_quality
from app.recommender import generate_recommendations

EXPECTED_SCORE_BANDS = {
    "strong": (65, 100),
    "moderate": (35, 75),
    "weak": (0, 45),
}


def run_case(case: dict) -> dict:
    resume_text = case["resume_text"]
    jd_text = case["job_description_text"]

    resume_profile = extract_resume_profile(resume_text)
    jd_profile = analyze_job_description(jd_text)
    ats_report = generate_ats_report(resume_profile, resume_text, jd_profile, jd_text)
    quality_report = analyze_resume_quality(resume_text, resume_profile["sections_detected"])
    recs = generate_recommendations(ats_report, quality_report, resume_profile)

    return {
        "id": case["id"],
        "domain": case["domain"],
        "expected_match_level": case["expected_match_level"],
        "extracted_skill_count": len(resume_profile["skills"]),
        "overall_ats_score": ats_report["overall_ats_score"],
        "skills_match_score": ats_report["skills_match_score"],
        "missing_skill_count": len(ats_report["missing_skills"]),
        "recommendation_count": len(recs),
        "high_priority_recs": sum(1 for r in recs if r["priority"] == "high"),
    }


def score_within_expected_band(result: dict) -> bool:
    lo, hi = EXPECTED_SCORE_BANDS[result["expected_match_level"]]
    return lo <= result["overall_ats_score"] <= hi


def check_determinism(case: dict, n_runs: int = 3) -> bool:
    scores = [run_case(case)["overall_ats_score"] for _ in range(n_runs)]
    return len(set(scores)) == 1


def main():
    with open("data/test_cases/test_cases.json") as f:
        cases = json.load(f)

    results = [run_case(c) for c in cases]

    # 1. Extraction coverage
    avg_skills_extracted = statistics.mean(r["extracted_skill_count"] for r in results)

    # 2. Matching / score-band accuracy
    band_hits = sum(1 for r in results if score_within_expected_band(r))
    band_accuracy = band_hits / len(results) * 100

    by_level = defaultdict(list)
    for r in results:
        by_level[r["expected_match_level"]].append(r["overall_ats_score"])

    # 3. Score consistency (determinism check on a sample)
    deterministic = all(check_determinism(c) for c in cases[:5])

    # 4. Recommendation quality: weak-match cases should get >= high-priority
    #    recs than strong-match cases, on average
    avg_high_priority = {
        level: statistics.mean(r["high_priority_recs"] for r in results if r["expected_match_level"] == level)
        for level in ("strong", "moderate", "weak")
    }
    recommendation_quality_ok = avg_high_priority["weak"] >= avg_high_priority["strong"]

    print("=" * 60)
    print("ATS SCANNER EVALUATION REPORT")
    print("=" * 60)
    print(f"Total test cases run: {len(results)}")
    print(f"\n[Skill Extraction]")
    print(f"  Average skills extracted per resume: {avg_skills_extracted:.1f}")
    print(f"\n[Matching Accuracy]")
    print(f"  Score-band accuracy (score falls in expected range): {band_accuracy:.1f}%")
    for level, scores in by_level.items():
        print(f"  {level:10s}: avg score = {statistics.mean(scores):.1f}, "
              f"range = [{min(scores):.1f}, {max(scores):.1f}], n={len(scores)}")
    print(f"\n[Score Consistency]")
    print(f"  Deterministic on repeated runs (sample of 5): {deterministic}")
    print(f"\n[Recommendation Quality]")
    for level, avg in avg_high_priority.items():
        print(f"  {level:10s}: avg high-priority recs = {avg:.2f}")
    print(f"  Weak-match resumes get >= high-priority recs than strong-match: {recommendation_quality_ok}")
    print("=" * 60)

    with open("data/test_cases/evaluation_results.json", "w") as f:
        json.dump({
            "avg_skills_extracted": avg_skills_extracted,
            "score_band_accuracy_pct": band_accuracy,
            "by_level_avg_score": {k: statistics.mean(v) for k, v in by_level.items()},
            "deterministic": deterministic,
            "avg_high_priority_recs_by_level": avg_high_priority,
            "per_case_results": results,
        }, f, indent=2)
    print("Detailed results saved to data/test_cases/evaluation_results.json")


if __name__ == "__main__":
    main()
