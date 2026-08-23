"""
Skill taxonomy for the ATS scanner.

The taxonomy is used by both:
- Resume skill extraction
- Job description skill extraction

Aliases normalize different ways of writing the same skill.
"""

# ============================================================
# SKILL TAXONOMY
# ============================================================

SKILL_TAXONOMY = {

    # --------------------------------------------------------
    # Programming
    # --------------------------------------------------------

    "programming_languages": [
        "python",
        "java",
        "javascript",
        "typescript",
        "c++",
        "c#",
        "c",
        "go",
        "golang",
        "rust",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "scala",
        "r",
        "matlab",
        "perl",
        "dart",
        "sql",
        "bash",
        "shell scripting",
    ],

    # --------------------------------------------------------
    # Web / Backend
    # --------------------------------------------------------

    "web_frameworks": [
        "react",
        "angular",
        "vue.js",
        "vue",
        "next.js",
        "nuxt.js",
        "django",
        "flask",
        "fastapi",
        "spring",
        "spring boot",
        "express.js",
        "express",
        "asp.net",
        "ruby on rails",
        "laravel",
        "svelte",
        "node.js",
        "nodejs",
    ],

    # --------------------------------------------------------
    # APIs / Web technologies
    # --------------------------------------------------------

    "web_technologies": [
        "rest api",
        "rest apis",
        "restful api",
        "restful apis",
        "graphql",
        "http",
        "json",
        "api development",
        "github api",
    ],

    # --------------------------------------------------------
    # Machine Learning / AI
    # --------------------------------------------------------

    "ml_ai": [
        "machine learning",
        "deep learning",
        "artificial intelligence",

        "tensorflow",
        "pytorch",
        "keras",
        "scikit-learn",
        "sklearn",

        "nlp",
        "natural language processing",

        "computer vision",
        "opencv",

        "reinforcement learning",
        "neural networks",
        "artificial neural networks",
        "cnn",
        "convolutional neural networks",
        "rnn",
        "lstm",

        "transformers",
        "bert",
        "gpt",
        "huggingface",
        "hugging face",

        "generative ai",
        "gen ai",
        "genai",
        "llm",
        "llms",
        "large language model",
        "large language models",

        "langchain",

        "xgboost",
        "lightgbm",

        "feature engineering",
        "feature scaling",
        "data preprocessing",

        "mlops",
        "model deployment",
        "model training",
        "model evaluation",
    ],

    # --------------------------------------------------------
    # Data Science
    # --------------------------------------------------------

    "data_science": [
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "scipy",
        "data science",
        "statistics",
        "data analysis",
        "exploratory data analysis",
        "eda",
    ],

    # --------------------------------------------------------
    # Databases
    # --------------------------------------------------------

    "databases": [
        "mysql",
        "postgresql",
        "postgres",
        "mongodb",
        "sqlite",
        "oracle",
        "sql server",
        "redis",
        "cassandra",
        "dynamodb",
        "elasticsearch",
        "neo4j",
        "firebase",
        "nosql",
    ],

    # --------------------------------------------------------
    # Cloud / DevOps
    # --------------------------------------------------------

    "cloud_devops": [
        "amazon web services",
        "aws",
        "azure",
        "gcp",
        "google cloud",

        "docker",
        "kubernetes",
        "k8s",

        "jenkins",
        "ci/cd",
        "terraform",
        "ansible",

        "git",
        "github",
        "gitlab",
        "bitbucket",

        "linux",

        "microservices",

        "serverless",
        "cloudformation",
        "nginx",
        "apache",
    ],

    # --------------------------------------------------------
    # Computer Vision / OCR
    # --------------------------------------------------------

    "computer_vision_tools": [
        "yolo",
        "yolov5",
        "yolov8",
        "easyocr",
        "tesseract",
        "ocr",
        "image processing",
        "image preprocessing",
        "object detection",
        "object tracking",
    ],

    # --------------------------------------------------------
    # Development Tools
    # --------------------------------------------------------

    "development_tools": [
        "streamlit",
        "jupyter",
        "jupyter notebook",
        "vs code",
        "visual studio code",
        "google sheets",
        "github api",
    ],

    # --------------------------------------------------------
    # Business / Visualization
    # --------------------------------------------------------

    "business_tools": [
        "excel",
        "powerpoint",
        "tableau",
        "power bi",
        "jira",
        "confluence",
        "salesforce",
        "sap",
        "figma",
        "canva",
        "google analytics",
    ],

    # --------------------------------------------------------
    # Soft Skills
    #
    # Kept separate so they can be treated differently from
    # technical skills later.
    # --------------------------------------------------------

    "soft_skills": [
        "communication",
        "leadership",
        "teamwork",
        "problem solving",
        "critical thinking",
        "time management",
        "adaptability",
        "creativity",
        "collaboration",
        "project management",
        "agile",
        "scrum",
        "presentation",
        "negotiation",
        "mentoring",
        "stakeholder management",
    ],
}


# ============================================================
# ALIASES
# ============================================================

SKILL_ALIASES = {

    # Programming
    "js": "javascript",
    "ts": "typescript",
    "py": "python",

    # ML
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "artificial intelligence",

    # Computer Vision
    "cv": "computer vision",
    "yolo v8": "yolov8",
    "yolo-v8": "yolov8",

    # NLP
    "nlp": "natural language processing",

    # Kubernetes
    "k8s": "kubernetes",

    # Cloud
    "aws": "amazon web services",
    "gcp": "google cloud",

    # Databases
    "postgres": "postgresql",

    # Node
    "node": "node.js",
    "nodejs": "node.js",

    # Vue
    "vue": "vue.js",

    # Scikit-learn
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "scikit-learn": "scikit-learn",

    # REST
    "rest api": "rest api",
    "rest apis": "rest api",
    "restful api": "rest api",
    "restful apis": "rest api",

    # GenAI
    "genai": "generative ai",
    "gen ai": "generative ai",
    "llm": "large language models",
    "llms": "large language models",

    # Hugging Face
    "huggingface": "hugging face",

    # Jupyter
    "jupyter": "jupyter notebook",

    # VS Code
    "visual studio code": "vs code",

    # OCR
    "easy ocr": "easyocr",
    "tesseract ocr": "tesseract",

    # YOLO
    "yolo": "yolo",
    "yolo v5": "yolov5",

    # OOP
    "oop": "object oriented programming",

    # DBMS
    "dbms": "database management systems",
}


# ============================================================
# FLATTEN TAXONOMY
# ============================================================

ALL_SKILLS = sorted(
    {
        skill
        for group in SKILL_TAXONOMY.values()
        for skill in group
    }
)


# ============================================================
# EDUCATION LEVELS
# ============================================================

EDUCATION_LEVELS = {

    # Doctorate
    "phd": 5,
    "doctorate": 5,

    # Master's
    "master": 4,
    "masters": 4,
    "master's": 4,
    "m.tech": 4,
    "mtech": 4,
    "msc": 4,
    "m.sc": 4,
    "mba": 4,
    "ms": 4,
    "m.s": 4,

    # Bachelor's
    "bachelor": 3,
    "bachelors": 3,
    "bachelor's": 3,
    "b.tech": 3,
    "btech": 3,
    "b.e": 3,
    "be": 3,
    "bsc": 3,
    "b.sc": 3,
    "bca": 3,
    "b.com": 3,

    # Diploma
    "diploma": 2,
    "associate": 2,

    # School
    "high school": 1,
    "hsc": 1,
    "senior secondary": 1,
}


# ============================================================
# EDUCATION FIELDS
# ============================================================

DEGREE_FIELDS = [

    "computer science",
    "computer engineering",
    "electronics & computer engineering",
    "electronics and computer engineering",

    "information technology",

    "electronics",
    "electronics engineering",

    "electrical engineering",

    "mechanical engineering",

    "civil engineering",

    "data science",

    "artificial intelligence",

    "artificial intelligence and machine learning",

    "mathematics",

    "statistics",

    "business administration",

    "commerce",

    "economics",
]