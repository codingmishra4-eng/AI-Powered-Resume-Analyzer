"""
ResumeIQ — AI-Powered Resume Analyzer & Job Match Platform
=========================================================
Main Streamlit Application
A modern, dark-themed SaaS dashboard for resume parsing, job matching,
skill gap analysis, and explainable recommendations.
"""

import io
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Application configuration
from config import (
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    CSS_PATH,
    DATA_DIR,
    DB_PATH,
    THEME_COLORS,
)

# Analyzer engine modules
from analyzer.resume_parser import (
    extract_contact_info,
    extract_text_from_file,
    parse_resume_sections,
)
from analyzer.skill_extractor import SkillExtractor
from analyzer.similarity import calculate_similarity, compute_match_details
from analyzer.recommendations import generate_recommendations

# Database persistence modules
from database.db import (
    clear_all_analyses,
    delete_analysis,
    get_all_analyses,
    get_analysis_by_id,
    get_history_summary_stats,
    init_db,
    save_analysis,
)

# Input validators
from utils.validators import (
    detect_scanned_document,
    sanitize_text,
    validate_file_upload,
    validate_job_description,
)

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title=f"{APP_NAME} — AI Resume Analyzer & Job Match",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Custom CSS Injector
# -----------------------------------------------------------------------------
def load_custom_css():
    """Injects custom SaaS dark theme styles."""
    if os.path.exists(CSS_PATH):
        try:
            with open(CSS_PATH, "r", encoding="utf-8") as f:
                css_content = f.read()
                st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        except Exception as exc:
            st.warning(f"Could not load custom styles: {exc}")


load_custom_css()

# Initialize Database
init_db(DB_PATH)

# Initialize Skill Extractor (cached in session state for efficiency)
if "skill_extractor" not in st.session_state:
    st.session_state.skill_extractor = SkillExtractor()


# -----------------------------------------------------------------------------
# Visualization Helpers (Plotly Dark Theme)
# -----------------------------------------------------------------------------
def create_score_gauge(score: float, title: str = "Overall Match Score") -> go.Figure:
    """
    Creates a modern circular gauge chart indicating match score.
    """
    if score >= 75:
        bar_color = THEME_COLORS["success"]
    elif score >= 50:
        bar_color = THEME_COLORS["warning"]
    else:
        bar_color = THEME_COLORS["danger"]

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "%", "font": {"size": 38, "color": THEME_COLORS["text_primary"]}},
            title={"text": title, "font": {"size": 16, "color": THEME_COLORS["text_secondary"]}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": THEME_COLORS["card_border"]},
                "bar": {"color": bar_color, "thickness": 0.28},
                "bgcolor": "#0F172A",
                "borderwidth": 1,
                "bordercolor": THEME_COLORS["card_border"],
                "steps": [
                    {"range": [0, 50], "color": "rgba(239, 68, 68, 0.08)"},
                    {"range": [50, 75], "color": "rgba(245, 158, 11, 0.08)"},
                    {"range": [75, 100], "color": "rgba(16, 185, 129, 0.08)"},
                ],
            },
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=25, r=25, t=40, b=25),
        height=220,
    )
    return fig


def create_skill_breakdown_chart(matched_count: int, missing_count: int, extra_count: int) -> go.Figure:
    """
    Creates a clean donut chart displaying the proportions of matched vs missing skills.
    """
    labels = ["Matched Skills", "Missing Skills", "Additional Skills"]
    values = [matched_count, missing_count, extra_count]
    colors = [THEME_COLORS["success"], THEME_COLORS["danger"], THEME_COLORS["accent_primary"]]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors, line=dict(color="#0F172A", width=2)),
                textinfo="label+value",
                hoverinfo="label+percent+value",
                textfont=dict(color="#F8FAFC", size=13),
            )
        ]
    )

    fig.update_layout(
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
        height=220,
    )
    return fig


def create_category_skill_bar(by_category_resume: Dict[str, List[str]], by_category_jd: Dict[str, List[str]]) -> go.Figure:
    """
    Creates a grouped horizontal bar chart comparing skill counts by domain.
    """
    all_categories = sorted(list(set(list(by_category_resume.keys()) + list(by_category_jd.keys()))))
    if not all_categories:
        all_categories = ["General Technical"]

    resume_counts = [len(by_category_resume.get(cat, [])) for cat in all_categories]
    jd_counts = [len(by_category_jd.get(cat, [])) for cat in all_categories]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=all_categories,
            x=resume_counts,
            name="Resume Skills",
            orientation="h",
            marker=dict(color=THEME_COLORS["accent_primary"]),
        )
    )
    fig.add_trace(
        go.Bar(
            y=all_categories,
            x=jd_counts,
            name="Job Requirements",
            orientation="h",
            marker=dict(color=THEME_COLORS["secondary_accent"] if "secondary_accent" in THEME_COLORS else "#38BDF8"),
        )
    )

    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=THEME_COLORS["text_secondary"]),
        margin=dict(l=10, r=20, t=20, b=20),
        height=260,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor="#334155", title="Count of Skills"),
        yaxis=dict(gridcolor="#1E293B"),
    )
    return fig


# -----------------------------------------------------------------------------
# Sample Data Helpers
# -----------------------------------------------------------------------------
def load_sample_resume_content() -> str:
    sample_file = DATA_DIR / "sample_resume.txt"
    if os.path.exists(sample_file):
        with open(sample_file, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def load_sample_jd_content() -> str:
    sample_file = DATA_DIR / "sample_job_description.txt"
    if os.path.exists(sample_file):
        with open(sample_file, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# -----------------------------------------------------------------------------
# Sidebar Navigation & Settings
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 10px 0 20px 0;">
            <div class="brand-badge">Engine v{APP_VERSION}</div>
            <h2 style="margin: 0; font-size: 1.6rem; color: #F8FAFC;">🎯 {APP_NAME}</h2>
            <p style="font-size: 0.85rem; color: #94A3B8; margin-top: 4px;">{APP_TAGLINE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    menu_choice = st.radio(
        "Navigation",
        [
            "⚡ Match & Analyze",
            "📊 Analysis History",
            "📚 Skill Taxonomy",
            "📖 How It Works",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 0.8rem; color: #94A3B8; line-height: 1.4;">
            <strong style="color: #F8FAFC;">🔒 Privacy & Storage:</strong><br>
            All processing runs 100% locally on your machine.
            Full resume text is never transmitted to external APIs or stored in database logs.
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Page 1: Match & Analyze (Main Dashboard)
# -----------------------------------------------------------------------------
if menu_choice == "⚡ Match & Analyze":
    # Top stats bar
    stats = get_history_summary_stats(DB_PATH)
    extractor = st.session_state.skill_extractor
    total_tax_skills = sum(len(skills) for skills in extractor.taxonomy.values())

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Total Analyses</div>
                <div class="stat-value">{stats['total_analyses']}</div>
                <div class="stat-subtext">Recorded locally</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_s2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Average Match</div>
                <div class="stat-value">{stats['avg_score']}%</div>
                <div class="stat-subtext">Across historical runs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_s3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Highest Score</div>
                <div class="stat-value">{stats['max_score']}%</div>
                <div class="stat-subtext">Top candidate alignment</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_s4:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Recognized Skills</div>
                <div class="stat-value">{total_tax_skills}</div>
                <div class="stat-subtext">In taxonomy dictionary</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Demo mode one-click pre-fill
    col_demo, col_clear = st.columns([4, 1])
    with col_demo:
        if st.button("🚀 Load Fictional Sample Resume & Job Description", type="secondary"):
            st.session_state["demo_resume_text"] = load_sample_resume_content()
            st.session_state["demo_jd_text"] = load_sample_jd_content()
            st.session_state["demo_file_name"] = "Alex_Rivera_Sample_Resume.txt"
            st.session_state["job_title_input"] = "Senior Python Backend Engineer"
            st.success("Sample data loaded! Click 'Analyze Resume & Job Match' below to evaluate.")

    # Two column layout: Left = Resume, Right = Job Description
    col_left, col_right = st.columns([1, 1], gap="medium")

    # ----- Left Column: Resume Upload -----
    with col_left:
        st.markdown("### 📄 1. Candidate Resume")

        uploaded_file = st.file_uploader(
            "Upload Resume (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            help="Maximum file size: 5MB. Scanned image PDFs are flagged for OCR.",
        )

        resume_text = ""
        resume_name = "Untitled Resume"
        is_scanned_flag = False
        scan_message = ""

        # Check if user uploaded a file
        if uploaded_file is not None:
            resume_name = uploaded_file.name
            file_bytes = uploaded_file.getvalue()
            is_valid, err_msg = validate_file_upload(resume_name, len(file_bytes))

            if not is_valid:
                st.error(f"Upload Error: {err_msg}")
            else:
                extracted, pages, warning_msg = extract_text_from_file(file_bytes, resume_name)
                if warning_msg and "Notice: This PDF appears to be a scanned" in warning_msg:
                    st.warning(warning_msg)
                    is_scanned_flag = True
                    scan_message = warning_msg
                elif warning_msg:
                    st.error(warning_msg)
                
                resume_text = extracted
                st.session_state["current_resume_text"] = resume_text
                st.session_state["current_resume_name"] = resume_name

        # Fallback to demo resume if loaded and no file uploaded
        elif "demo_resume_text" in st.session_state and st.session_state["demo_resume_text"]:
            resume_text = st.session_state["demo_resume_text"]
            resume_name = st.session_state.get("demo_file_name", "Sample_Resume.txt")
            st.info(f"Using pre-loaded demo resume: **{resume_name}**")

        # Display resume summary if text is available
        if resume_text:
            word_count = len(resume_text.split())
            st.caption(f"✓ Extracted {len(resume_text):,} characters ({word_count:,} words) from `{resume_name}`")

            # Extract Contact Information
            contact_data = extract_contact_info(resume_text)
            st.markdown(
                f"""
                <div style="background: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; font-size: 0.85rem;">
                    <strong>Contact Indicators:</strong><br>
                    📧 Email: <code>{contact_data['email'] or 'Not Detected'}</code> |
                    📞 Phone: <code>{contact_data['phone'] or 'Not Detected'}</code><br>
                    🔗 LinkedIn: <code>{contact_data['linkedin'] or 'Not Detected'}</code> |
                    💻 GitHub: <code>{contact_data['github'] or 'Not Detected'}</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander("👁 View Extracted Resume Text"):
                st.text_area("Extracted Resume Content", resume_text, height=220, disabled=True)

    # ----- Right Column: Job Description -----
    with col_right:
        st.markdown("### 📋 2. Target Job Description")

        default_title = st.session_state.get("job_title_input", "")
        job_title = st.text_input(
            "Target Job Title (Optional)",
            value=default_title,
            placeholder="e.g. Senior Python Backend Engineer",
        )

        default_jd = st.session_state.get("demo_jd_text", "")
        job_desc_input = st.text_area(
            "Paste Job Description / Requirements",
            value=default_jd,
            height=260,
            placeholder="Paste the job responsibilities, required qualifications, and tech stack here...",
        )

        jd_words = len(job_desc_input.split())
        st.caption(f"Job Description length: {len(job_desc_input):,} characters ({jd_words} words)")

    # -------------------------------------------------------------------------
    # Analysis Trigger Button
    # -------------------------------------------------------------------------
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    analyze_btn = st.button("⚡ Analyze Resume & Job Match", type="primary", use_container_width=True)

    if analyze_btn:
        if not resume_text or not resume_text.strip():
            st.error("Please upload a resume (PDF, DOCX, TXT) or load the sample resume first.")
        else:
            is_jd_valid, jd_err = validate_job_description(job_desc_input)
            if not is_jd_valid:
                st.error(f"Job Description Notice: {jd_err}")
            else:
                with st.spinner("Analyzing semantics, matching skills, and compiling recommendations..."):
                    # 1. Skill Extraction
                    resume_skills_data = extractor.extract_skills(resume_text)
                    jd_skills_data = extractor.extract_skills(job_desc_input)

                    # 2. Skill Comparison
                    skill_comp = extractor.compare_skills(
                        resume_skills_data["all_skills"],
                        jd_skills_data["all_skills"]
                    )

                    # 3. Text Preprocessing, TF-IDF and Composite Matching
                    match_details = compute_match_details(
                        resume_text,
                        job_desc_input,
                        skill_comp
                    )

                    # 4. Resume Section Parsing
                    parsed_sections = parse_resume_sections(resume_text)
                    contact_info = extract_contact_info(resume_text)

                    # 5. Rule-Based Recommendations
                    recommendations = generate_recommendations(
                        resume_text,
                        parsed_sections,
                        contact_info,
                        skill_comp
                    )

                    # Store results in session state
                    st.session_state["analysis_result"] = {
                        "resume_name": resume_name,
                        "job_title": job_title or "Target Position",
                        "resume_text": resume_text,
                        "job_desc": job_desc_input,
                        "match_details": match_details,
                        "skill_comp": skill_comp,
                        "resume_skills_data": resume_skills_data,
                        "jd_skills_data": jd_skills_data,
                        "parsed_sections": parsed_sections,
                        "contact_info": contact_info,
                        "recommendations": recommendations,
                    }
                    st.success("Analysis complete! Review the detailed findings below.")

    # -------------------------------------------------------------------------
    # Render Analysis Results
    # -------------------------------------------------------------------------
    if "analysis_result" in st.session_state:
        res = st.session_state["analysis_result"]
        md = res["match_details"]
        sc = res["skill_comp"]

        st.markdown("---")
        st.markdown(f"## 🎯 Match Assessment: {res['job_title']}")
        st.caption(f"Evaluated against resume: **{res['resume_name']}**")

        # Top Metric Showcase (Gauge + Donut + Summary Cards)
        m_col1, m_col2, m_col3 = st.columns([1.1, 1.1, 1.3], gap="medium")

        with m_col1:
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            st.markdown(f"<div class='card-title'>Overall Compatibility: <strong>{md['overall_score']}%</strong></div>", unsafe_allow_html=True)
            st.plotly_chart(create_score_gauge(md["overall_score"]), use_container_width=True)
            st.markdown(
                f"<div style='text-align: center; font-size: 0.9rem; font-weight: 600; color: #818CF8;'>Rating: {md['fit_level']}</div>"
                f"<div style='text-align: center; font-size: 0.8rem; color: #94A3B8; margin-top: 4px;'>{md['fit_description']}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with m_col2:
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            st.markdown("<div class='card-title'>Skill Match Breakdown</div>", unsafe_allow_html=True)
            st.plotly_chart(
                create_skill_breakdown_chart(
                    sc["matched_count"],
                    sc["missing_count"],
                    len(sc["additional_skills"])
                ),
                use_container_width=True,
            )
            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-around; font-size: 0.85rem; text-align: center;">
                    <div><span style="color: #10B981; font-weight: 700;">{sc['matched_count']}</span><br><span style="color: #94A3B8;">Matched</span></div>
                    <div><span style="color: #EF4444; font-weight: 700;">{sc['missing_count']}</span><br><span style="color: #94A3B8;">Missing</span></div>
                    <div><span style="color: #6366F1; font-weight: 700;">{len(sc['additional_skills'])}</span><br><span style="color: #94A3B8;">Additional</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with m_col3:
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            st.markdown("<div class='card-title'>Explainable Scoring Model</div>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div style="font-size: 0.88rem; line-height: 1.6; color: #CBD5E1;">
                    ResumeIQ uses a deterministic, transparent composite model:
                    <ul style="padding-left: 20px; margin-top: 8px;">
                        <li><strong>Skill Overlap ({md['skill_weight']}% weight):</strong> {md['skill_score_pct']}% direct coverage of required skills.</li>
                        <li><strong>TF-IDF Vocabulary ({md['tfidf_weight']}% weight):</strong> {md['tfidf_score_pct']}% semantic and contextual term alignment.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Top keywords driving similarity
            if md["top_shared_keywords"]:
                st.markdown("<div style='font-size: 0.85rem; font-weight: 600; color: #F8FAFC; margin-top: 10px;'>Top Co-occurring Keywords:</div>", unsafe_allow_html=True)
                kw_pills = "".join(
                    [f"<span class='skill-pill skill-neutral'>{word}</span> " for word, _ in md["top_shared_keywords"][:6]]
                )
                st.markdown(f"<div class='skill-pill-container'>{kw_pills}</div>", unsafe_allow_html=True)

            st.markdown(
                f"<div class='disclaimer-box'><strong>Ethical Transparency:</strong> {md['disclaimer']}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # Detailed Tabs: Skills, Recommendations, Resume Sections
        # ---------------------------------------------------------------------
        tab_skills, tab_recs, tab_sections = st.tabs(
            ["🛠 Skill Gap Analysis", "💡 Actionable Recommendations", "📑 Parsed Resume Sections"]
        )

        # Tab 1: Skill Gap Analysis
        with tab_skills:
            st.markdown("### Skill Overlap & Gap Matrix")

            c_gap1, c_gap2 = st.columns(2)

            with c_gap1:
                st.markdown(f"#### ✅ Matched Skills ({sc['matched_count']})")
                if sc["matched_skills"]:
                    pills_html = "".join(
                        [f"<span class='skill-pill skill-matched'>{s}</span>" for s in sc["matched_skills"]]
                    )
                    st.markdown(f"<div class='skill-pill-container'>{pills_html}</div>", unsafe_allow_html=True)
                else:
                    st.info("No direct skill matches detected against the catalog.")

                st.markdown(f"#### ➕ Additional Candidate Skills ({len(sc['additional_skills'])})")
                st.caption("Skills present in your resume that were not explicitly demanded by this job description:")
                if sc["additional_skills"]:
                    add_pills = "".join(
                        [f"<span class='skill-pill skill-additional'>{s}</span>" for s in sc["additional_skills"]]
                    )
                    st.markdown(f"<div class='skill-pill-container'>{add_pills}</div>", unsafe_allow_html=True)
                else:
                    st.caption("No extra catalog skills detected.")

            with c_gap2:
                st.markdown(f"#### ❌ Missing Skills Requested ({sc['missing_count']})")
                st.caption("Skills explicitly required or mentioned in the job description that were absent from your resume:")
                if sc["missing_skills"]:
                    missing_pills = "".join(
                        [f"<span class='skill-pill skill-missing'>{s}</span>" for s in sc["missing_skills"]]
                    )
                    st.markdown(f"<div class='skill-pill-container'>{missing_pills}</div>", unsafe_allow_html=True)
                else:
                    st.success("Outstanding! Your resume covers 100% of the skills identified in this job post.")

                if sc["suggested_priorities"]:
                    st.markdown("#### 🎯 Recommended Learning Priorities")
                    st.caption("Prioritized technical competencies to study or highlight first:")
                    for idx, s in enumerate(sc["suggested_priorities"], 1):
                        st.markdown(f"**{idx}. {s}**")

            # Domain breakdown chart
            st.markdown("---")
            st.markdown("#### Skill Distribution by Domain")
            st.plotly_chart(
                create_category_skill_bar(
                    res["resume_skills_data"]["by_category"],
                    res["jd_skills_data"]["by_category"],
                ),
                use_container_width=True,
            )

        # Tab 2: Recommendations
        with tab_recs:
            st.markdown("### Practical, Rule-Based Improvement Suggestions")
            st.caption("Targeted suggestions generated strictly from your resume data, section structures, and skill gaps.")

            for rec in res["recommendations"]:
                priority_class = f"priority-{rec['priority'].lower()}"
                badge_class = f"badge-{rec['priority'].lower()}"
                st.markdown(
                    f"""
                    <div class="rec-card {priority_class}">
                        <div class="rec-header">
                            <span class="rec-title">{rec['title']}</span>
                            <span class="rec-badge {badge_class}">{rec['priority']} Priority</span>
                        </div>
                        <p class="rec-advice">{rec['advice']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Tab 3: Parsed Resume Sections
        with tab_sections:
            st.markdown("### Transparent Section Parser Inspection")
            st.caption("Shows how Applicant Tracking Systems (ATS) identify and segment your resume headers:")

            for sec_name, sec_content in res["parsed_sections"].items():
                is_detected = sec_content != "Not Detected"
                status_icon = "🟢 Detected" if is_detected else "🔴 Not Detected"

                with st.expander(f"{sec_name} — {status_icon}", expanded=is_detected):
                    if is_detected:
                        st.text_area(f"{sec_name} Content", sec_content, height=140, key=f"sec_{sec_name}")
                    else:
                        st.warning(
                            f"The parser could not locate an obvious '{sec_name.upper()}' heading. "
                            "Consider adding a clearly formatted heading to assist automated parsers."
                        )

        # ---------------------------------------------------------------------
        # Save to Database History Section
        # -------------------------------------------------------------------------
        st.markdown("---")
        st.markdown("### 💾 Save to Analysis History")
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            save_notes = st.text_input("Add an optional note for this run", placeholder="e.g. Version 2 with Docker added")
        with col_h2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Save Record to SQLite", type="primary"):
                saved_id = save_analysis(
                    resume_name=res["resume_name"],
                    job_title=res["job_title"],
                    overall_score=md["overall_score"],
                    tfidf_score=md["tfidf_score_pct"],
                    skill_score=md["skill_score_pct"],
                    matched_skills=sc["matched_skills"],
                    missing_skills=sc["missing_skills"],
                    notes=save_notes,
                    db_path=DB_PATH,
                )
                st.success(f"Analysis saved locally with Record ID #{saved_id}!")


# -----------------------------------------------------------------------------
# Page 2: Analysis History
# -----------------------------------------------------------------------------
elif menu_choice == "📊 Analysis History":
    st.markdown("## 📊 Analysis History")
    st.caption("View and manage your locally saved resume evaluation sessions.")

    records = get_all_analyses(DB_PATH)

    if not records:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-icon">📂</div>
                <div class="empty-state-title">No Historical Records Found</div>
                <div class="empty-state-desc">
                    You haven't saved any resume evaluations yet. Run an analysis from the 'Match & Analyze' tab
                    and click 'Save Record to SQLite' to populate your history.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # History Action Bar
        col_act1, col_act2 = st.columns([4, 1])
        with col_act1:
            st.info(f"Displaying **{len(records)}** saved analysis records. Database: `{DB_PATH.name}`")
        with col_act2:
            if st.button("🗑 Clear All Records", type="secondary"):
                clear_all_analyses(DB_PATH)
                st.rerun()

        # Render records as interactive expandable cards
        for rec in records:
            score = rec["overall_score"]
            score_color = "#10B981" if score >= 75 else ("#F59E0B" if score >= 50 else "#EF4444")

            with st.expander(f"Record #{rec['id']}: {rec['job_title']} — {score}% Match ({rec['timestamp']})"):
                col_r1, col_r2, col_r3 = st.columns([2, 2, 1])
                with col_r1:
                    st.markdown(f"**Resume File:** `{rec['resume_name']}`")
                    st.markdown(f"**Date:** {rec['timestamp']}")
                    if rec["notes"]:
                        st.markdown(f"**Notes:** *{rec['notes']}*")

                with col_r2:
                    st.markdown(
                        f"""
                        <div style="font-size: 0.9rem;">
                            <strong>Overall Score:</strong> <span style="color: {score_color}; font-weight: 700;">{score}%</span><br>
                            <strong>TF-IDF Score:</strong> {rec['tfidf_score']}%<br>
                            <strong>Skill Coverage:</strong> {rec['skill_score']}%
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with col_r3:
                    if st.button("Delete Record", key=f"del_{rec['id']}", type="secondary"):
                        delete_analysis(rec["id"], DB_PATH)
                        st.success(f"Record #{rec['id']} deleted.")
                        st.rerun()

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                # Show skills breakdown
                matched = rec["matched_skills"]
                missing = rec["missing_skills"]

                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    st.markdown(f"**Matched Skills ({len(matched)}):**")
                    if matched:
                        pills = "".join([f"<span class='skill-pill skill-matched'>{s}</span>" for s in matched])
                        st.markdown(f"<div class='skill-pill-container'>{pills}</div>", unsafe_allow_html=True)
                    else:
                        st.caption("None recorded.")

                with c_m2:
                    st.markdown(f"**Missing Skills ({len(missing)}):**")
                    if missing:
                        pills = "".join([f"<span class='skill-pill skill-missing'>{s}</span>" for s in missing])
                        st.markdown(f"<div class='skill-pill-container'>{pills}</div>", unsafe_allow_html=True)
                    else:
                        st.caption("None missing.")


# -----------------------------------------------------------------------------
# Page 3: Skill Taxonomy Explorer
# -----------------------------------------------------------------------------
elif menu_choice == "📚 Skill Taxonomy":
    st.markdown("## 📚 Skill Taxonomy Explorer")
    st.caption("Explore, search, and customize the skills dictionary used for keyword and gap detection.")

    extractor = st.session_state.skill_extractor
    categories = list(extractor.taxonomy.keys())

    # Add custom skill form
    with st.expander("➕ Add Custom Skill to Taxonomy", expanded=False):
        c_add1, c_add2, c_add3 = st.columns([2, 2, 1])
        with c_add1:
            new_skill = st.text_input("Skill Name", placeholder="e.g. Julia, Rust, Solana")
        with c_add2:
            target_category = st.selectbox("Category", categories + ["Custom Skills"])
        with c_add3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Add Skill", type="primary"):
                if new_skill:
                    success = extractor.add_custom_skill(new_skill, target_category)
                    if success:
                        st.success(f"Added '{new_skill}' to '{target_category}'!")
                    else:
                        st.info(f"'{new_skill}' already exists in the taxonomy.")
                else:
                    st.warning("Please specify a valid skill name.")

    # Search filter
    search_query = st.text_input("🔍 Search skills", placeholder="Type to filter skills...").strip().lower()

    col1, col2 = st.columns(2)
    for idx, (cat, skills) in enumerate(extractor.taxonomy.items()):
        filtered_skills = [s for s in skills if search_query in s.lower()] if search_query else skills
        target_col = col1 if idx % 2 == 0 else col2

        with target_col:
            with st.container():
                st.markdown(f"#### {cat} ({len(filtered_skills)})")
                if filtered_skills:
                    pills = "".join([f"<span class='skill-pill skill-neutral'>{s}</span>" for s in filtered_skills])
                    st.markdown(f"<div class='skill-pill-container'>{pills}</div>", unsafe_allow_html=True)
                else:
                    st.caption("No matching skills found in this category.")


# -----------------------------------------------------------------------------
# Page 4: How It Works & Architecture Guide
# -----------------------------------------------------------------------------
elif menu_choice == "📖 How It Works":
    st.markdown("## 📖 Architecture & Educational Guide")
    st.caption("Understand the algorithms, pipelines, and design principles powering ResumeIQ.")

    st.markdown(
        """
        ### 🔄 End-to-End Execution Flow
        ```
        [ Resume File (PDF / DOCX / TXT) ]           [ Target Job Description ]
                      │                                          │
                      ▼                                          ▼
        [ Document Extractor (fitz / docx) ]        [ Input Sanitization & Validation ]
                      │                                          │
                      ▼                                          ▼
        [ Section & Contact Parsing ]               [ Skill Extractor (Regex Taxonomy) ]
                      │                                          │
                      ├──────────────────────────┬───────────────┤
                      │                          │               │
                      ▼                          ▼               ▼
           [ Skill Gap Analysis ]     [ TF-IDF Vectorizer ]  [ Rule-Based Recommendations ]
          (Matched, Missing, Extra)   (Cosine Similarity)   (Metrics, Phrasing, Sections)
                      │                          │                       │
                      └──────────────┬───────────┘                       │
                                     ▼                                   │
                       [ Weighted Compatibility Model ]                  │
                                     │                                   │
                                     └─────────────────┬─────────────────┘
                                                       ▼
                                         [ Modern Streamlit Dashboard ]
                                                       │
                                                       ▼
                                          [ SQLite Local History ]
        ```

        ---

        ### 🧠 Key Educational Concepts

        #### 1. How PDF Text Extraction Works
        - Standard digital PDFs contain vector text glyphs positioned with coordinates.
        - **PyMuPDF (`fitz`)** accesses the PDF's internal document tree and extracts character streams without rendering them into raster images.
        - If a PDF is a scanned photo, it contains zero text streams. ResumeIQ detects this by calculating the character-per-page ratio and warns the user that OCR is needed instead of silently failing.

        #### 2. How TF-IDF Vectorization Works
        - **TF (Term Frequency):** Measures how frequently a word appears in a document.
          $$\text{TF}(t, d) = \frac{\text{Count of word } t \text{ in document } d}{\text{Total words in document } d}$$
        - **IDF (Inverse Document Frequency):** Measures how rare or informative a word is across all documents.
          $$\text{IDF}(t) = \log\left(\frac{1 + N}{1 + \text{DF}(t)}\right) + 1$$
        - Rare technical words like `Kubernetes` or `FastAPI` receive higher TF-IDF weights, while common English words receive negligible weights.

        #### 3. How Cosine Similarity Works
        - Text documents are represented as high-dimensional TF-IDF vectors $\vec{A}$ and $\vec{B}$.
        - Cosine similarity calculates the cosine of the angle $\theta$ between the two vectors:
          $$\text{Cosine Similarity} = \frac{\vec{A} \cdot \vec{B}}{\|\vec{A}\| \|\vec{B}\|}$$
        - Returns a value from $0.0$ (no shared vocabulary) to $1.0$ (identical vocabulary proportions).

        #### 4. Explainable Hybrid Scoring
        Instead of treating an unexplainable number as an "AI Score", ResumeIQ explicitly divides the score into:
        1. **Skill Coverage (60% weight):** Did the candidate demonstrate the concrete hard skills required by the job?
        2. **TF-IDF Semantic Similarity (40% weight):** Does the overall vocabulary, experience descriptions, and terminology align with the job description?

        ---

        ### 🛡 Privacy Guarantee
        - **No Cloud Transmission:** No external LLM or cloud API is queried. All algorithms execute directly inside your Python interpreter.
        - **Safe Storage:** SQLite only stores high-level scores and extracted skill lists. Raw resume text is never permanently saved to disk.
        """
    )
