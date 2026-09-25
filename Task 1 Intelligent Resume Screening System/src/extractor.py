"""
Information and Skill Extraction Module
Extracts candidate contact details (Name, Email, Phone) and categorized technical skills
using targeted regex patterns, curated taxonomies, and canonical entity normalization.
"""

import re
from typing import Dict, List, Set, Tuple, Optional

# Optional spaCy integration with graceful fallback
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        # Fallback to blank model if en_core_web_sm model weights are not downloaded
        nlp = spacy.blank("en")
except Exception:
    nlp = None


# Comprehensive Skill Taxonomy & Canonical Mapping
# Format: Canonical Name -> List of regex patterns / aliases (case-insensitive)
SKILL_PATTERNS: Dict[str, Dict[str, any]] = {
    # --- Programming Languages ---
    "Python": {"category": "Programming Languages", "patterns": [r"\bpython\b", r"\bpython3\b"]},
    "Java": {"category": "Programming Languages", "patterns": [r"\bjava\b(?!script)"]},
    "JavaScript": {"category": "Programming Languages", "patterns": [r"\bjavascript\b", r"\bjs\b", r"\bes6\b"]},
    "TypeScript": {"category": "Programming Languages", "patterns": [r"\btypescript\b", r"\bts\b"]},
    "C++": {"category": "Programming Languages", "patterns": [r"\bc\+\+\b", r"\bcpp\b"]},
    "C#": {"category": "Programming Languages", "patterns": [r"\bc#\b", r"\bc-sharp\b", r"\bcsharp\b"]},
    "C": {"category": "Programming Languages", "patterns": [r"(?:\bC\b(?=[,\s/|]+(?:C\+\+|Java|Python|Assembly|Embedded)|\s+(?:programming|developer|language)))"]},
    "Go / Golang": {"category": "Programming Languages", "patterns": [r"\bgolang\b", r"\bgo\b(?=\s+(?:developer|programming|code|routine|lang))"]},
    "Rust": {"category": "Programming Languages", "patterns": [r"\brust\b(?:\s+(?:lang|programming|developer))?", r"\brustlang\b"]},
    "R": {"category": "Programming Languages", "patterns": [r"(?:\bR\b(?=[,\s/|]+(?:Python|SQL|SAS|MATLAB)|\s+(?:programming|language|package)))", r"\br-lang\b"]},
    "PHP": {"category": "Programming Languages", "patterns": [r"\bphp\b"]},
    "Ruby": {"category": "Programming Languages", "patterns": [r"\bruby\b", r"\bruby on rails\b"]},
    "Swift": {"category": "Programming Languages", "patterns": [r"\bswift\b"]},
    "Kotlin": {"category": "Programming Languages", "patterns": [r"\bkotlin\b"]},
    "Scala": {"category": "Programming Languages", "patterns": [r"\bscala\b"]},
    "SQL": {"category": "Programming Languages", "patterns": [r"\bsql\b", r"\bstructured query language\b"]},
    "HTML/CSS": {"category": "Programming Languages", "patterns": [r"\bhtml5?\b", r"\bcss3?\b", r"\bsass\b", r"\bscss\b"]},
    "Bash / Shell": {"category": "Programming Languages", "patterns": [r"\bbash\b", r"\bshell script(?:ing)?\b", r"\bpowershell\b"]},

    # --- AI, ML & Data Science ---
    "Machine Learning": {"category": "AI / ML & Data Science", "patterns": [r"\bmachine learning\b", r"\bml\b(?=\s+(?:models?|engineer|algorithms?|pipeline))"]},
    "Deep Learning": {"category": "AI / ML & Data Science", "patterns": [r"\bdeep learning\b", r"\bdl\b(?=\s+(?:models?|engineer|network))"]},
    "Natural Language Processing (NLP)": {"category": "AI / ML & Data Science", "patterns": [r"\bnatural language processing\b", r"\bnlp\b"]},
    "Computer Vision": {"category": "AI / ML & Data Science", "patterns": [r"\bcomputer vision\b", r"\bcv\b(?=\s+(?:algorithms?|engineer|models?))", r"\bimage processing\b"]},
    "Large Language Models (LLMs)": {"category": "AI / ML & Data Science", "patterns": [r"\blarge language models?\b", r"\bllms?\b", r"\bgenerative ai\b", r"\bgenai\b"]},
    "Scikit-Learn": {"category": "AI / ML & Data Science", "patterns": [r"\bscikit[- ]learn\b", r"\bsklearn\b"]},
    "TensorFlow": {"category": "AI / ML & Data Science", "patterns": [r"\btensorflow\b", r"\btf\b(?=\s+(?:keras|models?))"]},
    "PyTorch": {"category": "AI / ML & Data Science", "patterns": [r"\bpytorch\b", r"\btorch\b"]},
    "Keras": {"category": "AI / ML & Data Science", "patterns": [r"\bkeras\b"]},
    "Pandas": {"category": "AI / ML & Data Science", "patterns": [r"\bpandas\b"]},
    "NumPy": {"category": "AI / ML & Data Science", "patterns": [r"\bnumpy\b"]},
    "SciPy": {"category": "AI / ML & Data Science", "patterns": [r"\bscipy\b"]},
    "Hugging Face": {"category": "AI / ML & Data Science", "patterns": [r"\bhugging\s*face\b", r"\btransformers\b"]},
    "LangChain": {"category": "AI / ML & Data Science", "patterns": [r"\blangchain\b", r"\bllamaindex\b"]},
    "OpenCV": {"category": "AI / ML & Data Science", "patterns": [r"\bopencv\b", r"\bcv2\b"]},
    "NLTK": {"category": "AI / ML & Data Science", "patterns": [r"\bnltk\b"]},
    "spaCy": {"category": "AI / ML & Data Science", "patterns": [r"\bspacy\b"]},
    "XGBoost": {"category": "AI / ML & Data Science", "patterns": [r"\bxgboost\b", r"\blightgbm\b", r"\bcatboost\b"]},
    "Data Analysis": {"category": "AI / ML & Data Science", "patterns": [r"\bdata analysis\b", r"\bexploratory data analysis\b", r"\beda\b"]},
    "Feature Engineering": {"category": "AI / ML & Data Science", "patterns": [r"\bfeature engineering\b", r"\bmodel evaluation\b", r"\bhyperparameter\b"]},

    # --- Databases & Big Data ---
    "PostgreSQL": {"category": "Databases & Big Data", "patterns": [r"\bpostgresql\b", r"\bpostgres\b"]},
    "MySQL": {"category": "Databases & Big Data", "patterns": [r"\bmysql\b"]},
    "MongoDB": {"category": "Databases & Big Data", "patterns": [r"\bmongodb\b", r"\bmongo\b"]},
    "Redis": {"category": "Databases & Big Data", "patterns": [r"\bredis\b"]},
    "SQLite": {"category": "Databases & Big Data", "patterns": [r"\bsqlite\b"]},
    "Oracle": {"category": "Databases & Big Data", "patterns": [r"\boracle db\b", r"\boracle database\b"]},
    "Apache Spark": {"category": "Databases & Big Data", "patterns": [r"\bapache spark\b", r"\bpyspark\b", r"\bspark\b(?=\s+(?:streaming|sql|cluster))"]},
    "Apache Kafka": {"category": "Databases & Big Data", "patterns": [r"\bkafka\b", r"\bapache kafka\b"]},
    "Hadoop": {"category": "Databases & Big Data", "patterns": [r"\bhadoop\b", r"\bhdfs\b", r"\bmapreduce\b"]},
    "Snowflake": {"category": "Databases & Big Data", "patterns": [r"\bsnowflake\b"]},
    "Elasticsearch": {"category": "Databases & Big Data", "patterns": [r"\belasticsearch\b", r"\belk stack\b"]},

    # --- Cloud & DevOps ---
    "AWS": {"category": "Cloud & DevOps", "patterns": [r"\baws\b", r"\bamazon web services\b", r"\bec2\b", r"\bs3\b", r"\blambda\b"]},
    "Azure": {"category": "Cloud & DevOps", "patterns": [r"\bazure\b", r"\bmicrosoft azure\b"]},
    "Google Cloud (GCP)": {"category": "Cloud & DevOps", "patterns": [r"\bgcp\b", r"\bgoogle cloud\b", r"\bgoogle cloud platform\b"]},
    "Docker": {"category": "Cloud & DevOps", "patterns": [r"\bdocker\b", r"\bdockerfile\b", r"\bdocker-compose\b"]},
    "Kubernetes": {"category": "Cloud & DevOps", "patterns": [r"\bkubernetes\b", r"\bk8s\b"]},
    "CI/CD": {"category": "Cloud & DevOps", "patterns": [r"\bci/cd\b", r"\bcontinuous integration\b", r"\bcontinuous deployment\b"]},
    "Jenkins": {"category": "Cloud & DevOps", "patterns": [r"\bjenkins\b"]},
    "GitHub Actions": {"category": "Cloud & DevOps", "patterns": [r"\bgithub actions\b", r"\bgitlab ci\b"]},
    "Terraform": {"category": "Cloud & DevOps", "patterns": [r"\bterraform\b"]},
    "Linux": {"category": "Cloud & DevOps", "patterns": [r"\blinux\b", r"\bubuntu\b", r"\bcentos\b", r"\bdebian\b"]},

    # --- Web, Backend & Frameworks ---
    "React": {"category": "Web & Backend", "patterns": [r"\breact\b", r"\breactjs\b", r"\breact\.js\b"]},
    "Next.js": {"category": "Web & Backend", "patterns": [r"\bnext\.?js\b"]},
    "Node.js": {"category": "Web & Backend", "patterns": [r"\bnode\.?js\b", r"\bnodejs\b"]},
    "Express": {"category": "Web & Backend", "patterns": [r"\bexpress\.?js\b", r"\bexpress\b(?=\s+framework)"]},
    "Django": {"category": "Web & Backend", "patterns": [r"\bdjango\b"]},
    "Flask": {"category": "Web & Backend", "patterns": [r"\bflask\b"]},
    "FastAPI": {"category": "Web & Backend", "patterns": [r"\bfastapi\b"]},
    "Spring Boot": {"category": "Web & Backend", "patterns": [r"\bspring boot\b", r"\bspring framework\b"]},
    "GraphQL": {"category": "Web & Backend", "patterns": [r"\bgraphql\b"]},
    "REST APIs": {"category": "Web & Backend", "patterns": [r"\brest\s*apis?\b", r"\brestful\b"]},
    "Streamlit": {"category": "Web & Backend", "patterns": [r"\bstreamlit\b"]},

    # --- Tools, Methodologies & BI ---
    "Git": {"category": "Tools & Methodologies", "patterns": [r"\bgit\b(?!hub|lab)"]},
    "GitHub / GitLab": {"category": "Tools & Methodologies", "patterns": [r"\bgithub\b", r"\bgitlab\b", r"\bbitbucket\b"]},
    "Agile / Scrum": {"category": "Tools & Methodologies", "patterns": [r"\bagile\b", r"\bscrum\b", r"\bkanban\b", r"\bsprints\b"]},
    "Jira": {"category": "Tools & Methodologies", "patterns": [r"\bjira\b"]},
    "Power BI": {"category": "Tools & Methodologies", "patterns": [r"\bpower\s*bi\b"]},
    "Tableau": {"category": "Tools & Methodologies", "patterns": [r"\btableau\b"]},
    "Excel": {"category": "Tools & Methodologies", "patterns": [r"\bexcel\b", r"\bms excel\b", r"\bvlookup\b"]},
    "Unit Testing": {"category": "Tools & Methodologies", "patterns": [r"\bunit test(?:ing)?\b", r"\bpytest\b", r"\bjunit\b", r"\btdd\b"]},
}

# Unique categories for UI filtering and grouping
SKILL_CATEGORIES = sorted(list({meta["category"] for meta in SKILL_PATTERNS.values()}))


def extract_skills(text: str) -> List[str]:
    """
    Scans the given text against pre-compiled regex patterns to identify
    technical skills with boundary protection to prevent false positive substrings.

    Args:
        text: Raw or preprocessed text from resume or job description.

    Returns:
        Sorted list of canonical skill names matched in the text.
    """
    if not text:
        return []

    matched_skills = set()
    lower_text = text.lower()

    for canonical_name, meta in SKILL_PATTERNS.items():
        for pattern in meta["patterns"]:
            if re.search(pattern, lower_text, re.IGNORECASE):
                matched_skills.add(canonical_name)
                break

    return sorted(list(matched_skills))


def categorize_skills(skills: List[str]) -> Dict[str, List[str]]:
    """
    Groups a list of canonical skill names into their respective taxonomy categories.

    Args:
        skills: List of canonical skill names.

    Returns:
        Dict mapping category name to list of matching skills.
    """
    categorized = {cat: [] for cat in SKILL_CATEGORIES}
    for skill in skills:
        if skill in SKILL_PATTERNS:
            cat = SKILL_PATTERNS[skill]["category"]
            categorized[cat].append(skill)
        else:
            categorized.setdefault("Other Skills", []).append(skill)
    # Remove empty categories
    return {k: v for k, v in categorized.items() if v}


def extract_email(text: str) -> Optional[str]:
    """
    Extracts the primary email address from document text using RFC-compliant pattern.
    """
    if not text:
        return None
    email_pattern = r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
    matches = re.findall(email_pattern, text)
    if matches:
        # Return first valid email
        return matches[0].strip()
    return None


def extract_phone(text: str) -> Optional[str]:
    """
    Extracts phone numbers matching international and regional formats.
    """
    if not text:
        return None
    # Matches formats: +1-800-555-1234, (123) 456-7890, +92 300 1234567, 123.456.7890, etc.
    phone_pattern = r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b"
    candidates = re.findall(phone_pattern, text)
    for cand in candidates:
        digits_only = re.sub(r"\D", "", cand)
        # Standard phone numbers have between 10 and 15 digits
        if 10 <= len(digits_only) <= 15:
            return cand.strip()
    return None


def extract_candidate_name(text: str, filename: Optional[str] = None) -> str:
    """
    Infers the candidate name from top lines of the resume text using
    header heuristic filtering and spaCy Named Entity Recognition (NER).
    Falls back to sanitized filename if parsing cannot extract a confident name.
    """
    # 1. Check if spaCy is available and has PERSON entities in the first 400 characters
    if nlp is not None and text:
        intro_text = text[:600]
        try:
            doc = nlp(intro_text)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    clean_ent = ent.text.strip()
                    # Validate length and ensure it's not a common resume header word
                    if 2 <= len(clean_ent.split()) <= 4:
                        lower_ent = clean_ent.lower()
                        if not any(stop in lower_ent for stop in ["resume", "curriculum", "vitae", "summary", "profile", "contact", "experience", "education"]):
                            return clean_ent
        except Exception:
            pass

    # 2. Heuristic fallback: inspect the first 5 non-empty lines
    if text:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        header_blacklist = {
            "resume", "curriculum vitae", "cv", "summary", "professional summary",
            "contact", "education", "experience", "skills", "profile", "objective",
            "personal details", "phone", "email", "linkedin", "github"
        }
        for line in lines[:6]:
            # Skip lines with emails, URLs, or digits
            if "@" in line or "http" in line or "www." in line or any(c.isdigit() for c in line):
                continue
            cleaned = re.sub(r"[^a-zA-Z\s]", "", line).strip()
            words = cleaned.split()
            # Most human names are 2 to 4 words long and don't contain header keywords
            if 2 <= len(words) <= 4:
                if cleaned.lower() not in header_blacklist and not any(w.lower() in header_blacklist for w in words):
                    # Check capitalization
                    return " ".join([w.capitalize() for w in words])

    # 3. Fallback to filename if provided
    if filename:
        clean_name = re.sub(r"\.(pdf|docx|doc|txt)$", "", filename, flags=re.IGNORECASE)
        clean_name = clean_name.replace("_", " ").replace("-", " ")
        # Filter out prefixes like "resume", "cv", "candidate"
        clean_name = re.sub(r"\b(resume|cv|candidate|document)\b", "", clean_name, flags=re.IGNORECASE).strip()
        if clean_name:
            return " ".join([w.capitalize() for w in clean_name.split()])

    return "Candidate"
