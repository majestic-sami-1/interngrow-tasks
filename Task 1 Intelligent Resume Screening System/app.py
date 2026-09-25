"""
Intelligent Resume Screening System - Streamlit Dashboard
InternGrow AI Track - Task 1

An automated AI-powered recruitment screening portal that extracts candidate
information from resumes (PDF/DOCX), performs skill matching, computes TF-IDF
Cosine Similarity against target Job Descriptions, and ranks candidates with
interactive skill gap analysis and CSV export.
"""

import io
import datetime
from pathlib import Path
import streamlit as st
import pandas as pd

from src.parser import extract_text
from src.extractor import (
    extract_skills,
    extract_email,
    extract_phone,
    extract_candidate_name,
    categorize_skills,
)
from src.matcher import rank_candidates, analyze_skill_gap

# --- Page Configuration ---
st.set_page_config(
    page_title="Intelligent Resume Screening System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom Premium CSS Styling ---
st.markdown("""
<style>
    /* Main container styling */
    .main-header {
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 50%, #06B6D4 100%);
        padding: 2rem 2.5rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3);
    }
    .main-header h1 {
        margin: 0;
        font-weight: 800;
        font-size: 2.2rem;
        letter-spacing: -0.02em;
        color: #ffffff !important;
    }
    .main-header p {
        margin-top: 0.5rem;
        font-size: 1.05rem;
        opacity: 0.92;
        color: #f1f5f9 !important;
    }

    /* Metric Cards */
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #1e293b;
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }

    /* Badge Pills for Skills */
    .skill-pill {
        display: inline-block;
        padding: 0.22rem 0.65rem;
        margin: 0.15rem 0.25rem 0.15rem 0;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 9999px;
        line-height: 1.2;
    }
    .pill-matched {
        background-color: #d1fae5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }
    .pill-missing {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    .pill-neutral {
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #bae6fd;
    }
    .pill-candidate {
        background-color: #f1f5f9;
        color: #334155;
        border: 1px solid #cbd5e1;
    }

    /* Section Cards */
    .content-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Clean divider */
    hr {
        margin: 1.5rem 0;
        border-color: #f1f5f9;
    }
</style>
""", unsafe_allow_html=True)

# --- Sample Presets for Quick Testing ---
SAMPLE_JDS = {
    "AI / Machine Learning Engineer": """We are seeking a high-performing Machine Learning Engineer to architect, build, and deploy end-to-end intelligent systems.
Key Responsibilities:
- Design and implement state-of-the-art Machine Learning, Deep Learning, and NLP models.
- Build production pipelines using Python, PyTorch, TensorFlow, Scikit-Learn, and Pandas.
- Deploy scalable model APIs with Docker, Kubernetes, and FastAPI in AWS or GCP cloud environments.
- Manage data workflows with SQL, PostgreSQL, and Apache Spark.
- Utilize Git, CI/CD automation, and Unit Testing for robust software delivery.
Requirements:
- Bachelor's or Master's in Computer Science, Data Science, or related field.
- Strong proficiency in Python, Machine Learning, Deep Learning, NLP, and Scikit-Learn.
- Experience with Docker, Git, CI/CD, SQL, and REST APIs.""",

    "Full-Stack Web Developer": """We are hiring a versatile Full-Stack Web Developer to develop scalable web applications and cloud services.
Responsibilities:
- Build responsive frontend interfaces using React, Next.js, TypeScript, and HTML/CSS.
- Develop reliable backend microservices with Node.js, Express, Python, or FastAPI.
- Design database schemas and queries with PostgreSQL, MySQL, and MongoDB.
- Containerize and deploy services using Docker, AWS, and Git CI/CD pipelines.
- Collaborate across cross-functional engineering teams using Agile and Scrum.
Qualifications:
- Proficient in JavaScript, TypeScript, React, Node.js, and SQL.
- Hands-on experience with Docker, Git, REST APIs, and Linux.""",

    "Data Analyst / BI Specialist": """Looking for a detail-oriented Data Analyst to extract business insights from complex datasets.
Responsibilities:
- Perform exploratory Data Analysis using Python, Pandas, NumPy, and SQL.
- Build interactive dashboards and reporting systems using Power BI, Tableau, and Excel.
- Query and optimize large datasets across PostgreSQL, Snowflake, or MySQL databases.
- Communicate data-driven recommendations to business stakeholders.
Requirements:
- Proficiency in SQL, Python, Pandas, Data Analysis, Power BI, and Tableau.
- Strong analytical and statistical problem-solving abilities."""
}

# --- Sidebar Configuration ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/resume.png", width=64)
    st.title("Screening Engine")
    st.markdown("**InternGrow AI Track — Task 1**")
    st.caption("Intelligent Resume Screening & Candidate Ranking System")
    st.divider()

    st.subheader("⚙️ Scoring Weights")
    st.markdown("Fine-tune how candidate match scores are calculated:")
    tfidf_weight = st.slider(
        "TF-IDF Cosine Similarity Weight",
        min_value=0.0,
        max_value=1.0,
        value=0.60,
        step=0.05,
        help="Weight assigned to semantic and lexical text similarity between the resume and JD.",
    )
    skill_weight = round(1.0 - tfidf_weight, 2)
    st.info(f"💡 Skill Match Weight auto-balances to: **{int(skill_weight * 100)}%**")

    st.divider()
    st.markdown("### 🎯 Quick Demo Loaders")
    load_sample_candidates = st.checkbox(
        "Include Demo Candidates",
        value=False,
        help="Loads realistic built-in candidate resumes to test the system immediately without manual uploads.",
    )

    st.divider()
    st.caption("Developed with Streamlit, Scikit-Learn, PyPDF2 & Python-docx.")


# --- Main Dashboard Header ---
st.markdown("""
<div class="main-header">
    <h1>📄 Intelligent Resume Screening System</h1>
    <p>Upload job descriptions and candidate resumes to instantly compute semantic TF-IDF Cosine Similarity, perform deep technical skill gap analysis, and rank applicants objectively.</p>
</div>
""", unsafe_allow_html=True)

# --- Layout: Two Top Columns (Job Description & Resume Upload) ---
col_jd, col_resumes = st.columns([1, 1], gap="medium")

# --- 1. Job Description Section ---
with col_jd:
    st.subheader("1️⃣ Target Job Description")
    st.markdown("Paste your target job description, upload a document, or select a preset:")

    # Preset selection
    selected_preset = st.selectbox(
        "Select a Job Description Preset (Optional):",
        ["-- Custom / Paste Below --"] + list(SAMPLE_JDS.keys()),
    )

    initial_text = ""
    if selected_preset != "-- Custom / Paste Below --":
        initial_text = SAMPLE_JDS[selected_preset]

    # File uploader for JD
    uploaded_jd_file = st.file_uploader(
        "Or upload JD file (.txt, .pdf, .docx):",
        type=["txt", "pdf", "docx"],
        key="jd_file_uploader",
    )

    if uploaded_jd_file is not None:
        try:
            initial_text = extract_text(uploaded_jd_file, filename=uploaded_jd_file.name)
            st.success(f"Loaded JD from `{uploaded_jd_file.name}`")
        except Exception as e:
            st.error(f"Error parsing JD file: {e}")

    job_description = st.text_area(
        "Job Description Text:",
        value=initial_text,
        height=260,
        placeholder="Paste full job description including duties, required tech stack, and qualifications...",
        key="jd_text_area",
    )

    # Detect skills in JD in real time
    if job_description.strip():
        jd_detected_skills = extract_skills(job_description)
        with st.expander(f"🔍 Required Skills Detected in JD ({len(jd_detected_skills)})", expanded=True):
            if jd_detected_skills:
                pill_html = "".join([f'<span class="skill-pill pill-neutral">{s}</span>' for s in jd_detected_skills])
                st.markdown(pill_html, unsafe_allow_html=True)
            else:
                st.warning("No technical skills recognized from the taxonomy in this Job Description.")
    else:
        jd_detected_skills = []


# --- 2. Resume Upload Section ---
with col_resumes:
    st.subheader("2️⃣ Candidate Resumes")
    st.markdown("Upload candidate resumes in **PDF** or **DOCX** format:")

    uploaded_resume_files = st.file_uploader(
        "Drag and drop resume files here:",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Upload one or multiple PDF / DOCX resumes to screen.",
        key="resumes_uploader",
    )

    # Built-in demo resumes for immediate evaluation
    demo_candidates = []
    if load_sample_candidates:
        demo_candidates = [
            {
                "name": "Dr. Sarah Mitchell",
                "filename": "sarah_mitchell_ai_lead.docx",
                "email": "sarah.mitchell@email.com",
                "phone": "+1-555-019-2834",
                "text": """Sarah Mitchell, Ph.D. - Senior AI & Machine Learning Engineer
Email: sarah.mitchell@email.com | Phone: +1-555-019-2834
San Francisco, CA | LinkedIn: linkedin.com/in/sarahmitchell-ai

Professional Summary:
Accomplished Machine Learning Engineer with 6+ years designing, scaling, and deploying Deep Learning, Natural Language Processing (NLP), and Generative AI systems in production. Expert in Python, PyTorch, TensorFlow, and Scikit-Learn.

Technical Skills:
- Programming: Python, SQL, C++, Bash / Shell
- Machine Learning & AI: Machine Learning, Deep Learning, NLP, Scikit-Learn, PyTorch, TensorFlow, Keras, Pandas, NumPy, Hugging Face, LLMs, LangChain
- Cloud & DevOps: AWS, Docker, Kubernetes, CI/CD, Git, Linux
- Databases: PostgreSQL, MongoDB, Redis, Apache Spark
- Methodologies: Agile, Scrum, Unit Testing

Experience:
Lead Machine Learning Engineer | NexaAI (2021 - Present)
- Architected enterprise NLP models utilizing Hugging Face Transformers and LangChain, boosting retrieval accuracy by 38%.
- Scaled inference pipelines on AWS with Docker and Kubernetes, reducing latency by 45ms.
- Built data processing pipelines using Apache Spark, Pandas, and PostgreSQL."""
            },
            {
                "name": "David Chen",
                "filename": "david_chen_fullstack.pdf",
                "email": "david.chen@devmail.io",
                "phone": "+1-415-555-9082",
                "text": """David Chen - Senior Full Stack Software Engineer
Contact: david.chen@devmail.io | +1-415-555-9082 | GitHub: github.com/dchen-dev

Summary:
Full Stack Developer with 5 years of experience engineering high-scale responsive web applications, REST APIs, and microservices.

Core Competencies:
- Languages: JavaScript, TypeScript, Python, HTML/CSS, SQL
- Frontend: React, Next.js, Redux, Tailwind
- Backend: Node.js, Express, FastAPI, Django
- Databases: PostgreSQL, MySQL, Redis, MongoDB
- Cloud & Tools: AWS, Docker, Git, CI/CD, GitHub Actions, Linux, Jira, Agile / Scrum

Professional Experience:
Full Stack Developer | CloudScale Solutions (2020 - Present)
- Developed responsive dashboard applications using React, Next.js, and TypeScript.
- Built scalable backend microservices with Node.js and FastAPI, integrated with PostgreSQL and Redis.
- Implemented automated CI/CD deployment pipelines using Docker and GitHub Actions on AWS."""
            },
            {
                "name": "Emily Rodriguez",
                "filename": "emily_rodriguez_data_analyst.pdf",
                "email": "emily.rodriguez@analysthub.net",
                "phone": "+1-312-555-4721",
                "text": """Emily Rodriguez - Data Analyst & BI Specialist
Email: emily.rodriguez@analysthub.net | Phone: +1-312-555-4721 | Chicago, IL

Professional Profile:
Detail-oriented Data Analyst with 4 years translating complex operational data into actionable business intelligence dashboards and executive reports.

Technical Skills:
- Analytics: Data Analysis, Statistical Modeling, Machine Learning, Feature Engineering
- Programming & Libraries: Python, Pandas, NumPy, SQL, R
- Visualization & BI: Power BI, Tableau, Excel
- Databases: PostgreSQL, MySQL, Snowflake, SQLite
- Workflow: Git, Agile / Scrum, Jira

Work History:
Senior Data Analyst | MetricWorks Inc (2021 - Present)
- Engineered automated Tableau and Power BI executive dashboards connecting to Snowflake and PostgreSQL data lakes.
- Leveraged Python and Pandas for statistical customer segmentation, identifying $1.2M in recurring churn risks.
- Authored complex SQL queries for executive reporting."""
            },
            {
                "name": "Michael Taylor",
                "filename": "michael_taylor_junior.docx",
                "email": "mtaylor.dev@outlook.com",
                "phone": "+1-206-555-8831",
                "text": """Michael Taylor - Junior Software Developer
Email: mtaylor.dev@outlook.com | Phone: +1-206-555-8831

Objective:
Motivated junior software developer seeking an entry-level position to apply academic programming skills in a fast-paced environment.

Skills:
- Languages: Java, Python, HTML/CSS
- Concepts: Object-Oriented Programming, Data Structures, Git
- Web: Basic Flask, REST APIs
- Tools: VS Code, Git, GitHub

Education:
B.S. in Information Systems | State University (Graduated 2023)"""
            }
        ]

    # Process and parse resumes
    candidate_records = []

    # 1. Parse uploaded files
    if uploaded_resume_files:
        st.write(f"📁 **{len(uploaded_resume_files)}** file(s) uploaded:")
        for uploaded_file in uploaded_resume_files:
            try:
                extracted_text = extract_text(uploaded_file, filename=uploaded_file.name)
                candidate_name = extract_candidate_name(extracted_text, filename=uploaded_file.name)
                email = extract_email(extracted_text)
                phone = extract_phone(extracted_text)
                skills = extract_skills(extracted_text)

                candidate_records.append({
                    "name": candidate_name,
                    "filename": uploaded_file.name,
                    "text": extracted_text,
                    "email": email,
                    "phone": phone,
                    "skills": skills,
                })
            except Exception as parse_err:
                st.error(f"Failed to parse `{uploaded_file.name}`: {parse_err}")

    # 2. Add demo candidates if checked
    if load_sample_candidates:
        for demo in demo_candidates:
            skills = extract_skills(demo["text"])
            candidate_records.append({
                "name": demo["name"],
                "filename": demo["filename"] + " (Demo)",
                "text": demo["text"],
                "email": demo["email"],
                "phone": demo["phone"],
                "skills": skills,
            })

    if candidate_records:
        st.success(f"✅ Successfully loaded **{len(candidate_records)}** candidate resume(s).")
    else:
        st.info("👆 Please upload candidate resumes or check 'Include Demo Candidates' in the sidebar.")


st.divider()

# --- 3. Screening & Ranking Evaluation ---
if not job_description.strip():
    st.warning("⚠️ Please provide a Job Description above to begin screening and ranking candidates.")
elif not candidate_records:
    st.warning("⚠️ Please upload at least one candidate resume (PDF or DOCX) to screen against the Job Description.")
else:
    # Run matching engine
    with st.spinner("Analyzing candidate resumes, vectorizing texts, and computing match metrics..."):
        ranking_df = rank_candidates(
            job_description=job_description,
            candidates=candidate_records,
            tfidf_weight=tfidf_weight,
            skill_weight=skill_weight,
        )

    # --- Top KPI Summary Metrics ---
    st.subheader("📊 Screening Summary & Key Metrics")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    total_candidates = len(ranking_df)
    top_score = ranking_df["Match Score (%)"].max() if not ranking_df.empty else 0.0
    avg_score = round(ranking_df["Match Score (%)"].mean(), 1) if not ranking_df.empty else 0.0
    top_candidate = ranking_df.iloc[0]["Candidate Name"] if not ranking_df.empty else "N/A"

    with kpi_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_candidates}</div>
            <div class="metric-label">Candidates Screened</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #059669;">{top_score}%</div>
            <div class="metric-label">Top Match Score</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #2563eb;">{avg_score}%</div>
            <div class="metric-label">Average Match Score</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size: 1.25rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{top_candidate}</div>
            <div class="metric-label">🏆 Top Ranked Candidate</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 4. Candidate Ranking Table ---
    st.subheader("📋 Candidate Rankings & Evaluation Table")
    st.markdown("Review ranked candidates, their match scores, detected skills, and missing skills:")

    # Prepare display table
    display_cols = [
        "Rank",
        "Candidate Name",
        "Match Score (%)",
        "TF-IDF Similarity (%)",
        "Skill Match (%)",
        "Matched Skills",
        "Missing Skills",
        "Email",
        "Phone",
        "File Name",
    ]
    display_df = ranking_df[display_cols]

    # Format numeric columns for clean viewing
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", format="#%d", width="small"),
            "Match Score (%)": st.column_config.ProgressColumn(
                "Match Score (%)",
                format="%.1f%%",
                min_value=0,
                max_value=100,
                width="medium",
            ),
            "TF-IDF Similarity (%)": st.column_config.NumberColumn(
                "TF-IDF Similarity", format="%.1f%%", width="small"
            ),
            "Skill Match (%)": st.column_config.NumberColumn(
                "Skill Match", format="%.1f%%", width="small"
            ),
            "Matched Skills": st.column_config.TextColumn("Matched Skills", width="large"),
            "Missing Skills": st.column_config.TextColumn("Missing Skills", width="large"),
        },
    )

    # --- 5. Export Report ---
    col_dl1, col_dl2 = st.columns([1, 2])
    with col_dl1:
        # Create CSV export buffer
        export_df = ranking_df.copy()
        export_df["Screening Timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Drop raw text or complex list columns from CSV export
        export_csv_cols = [
            "Rank", "Candidate Name", "Match Score (%)", "TF-IDF Similarity (%)",
            "Skill Match (%)", "Matched Skills", "Missing Skills", "Detected Skills",
            "Email", "Phone", "File Name", "Screening Timestamp"
        ]
        csv_data = export_df[export_csv_cols].to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 Download Ranked Results as CSV",
            data=csv_data,
            file_name=f"resume_screening_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()

    # --- 6. Candidate Deep Dive & Skill Gap Analysis ---
    st.subheader("🔍 Candidate Deep Dive & Skill Gap Explorer")
    st.markdown("Select an individual candidate to inspect their detailed skill breakdown and raw resume text:")

    candidate_options = ranking_df["Candidate Name"].tolist()
    selected_candidate_name = st.selectbox("Select Candidate:", candidate_options)

    if selected_candidate_name:
        cand_row = ranking_df[ranking_df["Candidate Name"] == selected_candidate_name].iloc[0]

        detail_col1, detail_col2 = st.columns([1, 1], gap="medium")

        with detail_col1:
            st.markdown(f"### Profile: **{cand_row['Candidate Name']}**")
            st.markdown(f"- 📁 **File:** `{cand_row['File Name']}`")
            st.markdown(f"- 📧 **Email:** `{cand_row['Email']}`")
            st.markdown(f"- 📱 **Phone:** `{cand_row['Phone']}`")
            st.markdown(f"- 🏅 **Rank:** #{cand_row['Rank']} of {len(ranking_df)}")

            st.markdown("#### Score Composition")
            st.metric("Composite Match Score", f"{cand_row['Match Score (%)']}%")
            st.write(f"• **TF-IDF Semantic Similarity:** `{cand_row['TF-IDF Similarity (%)']}%` (Weight: {int(tfidf_weight*100)}%)")
            st.write(f"• **Skill Match Ratio:** `{cand_row['Skill Match (%)']}%` (Weight: {int(skill_weight*100)}%)")

        with detail_col2:
            st.markdown("### Skill Match vs Job Description")

            # Matched Skills
            matched_list = cand_row["Matched Skills List"]
            st.markdown(f"**✅ Matched Skills ({len(matched_list)}):**")
            if matched_list:
                pills = "".join([f'<span class="skill-pill pill-matched">{s}</span>' for s in matched_list])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.write("None of the skills required in the JD were detected.")

            st.markdown("<br>", unsafe_allow_html=True)

            # Missing Skills
            missing_list = cand_row["Missing Skills List"]
            st.markdown(f"**❌ Missing Required Skills ({len(missing_list)}):**")
            if missing_list:
                pills = "".join([f'<span class="skill-pill pill-missing">{s}</span>' for s in missing_list])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.success("Candidate covers 100% of the skills required in the JD!")

            st.markdown("<br>", unsafe_allow_html=True)

            # All Detected Candidate Skills
            all_detected = cand_row["Detected Skills List"]
            st.markdown(f"**📌 All Skills Detected on Candidate ({len(all_detected)}):**")
            if all_detected:
                pills = "".join([f'<span class="skill-pill pill-candidate">{s}</span>' for s in all_detected])
                st.markdown(pills, unsafe_allow_html=True)

        with st.expander(f"📄 View Extracted Text for {selected_candidate_name}", expanded=False):
            st.text_area("Extracted Resume Content:", value=cand_row["Raw Text"], height=300, disabled=True)

st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption("InternGrow AI Track • Task 1: Intelligent Resume Screening System")
