# ResumeIQ — AI-Powered Resume Analyzer & Job Match Platform

![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/pytest-36%20passed-brightgreen.svg)
![Frontend](https://img.shields.io/badge/frontend-Streamlit%20Dark%20SaaS-indigo.svg)
![Storage](https://img.shields.io/badge/database-SQLite%20Local-slate.svg)

**ResumeIQ** is an explainable, professional-grade resume analysis and job matching platform built with Python, Natural Language Processing (NLP), and Streamlit.

Designed with clean code, beginner-friendly architecture, and a modern SaaS dark theme, ResumeIQ analyzes candidate resumes against job descriptions, pinpoints technical skill gaps, evaluates semantic keyword alignment, and provides practical, rule-based improvement suggestions.

---

## 🌟 Key Features

### 1. Multi-Format Resume Parsing
- **PDF Extraction:** Extracts text glyphs using high-performance PyMuPDF (`fitz`).
- **DOCX Extraction:** Parses Microsoft Word paragraphs and tables via `python-docx`.
- **Plain Text Support:** Decodes `.txt` files with UTF-8 / Latin-1 fallbacks.
- **Scanned PDF Detection:** Automatically identifies image-only PDFs lacking embedded text layers and alerts the user to run OCR instead of silently failing.
- **Section Parsing:** Detects standard resume headings (*Summary, Experience, Skills, Education, Projects, Certifications*).
- **Contact Extraction:** Identifies email, phone, LinkedIn, GitHub, and personal portfolio links.

### 2. Explainable Job Matching & Scoring
- **TF-IDF Vectorization:** Normalizes text, filters stopwords, and computes unigram + bigram TF-IDF representations.
- **Cosine Similarity:** Measures the angular distance and vocabulary alignment between resume and job description.
- **Categorized Skill Taxonomy:** Scans text using a configurable catalog of hundreds of skills across Programming Languages, Frameworks, Cloud/DevOps, Databases, and AI.
- **Hybrid Compatibility Formula:**
  $$\text{Overall Score} = (0.40 \times \text{TF-IDF Cosine Score}) + (0.60 \times \text{Skill Overlap Ratio})$$
- **Ethical Transparency:** Explains the score as a mathematical alignment index rather than a deceptive "AI hiring certainty."

### 3. Interactive Skill Gap Matrix
- **Matched Skills (Green Pills):** Required skills found on the candidate's resume.
- **Missing Skills (Red Pills):** Skills requested in the job description but absent from the resume.
- **Additional Skills (Indigo Pills):** Extra candidate competencies beyond the job post.
- **Priority Learning Recommendations:** Recommends which missing technical skills to acquire or highlight first.
- **Plotly Visualizations:** Interactive gauge meters, donut charts, and domain distribution bar charts.

### 4. Rule-Based Resume Recommendations
- **Measurable Impact:** Flags bullets lacking metrics and suggests framing achievements with quantifiable numbers (percentages, latency, throughput).
- **Action Verbs:** Replaces passive phrases (*"responsible for"*, *"helped with"*) with strong action verbs (*"architected"*, *"optimized"*).
- **Structure Completeness:** Identifies missing standard sections to improve ATS readability.
- **Contact Completeness:** Warns when recruiter reach-out links (LinkedIn, GitHub) are absent.

### 5. Local SQLite Analysis History
- Saves analysis metadata, scores, timestamps, and matched/missing skills locally.
- 100% parameterized SQL queries to prevent SQL injection.
- Zero storage of raw resume text to protect candidate privacy.
- Interactive history view with individual record deletion and clear-all capabilities.

### 6. One-Click Demo Mode
- Instant loading of a realistic sample candidate resume and Senior Python Engineer job description for immediate testing.

---

## 🏗 Modular Project Architecture

```
AI Resume Analyzer/
├── app.py                      # Main Streamlit web application & user interface
├── config.py                   # Central application configuration & theme constants
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation & setup instructions
├── BEGINNER_GUIDE.md           # In-depth educational guide & viva interview prep
├── .gitignore                  # Git ignore rules for venv, database, and cache
├── analyzer/                   # Core NLP & analysis package
│   ├── __init__.py
│   ├── resume_parser.py        # PDF, DOCX, TXT parsers & section/contact extractors
│   ├── text_preprocessing.py   # Stopwords, cleaning, tokenization
│   ├── skill_extractor.py      # Skill taxonomy & gap analysis engine
│   ├── similarity.py           # TF-IDF vectorization & cosine similarity
│   └── recommendations.py      # Rule-based resume improvement engine
├── database/                   # SQLite persistence package
│   ├── __init__.py
│   └── db.py                   # SQLite schema, CRUD operations, parameterized queries
├── utils/                      # Helper package
│   ├── __init__.py
│   └── validators.py           # File size/extension checks, JD validation, OCR detector
├── assets/                     # UI styling
│   └── styles.css              # Custom SaaS dark theme stylesheet
├── sample_data/                # Synthetic test assets
│   ├── sample_resume.txt       # Plaintext sample resume
│   ├── sample_resume.pdf       # Formatted PDF sample resume
│   ├── sample_resume.docx      # Formatted Word sample resume
│   ├── sample_job_description.txt # Target job description
│   └── skills_data.json        # Categorized JSON skills taxonomy
└── tests/                      # Automated test suite (36 passing tests)
    ├── test_validators.py      # Validation & sanitization tests
    ├── test_parser.py          # Document & section extraction tests
    ├── test_skill_extractor.py # Skill pattern & boundary tests
    ├── test_similarity.py      # TF-IDF & cosine similarity tests
    ├── test_recommendations.py # Suggestion rules tests
    ├── test_db.py              # SQLite CRUD & aggregation tests
    └── test_integration.py     # End-to-end PDF & DOCX pipeline tests
```

---

## 🛠 Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Language** | Python 3.10 / 3.11 | Modern typing, pattern matching, and high performance. |
| **User Interface** | Streamlit + Custom CSS | Clean, reactive UI rendered with a modern SaaS slate/charcoal dark theme. |
| **PDF Extraction** | PyMuPDF (`pymupdf`/`fitz`) | High-speed C-based engine supporting font CMaps, encrypted checks, and fast text extraction. |
| **DOCX Support** | `python-docx` | Native Microsoft Word paragraph and table extraction. |
| **NLP & Vectors** | `scikit-learn` & `re` | Production-standard `TfidfVectorizer` and `cosine_similarity`. |
| **Visualizations** | `plotly` | High-definition, responsive charts (gauges, donuts, bar charts). |
| **Data Storage** | SQLite (`sqlite3`) | Embedded, zero-configuration local database using parameterized queries. |
| **Testing** | `pytest` | Comprehensive unit and integration test suite (36 tests). |

---

## 🚀 Setup & Execution Instructions (Windows / PowerShell)

Follow these step-by-step instructions in **Visual Studio Code** or the **Windows PowerShell terminal**.

### 1. Verify Your Python Installation
Open PowerShell and verify Python 3.10 or 3.11 is installed:
```powershell
python --version
```
*(If Python is not recognized, install it from [python.org](https://www.python.org/) and ensure "Add Python to PATH" is checked during installation).*

### 2. Navigate to the Project Folder
```powershell
cd "c:\Users\kavya\Desktop\AI Resume Analyzer"
```

### 3. Create a Virtual Environment
Isolate the project packages from your global Python environment:
```powershell
python -m venv .venv
```

### 4. Activate the Virtual Environment
```powershell
.venv\Scripts\Activate.ps1
```
> **Troubleshooting Note:** If PowerShell shows a script execution error (`PSSecurityException`), run this command in your PowerShell window to permit local scripts:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .venv\Scripts\Activate.ps1
> ```

### 5. Install Dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 6. Run the Automated Test Suite
Verify that all 36 tests pass on your machine:
```powershell
python -m pytest -v
```

### 7. Launch the Application
Run the Streamlit web dashboard:
```powershell
streamlit run app.py
```
Streamlit will automatically open your default web browser to:
```
http://localhost:8501
```

### 8. Deactivate the Virtual Environment
When you are finished using the app, you can shut down the local server by pressing `Ctrl + C` in PowerShell, then run:
```powershell
deactivate
```

---

## 🔒 Security & Privacy Guarantees

1. **100% Local Processing:** ResumeIQ requires **zero external API keys** and makes no cloud network calls during analysis. Resumes never leave your computer.
2. **Safe Database Storage:** SQLite stores only numerical scores, timestamps, and extracted skill arrays. **Full resume text is never written to the database.**
3. **Parameterized SQL:** All database interactions in `database/db.py` use `?` placeholders, eliminating SQL injection risks.
4. **Input Size & Type Limits:** File uploads are restricted to `.pdf`, `.docx`, and `.txt` up to a maximum of 5MB.
5. **No File Execution:** Documents are read strictly as data streams via PyMuPDF/python-docx; uploaded files are never executed.
6. **Full Data Control:** Users can inspect or permanently delete individual analysis records or wipe the entire history at any time.

---

## ⚠️ Known Limitations

- **Image-Only Resumes:** Resumes created as scanned images/photos without an embedded text layer require OCR (Optical Character Recognition). ResumeIQ detects these documents and alerts the user, but does not bundle heavy OCR binaries like Tesseract in this initial version.
- **Complex Multi-Column Layouts:** Unconventional artistic multi-column resumes may sometimes interleave adjacent text blocks. Using standard single- or two-column chronological formats is recommended for both ResumeIQ and real-world ATS software.
- **Single-User Local Version:** This release is architected as a local desktop/workstation tool, not a multi-tenant cloud service with user accounts.

---

## 🗺 Future Improvement Roadmap

- [ ] **Local OCR Integration:** Optional Tesseract OCR sidecar to extract text from scanned image PDFs.
- [ ] **PDF Export of Analysis:** One-click download of a formatted PDF report summarizing match score, skill gaps, and recommendations.
- [ ] **Local Transformer Embeddings:** Optional toggle for offline sentence-transformers (`all-MiniLM-L6-v2`) for deeper contextual understanding alongside TF-IDF.
- [ ] **Multi-Resume Batch Comparison:** Ability to upload 10+ resumes simultaneously and rank candidates against a single job description.

---

## 📚 Educational Companion Guide

For a line-by-line code explanation, step-by-step mathematical examples of TF-IDF and Cosine Similarity, and 15+ university viva/interview questions, read [`BEGINNER_GUIDE.md`](./BEGINNER_GUIDE.md).
