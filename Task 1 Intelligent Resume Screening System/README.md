# Intelligent Resume Screening System
### InternGrow AI Internship Track — Task 1

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Framework-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![Status](https://img.shields.io/badge/Status-Production--Ready-success.svg)]()

An end-to-end, automated AI-powered recruitment portal that parses candidate resumes (`PDF` and `DOCX`), extracts candidate details and technical skills using boundary-safe regex patterns and taxonomy dictionaries, computes semantic and lexical similarity against target Job Descriptions using `scikit-learn`'s **TF-IDF Vectorizer** and **Cosine Similarity**, performs automated **Skill Gap Analysis**, and ranks candidates on an interactive **Streamlit dashboard** with CSV export capabilities.

---

## 🌟 Key Features

1. **Multi-Format Document Parsing (`src/parser.py`)**:
   - High-fidelity text extraction from both `.pdf` and `.docx` files.
   - Handles multi-page PDFs with stream fallback using `PyPDF2`.
   - Iterates through paragraphs and tables in `.docx` files using `python-docx` to ensure tabulated skills are never lost.
   - Text sanitization: removes null characters, normalizes Unicode whitespaces, and standardizes line breaks.

2. **Technical Skill & Entity Extraction (`src/extractor.py`)**:
   - Broad, categorized taxonomy covering 70+ industry-standard technical skills:
     - **Programming Languages**: Python, Java, C++, C#, Go, Rust, JavaScript, TypeScript, SQL, etc.
     - **AI / ML & Data Science**: Machine Learning, Deep Learning, NLP, Scikit-Learn, PyTorch, TensorFlow, LLMs, LangChain, Pandas, NumPy, etc.
     - **Databases & Big Data**: PostgreSQL, MySQL, MongoDB, Redis, Apache Spark, Kafka, Snowflake, etc.
     - **Cloud & DevOps**: AWS, Azure, GCP, Docker, Kubernetes, CI/CD, Git, Linux, Terraform, etc.
     - **Web & Backend**: React, Next.js, Node.js, Express, FastAPI, Django, Spring Boot, REST APIs, etc.
   - **Boundary-Safe Matching**: Prevents false substring matches (e.g., stops "c" from matching inside "cat" or "go" inside "good").
   - **Candidate Contact Extraction**: Automated extraction of emails, phone numbers, and candidate names via header heuristics and entity models.

3. **TF-IDF Vectorization & Cosine Similarity (`src/matcher.py`)**:
   - Vectorizes job descriptions and candidate resumes using `scikit-learn`'s `TfidfVectorizer` (unigrams + bigrams, English stop-word filtering, sublinear TF scaling).
   - Computes **Cosine Similarity** mapping to a normalized `0.0% - 100.0%` score.
   - **Skill Gap Analysis**: Identifies **Matched Skills**, **Missing Skills**, and calculates a **Skill Match Ratio**.
   - **Composite Match Scoring**: Blends semantic text similarity with strict skill match requirements through configurable weights.

4. **Recruiter Dashboard (`app.py`)**:
   - **Target Job Description Input**: Paste text directly, upload `.txt` / `.pdf` / `.docx` files, or select from built-in role presets (e.g., AI/ML Engineer, Full Stack Developer, Data Analyst).
   - **Multi-File Uploader**: Drag and drop multiple PDF and DOCX resumes simultaneously.
   - **KPI Metrics**: Real-time summary displaying Candidates Screened, Top Match %, Average Score, and Top Applicant.
   - **Candidate Ranking Data Table**: Interactive table with match scores, progress bars, detected skills, and missing skills.
   - **Deep-Dive Candidate Inspector**: Detailed view displaying individual score compositions, emerald/crimson skill badges, and raw extracted text.
   - **CSV Export**: One-click download of the complete ranked evaluation report.

---

## 📁 Project Structure

```
Task 1 Intelligent Resume Screening System/
├── .venv/                         # Python virtual environment
├── requirements.txt               # Project dependencies
├── app.py                         # Streamlit interactive web application
├── README.md                      # Complete system documentation
├── src/
│   ├── __init__.py                # Package exports
│   ├── parser.py                  # Text extraction for PDF and DOCX
│   ├── extractor.py               # Skill extraction & contact info logic
│   └── matcher.py                 # TF-IDF Cosine Similarity & ranking engine
├── sample_data/                   # Demo resumes and job descriptions
│   ├── sample_jd_ai_engineer.txt
│   ├── sample_jd_fullstack.txt
│   └── generate_sample_resumes.py # Helper to create test PDF & DOCX resumes
└── tests/
    ├── __init__.py
    └── test_system.py             # Automated test suite (parser, extractor, matcher)
```

---

## 🚀 Quick Setup & Installation

### 1. Prerequisites
- Python **3.10** or higher installed.

### 2. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

*(Optional) Download spaCy English model for enhanced name entity extraction:*
```bash
python -m spacy download en_core_web_sm
```

---

## 🖥️ Running the Application

Launch the Streamlit web dashboard:
```bash
streamlit run app.py
```

After starting, Streamlit will provide a local URL (typically `http://localhost:8501`). Open it in any modern browser.

### Screening Workflow in 3 Steps:
1. **Provide a Job Description**: Choose a preset (e.g., *AI / Machine Learning Engineer*) or paste your custom job description.
2. **Upload Resumes**: Drag and drop one or multiple `.pdf` or `.docx` candidate resumes (or toggle *"Include Demo Candidates"* in the sidebar for instant verification).
3. **Review & Export**: View candidate rankings, inspect skill gaps, and click **"Download Ranked Results as CSV"**.

---

## 🧪 Running Automated Tests

Run the unit test suite to verify document parsers, skill extraction boundaries, and similarity calculations:

```bash
python -m unittest tests/test_system.py -v
```

---

## 🔬 Scoring Methodology

The screening system computes candidate rankings using a dual-channel evaluation strategy:

$$\text{Composite Score} = (W_{\text{tfidf}} \times \text{TF-IDF Similarity}) + (W_{\text{skill}} \times \text{Skill Match Ratio})$$

1. **TF-IDF Cosine Similarity ($W_{\text{tfidf}} = 60\%$ by default)**:
   - Captures contextual relevance, responsibilities, project scope, and domain phrasing using n-gram term frequencies penalized by inverse document frequencies.
2. **Skill Match Ratio ($W_{\text{skill}} = 40\%$ by default)**:
   - Evaluates mandatory skill fulfillment:
     $$\text{Skill Match Ratio} = \frac{|\text{Candidate Skills} \cap \text{Required JD Skills}|}{|\text{Required JD Skills}|} \times 100$$
3. Both weights can be interactively adjusted in real-time via the dashboard sidebar.

---

## 📄 License
InternGrow Internship AI Track — Task 1: Intelligent Resume Screening System.
