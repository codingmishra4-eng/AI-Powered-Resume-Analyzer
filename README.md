# ResumeIQ Enterprise — AI-Powered ATS Resume Analyzer & Job Match Platform

![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/pytest-55%20passed-brightgreen.svg)
![Frontend](https://img.shields.io/badge/frontend-Streamlit%20Dark%20SaaS-indigo.svg)
![Storage](https://img.shields.io/badge/database-SQLite%20Local-slate.svg)
![Release](https://img.shields.io/badge/version-2.0.0%20Enterprise-violet.svg)

**ResumeIQ Enterprise** is a production-oriented, explainable AI-powered resume analysis, ATS optimization, and job-matching platform built with **Python 3.10+**, **Natural Language Processing (NLP)**, and **Streamlit**.

Designed with clean code, modular architecture, and a modern SaaS dark theme (Slate 900 / Indigo accents), ResumeIQ empowers job seekers and engineers to assess their resume health across **three distinct, non-interchangeable scoring dimensions**, optimize content with Google XYZ impact formulas, and export verified ATS-friendly documents in vector PDF and Word (.docx) formats.

---

## 🎯 Three Distinct, Explainable Scoring Models

ResumeIQ strictly distinguishes between three fundamental evaluation metrics:

| Metric | What It Measures | Default Configurable Weights |
| :--- | :--- | :--- |
| **Resume Quality Score (0–100%)** | How well the resume is written, substantiated with numbers, and organized. | Content Completeness (15%), Work Experience & Achievements (25%), Skills & Evidence (20%), Summary Clarity (15%), Grammar & Readability (10%), Structure & Formatting (15%). |
| **ATS Parsing Compatibility (0–100%)** | How reliably commercial Applicant Tracking Systems (e.g. Workday, Taleo, Greenhouse) can extract text, map headings, and parse contact data. | Text Extraction Reliability (25%), Standard Headings (25%), Contact Completeness (20%), Layout & Formatting Risks (20%), File Format & Length (10%). |
| **Job Description Match Score (0–100%)** | How closely candidate skills, experience, and vocabulary align with a specific job posting. *(Shows clear prompt when no JD is supplied).* | Required Technical Skills (45%), Preferred Skills (15%), Semantic TF-IDF Vocabulary (20%), Role & Title Alignment (20%). |

---

## 🌟 Comprehensive Feature Set

### 1. Multi-Format Extraction & Structured Profile
- **PDF Extraction:** Extracts text glyphs using high-performance PyMuPDF (`fitz`).
- **DOCX Extraction:** Parses Microsoft Word paragraphs and tables via `python-docx`.
- **Scanned PDF Detection:** Identifies image-only PDFs lacking embedded text layers and alerts the user to run OCR instead of returning a deceptive score.
- **Editable Structured Preview:** Automatically extracts candidate name, location, email, phone, LinkedIn, GitHub, summary, and work roles, allowing users to correct extraction mistakes before finalizing analysis.

### 2. Dedicated ATS Compatibility Diagnostics
- **Heading Standardization Check:** Verifies standard section headings against industry norms.
- **Format Risk Scanner:** Identifies complex multi-column table artifacts, non-standard graphic glyphs (`■`, `✦`, `★`), and font encoding corruptions.
- **Header Contact Completeness:** Flags missing recruiter links (LinkedIn, GitHub) or missing email/phone.

### 3. Job Description Matching & Keyword Intelligence
- **Requirement Partitioning:** Distinguishes between **Required Qualifications** and **Preferred / Nice-to-Have** competencies.
- **Synonym Expansion:** Recognizes equivalent acronyms and terms (`JS` ↔ `JavaScript`, `K8s` ↔ `Kubernetes`, `AWS` ↔ `Amazon Web Services`, `Postgres` ↔ `PostgreSQL`).
- **Evidence Mapping:** Pinpoints exact sentence snippets in the resume where matched keywords appear.
- **Keyword Stuffing Detection:** Alerts candidates if keywords appear unnaturally often without accompanying action verbs.

### 4. Work Experience & Achievement Audit
- **Quantified Metrics Ratio:** Calculates the percentage of bullet points with measurable impact (numbers, percentages, dollar figures, latency, throughput).
- **Action Verb Audit:** Identifies bullets opening with strong action verbs (*"Architected"*, *"Spearheaded"*, *"Optimized"*) vs passive phrases (*"responsible for"*, *"worked on"*).
- **Weak Bullet Transformer:** Suggests stronger alternatives with Google-standard XYZ framing (*Accomplished [X] by doing [Z] as measured by [Y]*).

### 5. AI Resume Assistant & Optimizer
- **Provider Abstraction:** Configurable server-side integration supporting **Google Gemini API** (`GEMINI_API_KEY`) or **OpenAI API** (`OPENAI_API_KEY`), with a **high-quality deterministic local rule-based engine as the default offline zero-key fallback**.
- **Capabilities:**
  - Professional summary generator tailored to candidate experience and target role.
  - Bullet point enhancer with impact metric placeholders.
  - Contextual score explainer and interactive Q&A assistant.
- **Factuality & Safety:** Prompt injection guards; never fabricates unverified employers, dates, or degrees.

### 6. ATS-Friendly Resume Builder & Multi-Format Export
- **Vector PDF Generator:** Creates clean single-column PDF resumes via PyMuPDF with clickable hyperlinks.
- **Word DOCX Generator:** Generates formatted Microsoft Word (.docx) documents with standard heading styles.
- **Comprehensive Evaluation Report:** Downloadable detailed Markdown audit report.
- **Extractability Self-Test:** Re-parses the generated document in-memory to verify that 100% of the text layer is extractable and readable by an ATS.

### 7. Version History & Snapshot Comparison
- **SQLite Database Persistence:** Parameterized SQL queries preventing injection.
- **Version Tracking:** Save named snapshots (e.g., *v1.0 Baseline*, *v2.0 Targeted for CloudScale*).
- **Side-by-Side Comparison:** Compare Version A vs Version B to track score progression, newly added skills, and removed terms.

---

## 🏗 Modular Project Architecture

```
AI Resume Analyzer/
├── app.py                      # Main Streamlit web application & modern SaaS UI
├── config.py                   # Central configuration, scoring weights, and synonym dictionary
├── requirements.txt            # Project dependencies
├── README.md                   # Project documentation & setup instructions
├── BEGINNER_GUIDE.md           # 15-section pedagogical guide, algorithm deep-dive, viva Q&A
├── .gitignore                  # Git ignore rules for venv, database, and cache
├── analyzer/                   # Core NLP & analysis package
│   ├── __init__.py             # Public package exports
│   ├── resume_parser.py        # PDF, DOCX, TXT parsers & structured entity extractors
│   ├── text_preprocessing.py   # Stopwords, cleaning, tokenization
│   ├── skill_extractor.py      # Skill taxonomy & gap analysis engine
│   ├── similarity.py           # TF-IDF vectorization & cosine similarity
│   ├── recommendations.py      # Rule-based resume improvement engine
│   ├── ats_analyzer.py         # Dedicated ATS Compatibility Analyzer
│   ├── quality_analyzer.py     # Dedicated Resume Quality Analyzer & bullet audit
│   ├── job_matcher.py          # Job Description Matcher, synonyms, evidence mapper
│   ├── ai_assistant.py         # AI Assistant, bullet enhancer, score Q&A
│   └── resume_builder.py       # Vector PDF & DOCX generator, self-test re-parser
├── database/                   # SQLite persistence package
│   ├── __init__.py
│   └── db.py                   # Schema, migrations, CRUD, version snapshots, comparison
├── utils/                      # Helper package
│   ├── __init__.py
│   └── validators.py           # File size/extension checks, JD validation, OCR detector
├── assets/                     # UI styling
│   └── styles.css              # Custom SaaS dark theme stylesheet (Slate 900 / Indigo)
├── sample_data/                # Synthetic test assets
│   ├── sample_resume.txt       # Plaintext sample resume
│   ├── sample_resume.pdf       # Formatted PDF sample resume
│   ├── sample_resume.docx      # Formatted Word sample resume
│   ├── sample_job_description.txt # Target job description
│   └── skills_data.json        # Categorized JSON skills taxonomy
└── tests/                      # Automated test suite (55 passing tests)
    ├── test_validators.py      # Validation & sanitization tests
    ├── test_parser.py          # Document & section extraction tests
    ├── test_skill_extractor.py # Skill pattern & boundary tests
    ├── test_similarity.py      # TF-IDF & cosine similarity tests
    ├── test_recommendations.py # Suggestion rules tests
    ├── test_ats_analyzer.py    # ATS compatibility & layout risk tests
    ├── test_quality_analyzer.py# Quality score, metrics, and action verb tests
    ├── test_job_matcher.py     # JD requirement partition, synonyms, evidence tests
    ├── test_builder_and_assistant.py # PDF/DOCX builder, extractability, AI tests
    ├── test_db.py              # SQLite CRUD, version snapshots, comparison tests
    └── test_integration.py     # End-to-end PDF & DOCX pipeline tests
```

---

## 🚀 Setup & Execution Instructions (Windows / PowerShell)

### 1. Open Terminal and Navigate to the Project
```powershell
cd "c:\Users\kavya\Desktop\AI Resume Analyzer"
```

### 2. Activate the Virtual Environment
```powershell
.venv\Scripts\Activate.ps1
```
*(If PowerShell script execution is restricted on your system, execute: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` before activating).*

### 3. Run the Automated Test Suite (55 Tests)
```powershell
python -m pytest -v
```

### 4. Launch the Web Application
```powershell
streamlit run app.py
```
Open your web browser at:
```
http://localhost:8501
```

---

## 🔒 Security & Privacy Guarantees

1. **100% Local Default:** Zero external API keys required. Resumes never leave your computer unless you explicitly configure an external AI provider.
2. **Safe SQLite Storage:** Stores only numerical scores, timestamps, and extracted skill arrays. **Full resume text is never written to database tables.**
3. **Parameterized SQL:** All database operations in `database/db.py` use `?` placeholders, eliminating SQL injection risks.
4. **Input Size & Type Limits:** File uploads are restricted to `.pdf`, `.docx`, and `.txt` up to 5MB.
5. **No File Execution:** Documents are read strictly as data streams via PyMuPDF/python-docx; uploaded files are never executed.
6. **Full Data Control:** Users can inspect, compare, or permanently delete individual records or wipe the entire history at any time.

---

## 📚 Educational Companion Guide

For a line-by-line explanation of every algorithm, step-by-step mathematical examples of TF-IDF and Cosine Similarity, and 15+ university viva and interview questions with answers, open:
👉 [**BEGINNER_GUIDE.md**](./BEGINNER_GUIDE.md)
