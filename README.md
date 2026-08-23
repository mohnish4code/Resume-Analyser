# 🎯 Advanced ATS Resume Scanner System

An AI-powered system that analyzes a candidate's resume against a job description and generates an **explainable ATS compatibility report** — built with FastAPI, scikit-learn, and a rule-based NLP pipeline.

---

## ✨ Features

| Category | What it does |
|---|---|
| **Multi-format parsing** | PDF, DOCX, and TXT resumes |
| **Info extraction** | Contact details, skills, education, experience, projects, certifications, achievements |
| **JD analysis** | Splits **required vs. preferred** skills, minimum experience, minimum education level |
| **Matching engine** | Exact/alias skill match • Fuzzy "partially matched" skills • Keyword presence match • **TF-IDF cosine semantic similarity** |
| **ATS Scoring** | 0–100 overall score, fully explainable weighted breakdown across 5 components |
| **Quality analysis** | Flesch readability, section completeness, grammar/style heuristics (weak phrasing, buzzwords, action verbs, quantified achievements) |
| **Recommendations** | Prioritized, rule-based improvement suggestions |
| **Job-fit suggestions** | Candidate-fit job categories from a skill taxonomy |
| **History** | Every analysis saved to SQLite, queryable via API |
| **Testing** | 50 generated test cases + evaluation script (92% score-band accuracy, deterministic scoring) |

---

## 📁 Project Structure

```
ats_scanner/
├── app/
│   ├── main.py            # FastAPI app + all endpoints
│   ├── parser.py          # PDF/DOCX/TXT text extraction
│   ├── extractor.py       # NLP extraction of resume fields
│   ├── jd_analyzer.py     # Job description parsing
│   ├── matcher.py         # Skill/keyword/semantic matching
│   ├── scorer.py          # Weighted ATS scoring + explainable breakdown
│   ├── quality.py         # Readability / structure / grammar analysis
│   ├── recommender.py     # Recommendations + job category suggestions
│   ├── database.py        # SQLite history storage (SQLAlchemy)
│   └── skills_db.py       # Skill taxonomy, aliases, education levels
├── data/
│   ├── test_cases/
│   │   ├── generate_test_cases.py   # Generates the 50 test cases
│   │   ├── test_cases.json          # The 50 generated cases
│   │   └── evaluation_results.json  # Latest evaluation run output
│   ├── uploads/            # Scratch space for uploaded files
│   └── history/            # SQLite DB file lives here
├── evaluate.py             # Evaluation harness
├── requirements.txt
└── README.md
```

---

## 🚀 Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the server
python3 -m uvicorn app.main:app --reload --port 8000
```

Then open **http://localhost:8000/docs** for the interactive Swagger UI — upload a resume, paste a job description, and hit "Execute" to see the full report without writing any code.

> 💡 Used `python3 -m uvicorn ...` above instead of a bare `uvicorn` command — see [Troubleshooting](#-troubleshooting) if you'd rather fix your PATH.

---

## 🔌 API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/resume/parse` | Upload a resume, get parsed/extracted profile |
| `POST` | `/api/job/analyze` | Analyze a job description (JSON body: `text`, `job_title`) |
| `POST` | `/api/ats/score` | Full ATS report: resume file + job description → score |
| `POST` | `/api/skills/gap` | Skill-gap analysis only |
| `POST` | `/api/recommendations` | Recommendations + assessment + job category suggestions |
| `GET` | `/api/history` | List past analyses (paginated) |
| `GET` | `/api/history/{id}` | Fetch one full past analysis |
| `GET` | `/api/health` | Health check |

### Example: full ATS score

```bash
curl -X POST http://localhost:8000/api/ats/score \
  -F "file=@resume.pdf" \
  -F "job_description=Required Skills: Python, TensorFlow, SQL. 2+ years experience." \
  -F "job_title=ML Engineer"
```

**Response shape:**
```json
{
  "resume_profile": { "contact": {}, "skills": [], "education": [], "experience_years": 2.0 },
  "job_description_profile": { "required_skills": [], "preferred_skills": [] },
  "ats_report": {
    "overall_ats_score": 78.4,
    "skills_match_score": 85.0,
    "experience_match_score": 100.0,
    "education_match_score": 100.0,
    "keyword_match_score": 75.0,
    "semantic_similarity_score": 42.1,
    "matched_skills": [],
    "missing_skills": [],
    "partially_matched_skills": [],
    "score_breakdown": [ { "component": "Skills Match", "weight": 0.35, "score": 85.0, "explanation": "..." } ]
  },
  "quality_report": { "quality_score": 72.6, "readability": {}, "structure": {}, "grammar_style": {} },
  "recommendations": [ { "priority": "high", "category": "Skills Gap", "recommendation": "..." } ],
  "overall_assessment": { "verdict": "Good match — recommend for review..." },
  "suggested_job_categories": [ { "category": "Machine Learning / AI Engineer", "match_score": 66.7 } ],
  "analysis_id": 1
}
```

---

## 🧪 Test Cases & Evaluation

```bash
python data/test_cases/generate_test_cases.py   # regenerate the 50 cases
python evaluate.py                               # run the evaluation
```

The generator covers **5 job domains** (ML engineer, backend, frontend, data analyst, DevOps) × **3 match-quality bands** (strong / moderate / weak fit) × 10 cases per domain = **50 total**.

`evaluate.py` runs every case through the full pipeline and reports:

- **Skill extraction coverage** — average skills found per resume
- **Score-band accuracy** — does the ATS score land in the expected range per match band? **(currently 92%)**
- **Determinism** — identical input always produces identical scores ✅
- **Recommendation quality** — weaker matches receive more high-priority recommendations than strong matches ✅

---

## ⚖️ Scoring Weights

Tunable in `app/scorer.py`:

| Component | Weight |
|---|---|
| Skills Match | 35% |
| Semantic Similarity | 25% |
| Experience Match | 15% |
| Keyword Match | 15% |
| Education Match | 10% |

---

## 🧠 Why TF-IDF instead of a downloaded embedding model?

Semantic similarity uses scikit-learn's **TF-IDF + cosine similarity** rather than a Sentence-Transformers model. This keeps the whole system pip-installable and runnable **fully offline**, with no model downloads — while still being a legitimate, standard semantic similarity technique (bi-gram TF-IDF captures term importance and co-occurrence, not just raw keyword overlap).

If your environment has internet access to a model hub, swapping in `sentence-transformers` embeddings is a **drop-in change** — only `app/matcher.py::semantic_similarity()` needs to change.

---

## 🛠️ Troubleshooting

**`zsh: command not found: uvicorn`**
Pip installed the package, but its script isn't on your PATH. Run it as a module instead:
```bash
python3 -m uvicorn app.main:app --reload --port 8000
```
To fix it permanently, find pip's script directory and add it to PATH:
```bash
python3 -m site --user-base
# add "<that path>/bin" to PATH in ~/.zshrc, then: source ~/.zshrc
```

**`{"detail":"Not Found"}` at the root URL**
There's no route at `/` — only `/api/...` and `/docs`. Go to `http://localhost:8000/docs` instead.

**Port already in use**
Pick a different port: `python3 -m uvicorn app.main:app --reload --port 8001`.

---

## ⚠️ Known Limitations

- **Semantic similarity** is TF-IDF based, not a trained embedding model — good for demonstrating the *concept* of semantic vs. keyword matching, but a transformer embedding model would generalize better to paraphrased text.
- **Grammar checking** is heuristic (weak phrases, buzzwords, action-verb ratio), not a full grammar engine — swapping in `language_tool_python` would need a Java runtime.
- **Name extraction** is a positional heuristic (first title-case line) — works well for standard resume layouts, less reliably for heavily templated PDFs.
# ATSense-Ai
