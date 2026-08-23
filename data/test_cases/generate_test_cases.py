"""
Generates 50 synthetic (resume, job_description, expected_signal) test
cases spanning several domains (ML, backend, frontend, data, devops,
business) and difficulty bands (strong / moderate / weak match), so
the evaluation script has something to score against.

`expected_signal` is a coarse label a human reviewer would assign —
used to sanity-check that the ATS score band and skill-gap direction
are directionally correct, not as an exact ground truth score.
"""
import json
import random

random.seed(42)

DOMAINS = {
    "ml_engineer": {
        "core_skills": ["python", "tensorflow", "pytorch", "machine learning", "deep learning",
                         "scikit-learn", "pandas", "numpy", "sql"],
        "bonus_skills": ["docker", "kubernetes", "aws", "mlops", "nlp", "computer vision"],
        "title": "Machine Learning Engineer",
    },
    "backend_dev": {
        "core_skills": ["python", "django", "flask", "fastapi", "sql", "postgresql", "rest api", "git"],
        "bonus_skills": ["docker", "kubernetes", "redis", "microservices", "aws"],
        "title": "Backend Developer",
    },
    "frontend_dev": {
        "core_skills": ["javascript", "react", "html", "css", "typescript", "git"],
        "bonus_skills": ["next.js", "redux", "tailwind", "figma"],
        "title": "Frontend Developer",
    },
    "data_analyst": {
        "core_skills": ["sql", "excel", "python", "tableau", "power bi", "statistics"],
        "bonus_skills": ["r", "machine learning", "pandas"],
        "title": "Data Analyst",
    },
    "devops_engineer": {
        "core_skills": ["docker", "kubernetes", "aws", "terraform", "ci/cd", "linux", "git"],
        "bonus_skills": ["ansible", "jenkins", "azure", "python"],
        "title": "DevOps Engineer",
    },
}

NAMES = [
    "Aarav Mehta", "Diya Patel", "Rohan Verma", "Isha Kapoor", "Karan Singh",
    "Ananya Rao", "Vikram Nair", "Priya Iyer", "Arjun Reddy", "Sneha Gupta",
]

EDU_LINES = [
    "B.Tech in Computer Science, XYZ Institute of Technology, 2025, CGPA 8.2",
    "B.E. in Electronics and Computer Engineering, ABC University, 2026, CGPA 7.9",
    "M.Tech in Data Science, National Institute of Technology, 2024",
    "Bachelor of Computer Applications, State University, 2023",
    "Diploma in Computer Engineering, City Polytechnic, 2022",
]


def make_resume(domain_key: str, match_level: str, idx: int) -> str:
    domain = DOMAINS[domain_key]
    name = NAMES[idx % len(NAMES)]
    email = name.lower().replace(" ", ".") + f"{idx}@email.com"
    phone = f"9{random.randint(100000000, 999999999)}"
    edu = EDU_LINES[idx % len(EDU_LINES)]

    if match_level == "strong":
        skills = domain["core_skills"] + domain["bonus_skills"][:2]
        exp_years = random.choice([2, 3, 4])
    elif match_level == "moderate":
        skills = domain["core_skills"][: max(3, len(domain["core_skills"]) // 2)]
        exp_years = random.choice([1, 2])
    else:  # weak
        other_domain = random.choice([d for d in DOMAINS if d != domain_key])
        skills = DOMAINS[other_domain]["core_skills"][:3]
        exp_years = random.choice([0, 1])

    start_year = 2026 - exp_years
    resume = f"""{name}
{email} | {phone} | linkedin.com/in/{name.lower().replace(' ', '')}

Education
{edu}

Skills
{', '.join(skills)}

Experience
{start_year} - Present: Software Engineer Intern, TechNova Solutions
- Worked on {domain['title'].lower()} related tasks using {skills[0] if skills else 'various tools'}
- Collaborated with a team of 5 to deliver features on schedule
- Improved system performance by {random.randint(10, 40)}%

Projects
{domain['title']} Mini Project
- Built a project applying {', '.join(skills[:3]) if skills else 'general programming'}
- Achieved measurable improvement in project outcomes

Certifications
{random.choice(['AWS Certified Cloud Practitioner', 'Google Data Analytics Certificate', 'Scrum Master Certified', 'None'])}

Achievements
Recognized as top performer in {random.randint(2023, 2025)} hackathon
"""
    return resume


def make_job_description(domain_key: str) -> str:
    domain = DOMAINS[domain_key]
    required = ", ".join(domain["core_skills"])
    preferred = ", ".join(domain["bonus_skills"])
    return f"""We are hiring a {domain['title']}.

About the role: You will work with our engineering team to build and ship product features.

Required Skills: {required}
Preferred Skills: {preferred}

Requirements: 2+ years of experience. Bachelor degree in Computer Science, Engineering, or related field required.
"""


def generate_all(n_per_domain: int = 10):
    cases = []
    idx = 0
    for domain_key in DOMAINS:
        levels = (["strong"] * (n_per_domain // 3) + ["moderate"] * (n_per_domain // 3)
                  + ["weak"] * (n_per_domain - 2 * (n_per_domain // 3)))
        random.shuffle(levels)
        jd_text = make_job_description(domain_key)
        for level in levels:
            resume_text = make_resume(domain_key, level, idx)
            cases.append({
                "id": idx + 1,
                "domain": domain_key,
                "job_title": DOMAINS[domain_key]["title"],
                "expected_match_level": level,
                "resume_text": resume_text,
                "job_description_text": jd_text,
            })
            idx += 1
    return cases


if __name__ == "__main__":
    cases = generate_all(n_per_domain=10)
    with open("data/test_cases/test_cases.json", "w") as f:
        json.dump(cases, f, indent=2)
    print(f"Generated {len(cases)} test cases -> data/test_cases/test_cases.json")
