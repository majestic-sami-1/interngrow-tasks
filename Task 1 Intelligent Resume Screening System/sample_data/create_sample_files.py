"""
Utility to generate sample PDF and DOCX resumes for testing.
"""

from pathlib import Path
import docx


def create_minimal_pdf(output_path: Path, title: str, lines: list[str]):
    """
    Generates a valid, syntactically clean PDF 1.4 document without third-party heavy PDF writers.
    """
    # Build text stream
    # Note: escape parentheses in text
    stream_content = ["BT", "/F1 11 Tf", "14.4 TL", "50 740 Td"]
    # Title in bold-like or larger spacing
    stream_content.append(f"({title.replace('(', '[').replace(')', ']')}) Tj")
    stream_content.append("T*")
    stream_content.append("T*")

    for line in lines:
        escaped_line = line.replace("\\", "\\\\").replace("(", "[").replace(")", "]")
        stream_content.append(f"({escaped_line}) Tj")
        stream_content.append("T*")

    stream_content.append("ET")
    stream_data = "\n".join(stream_content).encode("latin-1", errors="replace")

    objects = []
    offsets = []

    # Obj 1: Catalog
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    # Obj 2: Pages
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    # Obj 3: Page
    objects.append(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n")
    # Obj 4: Stream
    stream_header = f"4 0 obj\n<< /Length {len(stream_data)} >>\nstream\n".encode("ascii")
    stream_footer = b"\nendstream\nendobj\n"
    objects.append(stream_header + stream_data + stream_footer)
    # Obj 5: Font
    objects.append(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    # Assemble PDF with valid xref
    pdf_bytes = bytearray(b"%PDF-1.4\n")
    for obj in objects:
        offsets.append(len(pdf_bytes))
        pdf_bytes.extend(obj)

    xref_offset = len(pdf_bytes)
    pdf_bytes.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for offset in offsets:
        pdf_bytes.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    pdf_bytes.extend(f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))

    with open(output_path, "wb") as f:
        f.write(pdf_bytes)


def create_sample_docx(output_path: Path, name: str, email: str, phone: str, summary: str, skills: list[str], experience: list[str]):
    """
    Generates a styled DOCX resume with tables and paragraphs.
    """
    doc = docx.Document()
    doc.add_heading(name, level=0)
    p_contact = doc.add_paragraph(f"Email: {email} | Phone: {phone} | Location: Remote")
    
    doc.add_heading("Professional Summary", level=1)
    doc.add_paragraph(summary)

    doc.add_heading("Technical Skills", level=1)
    # Create skills table
    table = doc.add_table(rows=len(skills), cols=2)
    for i, (cat, sk_list) in enumerate(skills):
        table.rows[i].cells[0].text = cat
        table.rows[i].cells[1].text = sk_list

    doc.add_heading("Work Experience", level=1)
    for exp in experience:
        doc.add_paragraph(exp, style="List Bullet")

    doc.save(str(output_path))


def generate_all_samples():
    sample_dir = Path(__file__).parent

    # 1. Sample AI Resume in DOCX
    docx_path1 = sample_dir / "candidate_sarah_mitchell_ai.docx"
    create_sample_docx(
        output_path=docx_path1,
        name="Dr. Sarah Mitchell",
        email="sarah.mitchell@ai-nexus.io",
        phone="+1-555-019-2834",
        summary="Senior Machine Learning Engineer with 6+ years deploying NLP, Deep Learning, and LLM applications.",
        skills=[
            ("AI & Machine Learning", "Machine Learning, Deep Learning, NLP, Scikit-Learn, PyTorch, TensorFlow, LLMs, LangChain"),
            ("Languages & Databases", "Python, SQL, PostgreSQL, MongoDB, Redis, Apache Spark"),
            ("Cloud & DevOps", "Docker, Kubernetes, AWS, Git, CI/CD, Linux, Unit Testing"),
        ],
        experience=[
            "Lead AI Engineer at NeuroPulse: Designed and scaled enterprise NLP pipelines using PyTorch and Hugging Face.",
            "Deployed microservices using FastAPI, Docker, and Kubernetes on AWS with automated CI/CD.",
            "Built feature stores and ETL jobs utilizing Pandas, NumPy, and Apache Spark.",
        ]
    )
    print(f"Created: {docx_path1.name}")

    # 2. Sample Full-Stack Resume in PDF
    pdf_path1 = sample_dir / "candidate_david_chen_fullstack.pdf"
    create_minimal_pdf(
        output_path=pdf_path1,
        title="David Chen - Full Stack Engineer",
        lines=[
            "Email: david.chen@devmail.io | Phone: +1-415-555-9082",
            "Professional Summary:",
            "Full Stack Software Developer with 5 years building scalable web apps and REST APIs.",
            "Technical Skills:",
            "Languages: JavaScript, TypeScript, Python, HTML/CSS, SQL",
            "Frontend: React, Next.js, Redux",
            "Backend: Node.js, Express, FastAPI, REST APIs",
            "Databases & Cloud: PostgreSQL, MySQL, Redis, AWS, Docker, Git, CI/CD, Linux",
            "Professional Experience:",
            "- Engineered interactive dashboards using React, Next.js, and TypeScript.",
            "- Developed Node.js and Express backend microservices with PostgreSQL.",
            "- Automated containerized releases via Docker, AWS, and Git CI/CD.",
        ]
    )
    print(f"Created: {pdf_path1.name}")

    # 3. Sample Data Analyst Resume in PDF
    pdf_path2 = sample_dir / "candidate_emily_rodriguez_analyst.pdf"
    create_minimal_pdf(
        output_path=pdf_path2,
        title="Emily Rodriguez - Senior Data Analyst",
        lines=[
            "Email: emily.rodriguez@analysthub.net | Phone: +1-312-555-4721",
            "Professional Summary:",
            "Detail-oriented Data Analyst with 4 years translating data into executive business intelligence.",
            "Technical Skills:",
            "Analytics: Data Analysis, Statistical Modeling, Machine Learning, Feature Engineering",
            "Languages & Databases: Python, Pandas, NumPy, SQL, R, PostgreSQL, Snowflake, MySQL",
            "BI & Visualization: Power BI, Tableau, Excel",
            "Tools: Git, Agile / Scrum, Jira",
            "Professional Experience:",
            "- Engineered automated Power BI and Tableau dashboards connected to Snowflake data lakes.",
            "- Conducted exploratory Data Analysis in Python and Pandas uncovering $1.2M in churn risks.",
            "- Authored advanced SQL optimization queries for executive leadership.",
        ]
    )
    print(f"Created: {pdf_path2.name}")


if __name__ == "__main__":
    generate_all_samples()
