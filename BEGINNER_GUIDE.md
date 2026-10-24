# ResumeIQ — Comprehensive Beginner & Architecture Guide

Welcome to **ResumeIQ**! This guide is written specifically for students, aspiring software engineers, and developers who are new to Python or building full-stack data applications. 

Whether you are studying this project for university coursework, preparing for technical interviews/vivas, or extending the platform with your own custom features, this guide explains every component in clear, practical, beginner-friendly terms.

---

## Table of Contents
1. [What the Project Does](#1-what-the-project-does)
2. [Python Concepts Taught by this Project](#2-python-concepts-taught-by-this-project)
3. [Folder and File Architecture](#3-folder-and-file-architecture)
4. [Execution Flow: From Upload to Match Results](#4-execution-flow-from-upload-to-match-results)
5. [Deep Dive into Important Functions](#5-deep-dive-into-important-functions)
6. [How PDF Text Extraction Works](#6-how-pdf-text-extraction-works)
7. [How TF-IDF Works (With a Step-by-Step Numerical Example)](#7-how-tf-idf-works-with-a-step-by-step-numerical-example)
8. [What Cosine Similarity Means and How It Is Calculated](#8-what-cosine-similarity-means-and-how-it-is-calculated)
9. [How Skill Extraction and Taxonomy Matching Work](#9-how-skill-extraction-and-taxonomy-matching-work)
10. [How SQLite Stores Analysis History Safely](#10-how-sqlite-stores-analysis-history-safely)
11. [How Streamlit Renders the Reactive User Interface](#11-how-streamlit-renders-the-reactive-user-interface)
12. [How Errors and Edge Cases Are Handled](#12-how-errors-and-edge-cases-are-handled)
13. [How to Modify and Extend the Skill Dictionary](#13-how-to-modify-and-extend-the-skill-dictionary)
14. [Common Beginner Mistakes and How to Debug Them](#14-common-beginner-mistakes-and-how-to-debug-them)
15. [Comprehensive Viva and Technical Interview Q&A](#15-comprehensive-viva-and-technical-interview-qa)

---

## 1. What the Project Does

**ResumeIQ** is an offline, AI-powered resume analyzer and job match platform built with Python, Natural Language Processing (NLP), and Streamlit.

When candidates apply for technical jobs, their resumes are typically parsed by an **Applicant Tracking System (ATS)**. Candidates often wonder:
- *Does my resume align with the requirements of this specific job posting?*
- *What critical skills or tools are explicitly required that I didn't mention?*
- *Is my formatting clear, and did I highlight quantifiable results?*

ResumeIQ solves this by:
1. **Extracting text from real files**: Reads `.pdf` (using PyMuPDF), `.docx` (Word), and `.txt` files.
2. **Detecting scanned PDFs**: Warns users if a PDF is an image scan lacking a text stream.
3. **Parsing Resume Sections & Contacts**: Automatically identifies sections like Summary, Work Experience, Skills, Education, and Certifications, as well as email, phone, GitHub, and LinkedIn links.
4. **Extracting Skills with Taxonomy Matching**: Scans both the resume and the job posting using a configurable taxonomy of hundreds of technical and soft skills.
5. **Computing an Explainable Compatibility Score**: Calculates an overall match score combining **TF-IDF Cosine Similarity** (40%) and **Direct Skill Coverage** (60%).
6. **Performing Skill Gap Analysis**: Categorizes skills into *Matched*, *Missing*, and *Additional*, and suggests top learning priorities.
7. **Rule-Based Resume Suggestions**: Provides actionable feedback (e.g., adding quantifiable metrics like percentages and dollar amounts, replacing passive phrasing with strong action verbs).
8. **Local History Persistence**: Saves session records to an embedded SQLite database using parameterized queries, with options to inspect, filter, or delete history.

---

## 2. Python Concepts Taught by this Project

Building this project teaches several foundational and intermediate software development concepts:

| Concept | Where It Is Used | Why It Matters |
| :--- | :--- | :--- |
| **Modular Architecture & Packages** | `analyzer/`, `database/`, `utils/` with `__init__.py` | Prevents messy monolithic scripts; encourages code reuse and separation of concerns. |
| **Object-Oriented Programming (OOP)** | `SkillExtractor` class | Encapsulates state (the taxonomy dictionary and pre-compiled regex patterns) inside an object. |
| **Type Hinting** | `Tuple[bool, str]`, `Dict[str, any]`, `List[str]` | Catches bugs early, clarifies function contracts, and improves IDE auto-completion. |
| **Regular Expressions (`re`)** | Email/phone patterns, section detection, skill boundaries | Essential for unstructured text parsing and string pattern recognition. |
| **File I/O and Streams** | `io.BytesIO`, `open(..., encoding="utf-8")` | Allows reading uploaded files in-memory without saving temporary files to disk. |
| **Natural Language Processing (NLP)** | Tokenization, stopword filtering, n-grams | Core techniques for transforming raw text into mathematical vectors. |
| **Machine Learning / Vector Math** | `TfidfVectorizer`, `cosine_similarity` | Transforms textual documents into vector spaces and measures angular distance. |
| **Relational Database & SQL** | `sqlite3`, parameterized queries `?` | Safe data persistence, prevention of SQL injection attacks, schema design. |
| **Data Visualization** | `plotly.graph_objects`, `plotly.express` | Building interactive gauges, donut charts, and horizontal grouped bar charts. |
| **Automated Testing** | `pytest`, test fixtures (`tmp_path`) | Professional engineering standard for verifying code correctness before deployment. |

---

## 3. Folder and File Architecture

The repository is structured with strict separation of responsibilities:

```
AI Resume Analyzer/
├── app.py                      # Main Streamlit web application & user interface
├── config.py                   # Central configuration (paths, weights, theme colors)
├── requirements.txt            # Python package dependencies
├── README.md                   # Project overview, setup, and feature documentation
├── BEGINNER_GUIDE.md           # This comprehensive educational guide
├── .gitignore                  # Git ignore rules for venv, cache, and local DBs
├── analyzer/                   # Core NLP, parsing, and scoring engine
│   ├── __init__.py             # Exports public functions from the analyzer package
│   ├── resume_parser.py        # PDF, DOCX, TXT extraction and section/contact parsers
│   ├── text_preprocessing.py   # Text normalization, cleaning, tokenization, stopwords
│   ├── skill_extractor.py      # Taxonomy loading, regex compilation, and skill comparison
│   ├── similarity.py           # TF-IDF vectorization and cosine similarity calculations
│   └── recommendations.py      # Rule-based suggestions (metrics, verbs, structure)
├── database/                   # Data storage layer
│   ├── __init__.py             # Exports database operations
│   └── db.py                   # SQLite schema, CRUD operations, parameterized SQL queries
├── utils/                      # Helper utilities
│   ├── __init__.py             # Exports utility helpers
│   └── validators.py           # File size/type validation, JD checks, OCR scan detector
├── assets/                     # Frontend styling
│   └── styles.css              # Custom CSS rules for modern dark-themed SaaS UI
├── sample_data/                # Synthetic test assets
│   ├── sample_resume.txt       # Sample candidate resume in plaintext
│   ├── sample_resume.pdf       # Sample candidate resume in PDF format
│   ├── sample_resume.docx      # Sample candidate resume in Word format
│   ├── sample_job_description.txt # Sample Senior Python Engineer job posting
│   └── skills_data.json        # Categorized taxonomy dictionary of technical skills
└── tests/                      # Automated test suite
    ├── test_validators.py      # Tests for validation and sanitization
    ├── test_parser.py          # Tests for document, section, and contact parsing
    ├── test_skill_extractor.py # Tests for skill detection and boundary rules
    ├── test_similarity.py      # Tests for preprocessing and TF-IDF similarity
    ├── test_recommendations.py # Tests for quantifiable metric detection and advice
    ├── test_db.py              # Tests for SQLite database operations
    └── test_integration.py     # End-to-end full pipeline integration tests
```

---

## 4. Execution Flow: From Upload to Match Results

```
                  ┌────────────────────────────────────────┐
                  │ 1. User Uploads Resume & Pastes Job Desc│
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │ 2. Validation & Security Checks         │
                  │    - Check file extension (.pdf/.docx) │
                  │    - Enforce 5 MB maximum size limit   │
                  │    - Verify job description length     │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │ 3. Document Text Extraction            │
                  │    - PyMuPDF reads PDF text glyphs     │
                  │    - python-docx reads Word XML nodes  │
                  │    - Checks for scanned image PDFs     │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │ 4. Resume Section & Contact Parsing    │
                  │    - Extract email, phone, links       │
                  │    - Segment Experience, Education, etc│
                  └───────────────────┬────────────────────┘
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                     ▼
      ┌─────────────────────────┐           ┌─────────────────────────┐
      │ 5. Skill Extraction     │           │ 6. TF-IDF Preprocessing │
      │    - Scan Resume Skills │           │    - Clean text         │
      │    - Scan JD Skills     │           │    - Remove Stopwords   │
      │    - Compute Gap Matrix │           │    - Fit TF-IDF Matrix  │
      └────────────┬────────────┘           └────────────┬────────────┘
                   │                                     │
                   └──────────────────┬──────────────────┘
                                      ▼
                  ┌────────────────────────────────────────┐
                  │ 7. Composite Compatibility Score        │
                  │    - Skill Match (60% weight)          │
                  │    - TF-IDF Cosine Match (40% weight)  │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │ 8. Rule-Based Recommendations Engine   │
                  │    - Check for quantifiable metrics    │
                  │    - Identify passive verbs            │
                  │    - Flag missing skills & sections    │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │ 9. UI Rendering & Optional SQLite Save │
                  │    - Plotly score gauge & charts       │
                  │    - Skill badges & recommendation list│
                  │    - Save metadata to local DB history │
                  └────────────────────────────────────────┘
```

---

## 5. Deep Dive into Important Functions

### `validate_file_upload(file_name, file_size_bytes)` in `utils/validators.py`
- **What it does:** Ensures the user cannot crash the server by uploading an unhandled format (like `.exe` or `.zip`) or a massive multi-gigabyte file.
- **How it works:** Uses `os.path.splitext()` to inspect the extension and compares against `ALLOWED_EXTENSIONS`. Checks `file_size_bytes > MAX_FILE_SIZE_BYTES` (5MB).

### `extract_text_from_pdf(file_source)` in `analyzer/resume_parser.py`
- **What it does:** Reads raw PDF bytes or file paths, unlocks text streams, and returns the combined text and page count.
- **How it works:** Opens the stream with `pymupdf.open()`. Checks `doc.is_encrypted`. Loops through each page calling `page.get_text("text")`. Calls `detect_scanned_document` to see if the character-per-page ratio is near zero.

### `clean_text(raw_text)` in `analyzer/text_preprocessing.py`
- **What it does:** Prepares unstructured English text for keyword vectorization.
- **Special Logic:** Most naive text cleaners strip out all punctuation, which ruins tech skills like `C++` (becomes `C`), `C#` (becomes `C`), or `.NET` (becomes `NET`). `clean_text` temporarily masks `C++` as `__cplusplus__` and `C#` as `__csharp__` before stripping punctuation, then restores them.

### `extract_skills(text)` in `analyzer/skill_extractor.py`
- **What it does:** Identifies all technical and soft skills present in a text string.
- **Special Logic:** Uses pre-compiled regex patterns with negative lookaround boundaries `rf"(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])"`. This ensures that a word like "Going" or "Good" never falsely matches the programming language "Go".

### `calculate_tfidf_similarity(resume_text, job_description)` in `analyzer/similarity.py`
- **What it does:** Generates TF-IDF vectors for the resume and job posting, calculates cosine similarity, and extracts top shared keywords.
- **Output:** Returns a float between `0.0` and `1.0` representing vocabulary alignment.

### `save_analysis(...)` in `database/db.py`
- **What it does:** Persists analysis metadata and scores to SQLite.
- **Security:** Uses `?` parameter placeholders: `INSERT INTO analyses (...) VALUES (?, ?, ?, ...);`. Never concatenates user strings into SQL queries.

---

## 6. How PDF Text Extraction Works

A PDF (Portable Document Format) is not simply a text file. It is a vector graphic layout language (derived from PostScript).

Inside a PDF, text is stored as a series of instructions:
```
BT
/F1 12 Tf
72 712 Td
(ALEX RIVERA - Software Engineer) Tj
ET
```
- `BT` / `ET`: Begin Text / End Text
- `Tf`: Sets the font and font size
- `Td`: Coordinates on the page (X, Y)
- `Tj`: The actual character glyph string

**PyMuPDF (`fitz`)** parses these low-level operators, decodes the character map (ToUnicode CMap), and stitches the characters into readable lines.

### The "Scanned PDF" Problem:
If someone takes a smartphone photo of a printed resume or scans it as an image without running Optical Character Recognition (OCR), the PDF only contains a bitmap image (`/XObject /Subtype /Image`). There are **no text operators**! Naive parsers return an empty string without explanation.

ResumeIQ solves this by calculating:
$$\text{Chars Per Page} = \frac{\text{Total Characters Extracted}}{\text{Page Count}}$$
If a 2-page document produces fewer than 50 characters, ResumeIQ flags it:
> *"Notice: This PDF appears to be a scanned image or photo without an embedded text layer..."*

---

## 7. How TF-IDF Works (With a Step-by-Step Numerical Example)

**TF-IDF** stands for **Term Frequency – Inverse Document Frequency**. It is one of the most widely used text algorithms in computer science.

### Why not just count word frequency?
If word frequency alone were used, common words like "the", "experience", and "worked" would dominate, drowning out discriminative keywords like "Kubernetes" or "FastAPI".

### The Two Components:

#### 1. Term Frequency (TF)
How frequently a word appears in a specific document:
$$\text{TF}(t, d) = \frac{\text{Count of word } t \text{ in document } d}{\text{Total words in document } d}$$

#### 2. Inverse Document Frequency (IDF)
How rare or informative the word is across the entire corpus:
$$\text{IDF}(t) = \ln\left(\frac{1 + N}{1 + \text{DF}(t)}\right) + 1$$
*(where $N$ is total documents and $\text{DF}(t)$ is number of documents containing term $t$)*

### Small Numerical Example:
Suppose we have 2 small documents:
- **Resume ($D_1$):** `"Python FastAPI Docker"` (3 words)
- **Job Description ($D_2$):** `"Python FastAPI Kubernetes Redis"` (4 words)

Total documents $N = 2$.

| Word | Count in $D_1$ | Count in $D_2$ | $\text{DF}$ (Docs containing word) | $\text{IDF}$ Value |
| :--- | :--- | :--- | :--- | :--- |
| **Python** | 1 | 1 | 2 (Common) | $\ln(3 / 3) + 1 = 1.0$ |
| **FastAPI** | 1 | 1 | 2 (Common) | $\ln(3 / 3) + 1 = 1.0$ |
| **Docker** | 1 | 0 | 1 (Specific to $D_1$) | $\ln(3 / 2) + 1 = 1.405$ |
| **Kubernetes** | 0 | 1 | 1 (Specific to $D_2$) | $\ln(3 / 2) + 1 = 1.405$ |
| **Redis** | 0 | 1 | 1 (Specific to $D_2$) | $\ln(3 / 2) + 1 = 1.405$ |

The vector for each document is computed by multiplying $\text{TF} \times \text{IDF}$.
Notice that shared words ("Python", "FastAPI") match between both vectors, while non-shared words ("Docker", "Kubernetes", "Redis") contribute 0 to the dot product.

---

## 8. What Cosine Similarity Means and How It Is Calculated

Once two documents are converted into numeric TF-IDF vectors ($\vec{A}$ for resume, $\vec{B}$ for job description), we treat them as arrows in an $n$-dimensional space.

**Cosine similarity** measures the **cosine of the angle $\theta$** between the two arrows:

$$\text{Cosine Similarity} = \cos(\theta) = \frac{\vec{A} \cdot \vec{B}}{\|\vec{A}\| \|\vec{B}\|}$$

Where:
- $\vec{A} \cdot \vec{B} = \sum_{i=1}^n A_i B_i$ is the vector dot product (how much the vectors point in the same direction).
- $\|\vec{A}\| = \sqrt{\sum A_i^2}$ is the Euclidean length (magnitude) of vector $A$.
- $\|\vec{B}\| = \sqrt{\sum B_i^2}$ is the Euclidean length (magnitude) of vector $B$.

```
           Vector B (Job Description)
              ^
              |    /
              |   /  Angle θ
              |  /
              | /
              |/--------------> Vector A (Resume)
```

### Why use Cosine Similarity instead of Euclidean Distance?
If a candidate has a 5-page resume and the job description is 1 paragraph, Euclidean distance would penalize the resume simply because it has more total words (larger vector magnitude).
Cosine similarity **normalizes by document length** ($\|\vec{A}\| \|\vec{B}\|$), measuring **direction and topical alignment**, not document length!

- $\cos(0^\circ) = 1.0 \implies$ Identical vocabulary proportions.
- $\cos(90^\circ) = 0.0 \implies$ No shared terms.

---

## 9. How Skill Extraction and Taxonomy Matching Work

Text similarity alone is insufficient: an applicant could write a beautiful essay using similar vocabulary, but lack the specific required programming language or tool.

ResumeIQ implements a **categorized skill taxonomy** in `sample_data/skills_data.json`:
- **Programming Languages:** Python, Java, C++, TypeScript...
- **Web Frameworks:** FastAPI, Django, React, Express...
- **Databases:** PostgreSQL, Redis, MongoDB, SQLite...
- **Cloud & DevOps:** Docker, Kubernetes, AWS, CI/CD...
- **AI & Data Science:** Machine Learning, Pandas, Scikit-Learn...
- **Engineering Practices:** Agile, Microservices, Unit Testing...

### The Skill Gap Algorithm:
Let $S_{\text{resume}}$ be the set of skills detected in the resume, and $S_{\text{job}}$ be the set detected in the job description:
1. **Matched Skills:** $S_{\text{matched}} = S_{\text{resume}} \cap S_{\text{job}}$
2. **Missing Skills:** $S_{\text{missing}} = S_{\text{job}} \setminus S_{\text{resume}}$
3. **Additional Skills:** $S_{\text{extra}} = S_{\text{resume}} \setminus S_{\text{job}}$
4. **Skill Coverage Ratio:**
   $$\text{Coverage} = \frac{|S_{\text{matched}}|}{|S_{\text{job}}|}$$

### Composite Scoring Formula:
$$\text{Overall Score} = (0.40 \times \text{TF-IDF Cosine Score}) + (0.60 \times \text{Skill Coverage Score})$$
This balance ensures candidates with both high technical coverage and strong contextual description score highest.

---

## 10. How SQLite Stores Analysis History Safely

SQLite is an embedded, serverless relational database engine stored as a single file on disk (`database/resume_iq.db`).

### Schema Design:
```sql
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    resume_name TEXT NOT NULL,
    job_title TEXT,
    overall_score REAL NOT NULL,
    tfidf_score REAL NOT NULL,
    skill_score REAL NOT NULL,
    matched_skills TEXT NOT NULL,
    missing_skills TEXT NOT NULL,
    matched_count INTEGER NOT NULL,
    missing_count INTEGER NOT NULL,
    notes TEXT
);
```

### Why We Use Parameterized Queries:
Beginners often write queries using f-strings or string concatenation:
```python
# DANGEROUS! Vulnerable to SQL Injection
cursor.execute(f"INSERT INTO analyses (resume_name) VALUES ('{user_input}');")
```
If `user_input` contains `' OR '1'='1`, an attacker could alter or drop tables.

ResumeIQ strictly uses **parameterized queries**:
```python
# SAFE! The database driver treats inputs purely as literals
cursor.execute("INSERT INTO analyses (resume_name) VALUES (?);", (user_input,))
```

### Privacy Safeguard:
Notice what is NOT in the database: **the full resume text**.
Full resume documents may contain personal home addresses, phone numbers, and candidate names. To protect candidate privacy, ResumeIQ only logs numerical scores, timestamps, and extracted skill arrays.

---

## 11. How Streamlit Renders the Reactive User Interface

Streamlit uses a **declarative, reactive execution model**:
1. When a user interacts with a widget (clicks a button, uploads a file, types text), Streamlit executes the entire `app.py` script from top to bottom.
2. State between reruns is preserved using `st.session_state`:
   - `st.session_state["analysis_result"]`: Stores the current evaluation dictionary.
   - `st.session_state.skill_extractor`: Stores the cached `SkillExtractor` object so regex patterns don't need recompilation on every click.
3. Custom CSS is injected at the top of the script using `st.markdown("<style>...</style>", unsafe_allow_html=True)`.

---

## 12. How Errors and Edge Cases Are Handled

ResumeIQ anticipates common real-world errors:

| Edge Case | How ResumeIQ Handles It |
| :--- | :--- |
| **Corrupted / Empty File** | `validate_file_upload` checks `file_size <= 0` and rejects it before attempting extraction. |
| **Unsupported File Type (e.g. `.exe`, `.png`)** | Validates against `ALLOWED_EXTENSIONS` (`.pdf`, `.docx`, `.txt`) and displays a clear error message. |
| **Password-Protected / Encrypted PDF** | `extract_text_from_pdf` checks `doc.is_encrypted` and returns a friendly prompt to upload an unlocked document. |
| **Scanned Photo PDF** | Detects character-per-page ratio and warns that OCR is needed instead of showing confusing 0% matches. |
| **Extremely Short Job Description** | `validate_job_description` requires at least 10 words, preventing misleading 1-word similarity calculations. |
| **Missing Skill Dictionary File** | Falls back gracefully to `FALLBACK_TAXONOMY` in Python memory if `skills_data.json` is moved or deleted. |

---

## 13. How to Modify and Extend the Skill Dictionary

To add new technical skills or industry domains to ResumeIQ:

### Method 1: Edit `sample_data/skills_data.json`
Open `sample_data/skills_data.json` in VS Code. Simply add your skill to the appropriate category array:
```json
{
  "Cloud & DevOps": [
    "AWS",
    "Docker",
    "Kubernetes",
    "YourNewToolHere"
  ]
}
```

### Method 2: Use the In-App Taxonomy Explorer
1. In the sidebar, select **📚 Skill Taxonomy**.
2. Click **➕ Add Custom Skill to Taxonomy**.
3. Type the skill name, choose a category, and click **Add Skill**. The skill is instantly compiled into active regex memory.

---

## 14. Common Beginner Mistakes and How to Debug Them

### Mistake 1: Running `python app.py` instead of `streamlit run app.py`
- **Symptom:** Warnings about `missing ScriptRunContext` or nothing opening in the browser.
- **Fix:** Streamlit applications must be launched with:
  ```powershell
  streamlit run app.py
  ```

### Mistake 2: Forgetting to activate the virtual environment
- **Symptom:** `ModuleNotFoundError: No module named 'fitz'` or `'streamlit'`.
- **Fix:** In PowerShell, activate your `.venv`:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
  *(If execution policies block scripts, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that session).*

### Mistake 3: Punctuation stripping breaking programming language names
- **Symptom:** `C++` matches as `C`, or `Node.js` gets split into `Node` and `js`.
- **Fix:** Always preserve tech symbols using regex boundaries or temporary token masking before applying lowercase and punctuation sanitization.

---

## 15. Comprehensive Viva and Technical Interview Q&A

Here are questions typically asked in project vivas, college defenses, and software engineering interviews:

### Q1: Why did you choose PyMuPDF instead of PyPDF2 or pdfminer?
> **Answer:** PyMuPDF (`fitz`) is built on MuPDF, a C-based high-performance rendering and document analysis engine. It is significantly faster than pure-Python libraries like PyPDF2, handles complex font encodings and ToUnicode CMaps more reliably, and supports inspection of encrypted files and page metadata.

### Q2: What is the time complexity of TF-IDF vectorization?
> **Answer:** For a vocabulary of size $V$ and a document with $N$ words, computing Term Frequency is $O(N)$. Computing TF-IDF across $D$ documents takes $O(D \cdot \bar{N})$ where $\bar{N}$ is the average document length. Finding cosine similarity between two sparse vectors takes $O(k)$ where $k$ is the number of non-zero shared features.

### Q3: Why does ResumeIQ use a hybrid score instead of relying only on TF-IDF cosine similarity?
> **Answer:** TF-IDF measures statistical word overlap across the entire text. However, job descriptions have many boilerplate sentences ("competitive salary", "equal opportunity", "hybrid office"). If we only used TF-IDF, candidates might match on non-technical words. By incorporating explicit skill taxonomy matching with 60% weight, we ensure that concrete qualifications (languages, databases, frameworks) carry the primary decision weight.

### Q4: How does the application prevent SQL Injection?
> **Answer:** All database write and query operations in `database/db.py` use SQLite parameter placeholders (`?`). The SQLite engine treats user arguments strictly as literal values rather than executable SQL syntax, making injection impossible.

### Q5: What is the difference between text similarity and actual candidate qualification?
> **Answer:** Text similarity measures lexical and semantic alignment between two written documents. It cannot evaluate a candidate's problem-solving ability, code quality, leadership nuance, culture fit, or the actual depth of their experience. ResumeIQ explicitly displays an ethical disclaimer reminding users that the score is a preparation guide, not an automated hiring judgment.

### Q6: How does the application handle scanned resume images?
> **Answer:** Scanned PDFs contain pixel image streams rather than character font glyphs. PyMuPDF extracts 0 characters from them. ResumeIQ detects this by evaluating the extracted character count relative to page count; if fewer than 30 characters per page exist, it triggers a user warning advising OCR conversion rather than returning a deceptive 0% score.
