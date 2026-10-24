"""
ResumeIQ Enterprise — AI-Powered ATS Resume Analyzer & Job Match Platform
========================================================================
Main Streamlit Application
A modern, dark-themed SaaS platform providing:
1. Distinct Resume Quality Score (0-100)
2. Dedicated ATS Parsing Compatibility Score (0-100)
3. Job Description Match Score (0-100)
4. Structured editable resume representation
5. Action verb & quantified metrics audits
6. AI Resume Assistant & Optimizer
7. ATS-friendly PDF and DOCX export with self-test verification
8. Resume version history and score comparison
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
    AI_CONFIG,
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
    parse_full_resume_structure,
    parse_resume_sections,
)
from analyzer.skill_extractor import SkillExtractor
from analyzer.similarity import calculate_similarity, calculate_tfidf_similarity, compute_match_details
from analyzer.recommendations import generate_recommendations
from analyzer.ats_analyzer import analyze_ats_compatibility
from analyzer.quality_analyzer import analyze_resume_quality, audit_bullet_points
from analyzer.job_matcher import match_resume_to_job
from analyzer.ai_assistant import ResumeAssistant
from analyzer.resume_builder import (
    generate_analysis_report,
    generate_docx_resume,
    generate_pdf_resume,
    verify_generated_resume_extractability,
)

# Database persistence modules
from database.db import (
    clear_all_analyses,
    compare_analysis_records,
    delete_analysis,
    get_all_analyses,
    get_analysis_by_id,
    get_history_summary_stats,
    get_resume_versions,
    init_db,
    save_analysis,
    save_resume_version,
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
    page_title=f"{APP_NAME} Enterprise — AI Resume Analyzer & ATS Optimizer",
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

# Initialize Session State Objects
if "skill_extractor" not in st.session_state:
    st.session_state.skill_extractor = SkillExtractor()

if "ai_assistant" not in st.session_state:
    st.session_state.ai_assistant = ResumeAssistant()


# -----------------------------------------------------------------------------
# Plotly Chart Generators (Dark Theme Cohesion)
# -----------------------------------------------------------------------------
def create_score_gauge(score: float, title: str, accent_color: str) -> go.Figure:
    """Creates a modern circular gauge chart indicating a specific score."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "%", "font": {"size": 36, "color": THEME_COLORS["text_primary"]}},
            title={"text": title, "font": {"size": 15, "color": THEME_COLORS["text_secondary"]}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": THEME_COLORS["card_border"]},
                "bar": {"color": accent_color, "thickness": 0.28},
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
        margin=dict(l=20, r=20, t=35, b=20),
        height=200,
    )
    return fig


def create_radar_breakdown(breakdown_dict: Dict[str, float], title: str, color: str) -> go.Figure:
    """Creates a radar chart showing multi-dimensional sub-scores."""
    categories = [k.replace("_", " ").title() for k in breakdown_dict.keys()]
    values = list(breakdown_dict.values())
    if values:
        categories.append(categories[0])
        values.append(values[0])

    fig = go.Figure(
        data=[
            go.Scatterpolar(
                r=values,
                theta=categories,
                fill="toself",
                fillcolor=f"rgba{tuple(list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + [0.2])}",
                line=dict(color=color, width=2),
            )
        ]
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#334155", tickfont=dict(color="#94A3B8")),
            angularaxis=dict(gridcolor="#334155", tickfont=dict(color="#F8FAFC", size=10)),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=35, r=35, t=30, b=30),
        height=260,
        showlegend=False,
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
# Core Analysis Engine Dispatcher
# -----------------------------------------------------------------------------
def run_full_analysis(raw_text: str, file_name: str, job_desc: str = "", target_title: str = ""):
    """Executes the full evaluation pipeline across Quality, ATS, and Job Matching."""
    extractor = st.session_state.skill_extractor

    # 1. Structured Resume Parsing
    structured = parse_full_resume_structure(raw_text, file_name)
    parsed_sections = structured["sections"]
    contact_info = structured["contact"]

    # 2. Extract Skills
    skills_data = extractor.extract_skills(raw_text)
    detected_skills = skills_data["all_skills"]

    # 3. Dedicated ATS Compatibility Analysis
    ats_res = analyze_ats_compatibility(
        raw_text=raw_text,
        parsed_sections=parsed_sections,
        contact_info=contact_info,
        page_count=max(1, structured["word_count"] // 450),
        file_name=file_name,
    )

    # 4. Dedicated Resume Quality Analysis
    quality_res = analyze_resume_quality(
        raw_text=raw_text,
        parsed_sections=parsed_sections,
        structured_data=structured,
        detected_skills=detected_skills,
    )

    # 5. Job Description Match Analysis
    job_match_res = match_resume_to_job(
        resume_text=raw_text,
        job_description=job_desc,
        target_job_title=target_title,
        extractor=extractor,
    )

    # 6. Legacy / Hybrid Compatibility for Overview
    skill_comp = extractor.compare_skills(
        detected_skills,
        extractor.extract_skills(job_desc)["all_skills"] if job_desc else set(),
    )
    legacy_match = compute_match_details(raw_text, job_desc or raw_text, skill_comp)

    # Store into session state
    st.session_state["structured_resume"] = structured
    st.session_state["raw_resume_text"] = raw_text
    st.session_state["resume_file_name"] = file_name
    st.session_state["ats_analysis"] = ats_res
    st.session_state["quality_analysis"] = quality_res
    st.session_state["job_match_analysis"] = job_match_res
    st.session_state["legacy_match"] = legacy_match
    st.session_state["detected_skills"] = detected_skills
    st.session_state["skills_data"] = skills_data
    st.session_state["target_jd"] = job_desc
    st.session_state["target_job_title"] = target_title


# -----------------------------------------------------------------------------
# Sidebar Navigation & Platform Status
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 6px 0 16px 0;">
            <div class="brand-badge">Enterprise v{APP_VERSION}</div>
            <h2 style="margin: 0; font-size: 1.5rem; color: #F8FAFC;">🎯 {APP_NAME}</h2>
            <p style="font-size: 0.82rem; color: #94A3B8; margin-top: 3px;">{APP_TAGLINE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_options = [
        "📊 Dashboard Overview",
        "📄 Upload & Parsed Resume",
        "🎯 ATS Compatibility",
        "📋 Job Description Match",
        "🛠 Skills & Keywords",
        "💼 Experience & Achievements",
        "✍ AI Resume Assistant",
        "🏗 Resume Builder & Export",
        "🕒 History & Comparisons",
        "⚙ Settings & API",
    ]

    selected_page = st.radio("Navigation", nav_options, index=0)

    st.markdown("---")

    # One-Click Demo Mode Button in Sidebar
    if st.button("🚀 Load Demo Resume & Job", type="secondary"):
        demo_resume = load_sample_resume_content()
        demo_jd = load_sample_jd_content()
        run_full_analysis(
            raw_text=demo_resume,
            file_name="Alex_Rivera_Sample_Resume.pdf",
            job_desc=demo_jd,
            target_title="Senior Python Backend Engineer",
        )
        st.success("Sample data loaded & analyzed!")
        st.rerun()

    st.markdown(
        """
        <div style="font-size: 0.78rem; color: #94A3B8; line-height: 1.4; margin-top: 10px;">
            <strong style="color: #F8FAFC;">🔒 Privacy First:</strong><br>
            All parsing and vector processing runs 100% locally on your computer.
            Full resume text is never sent to public APIs or logged to disk.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# PAGE 1: DASHBOARD OVERVIEW
# =============================================================================
if selected_page == "📊 Dashboard Overview":
    st.markdown("## 📊 Executive Dashboard Overview")
    st.caption("Comprehensive multi-dimensional health overview of candidate resumes, ATS readiness, and job alignment.")

    # Top Summary Stat Cards from SQLite Database
    stats = get_history_summary_stats(DB_PATH)

    has_active_analysis = "structured_resume" in st.session_state

    # Top Three Primary Score Showcase Cards
    c_s1, c_s2, c_s3 = st.columns(3)

    if has_active_analysis:
        q_res = st.session_state["quality_analysis"]
        ats_res = st.session_state["ats_analysis"]
        jm_res = st.session_state["job_match_analysis"]

        with c_s1:
            st.markdown(
                f"""
                <div class="score-trio-card score-quality">
                    <span class="score-tag-badge" style="background: rgba(99, 102, 241, 0.2); color: #A5B4FC;">Quality Score</span>
                    <div style="font-size: 2.2rem; font-weight: 700; color: #F8FAFC;">{q_res['quality_score']}%</div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: #818CF8; margin-top: 4px;">{q_res['rating']}</div>
                    <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 6px;">Evaluates content depth, metrics, and action verbs.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_s2:
            st.markdown(
                f"""
                <div class="score-trio-card score-ats">
                    <span class="score-tag-badge" style="background: rgba(59, 130, 246, 0.2); color: #93C5FD;">ATS Compatibility</span>
                    <div style="font-size: 2.2rem; font-weight: 700; color: #F8FAFC;">{ats_res['ats_score']}%</div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: #60A5FA; margin-top: 4px;">{ats_res['score_category']}</div>
                    <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 6px;">Evaluates digital text layer, headings, and formatting risks.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_s3:
            if jm_res.get("has_job_description"):
                jm_score_str = f"{jm_res['job_match_score']}%"
                jm_fit = jm_res["fit_level"]
                jm_sub = f"Evaluated against: {st.session_state.get('target_job_title', 'Target Role')}"
            else:
                jm_score_str = "Not Evaluated"
                jm_fit = "Awaiting Job Description"
                jm_sub = "Paste a job description to calculate target alignment."

            st.markdown(
                f"""
                <div class="score-trio-card score-job">
                    <span class="score-tag-badge" style="background: rgba(16, 185, 129, 0.2); color: #6EE7B7;">Job Description Match</span>
                    <div style="font-size: 2.2rem; font-weight: 700; color: #F8FAFC;">{jm_score_str}</div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: #34D399; margin-top: 4px;">{jm_fit}</div>
                    <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 6px;">{jm_sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        with c_s1:
            st.markdown(
                """
                <div class="score-trio-card score-quality">
                    <span class="score-tag-badge" style="background: rgba(99, 102, 241, 0.2); color: #A5B4FC;">Quality Score</span>
                    <div style="font-size: 2.2rem; font-weight: 700; color: #94A3B8;">--%</div>
                    <div style="font-size: 0.82rem; color: #94A3B8; margin-top: 6px;">Upload a resume to calculate content quality.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_s2:
            st.markdown(
                """
                <div class="score-trio-card score-ats">
                    <span class="score-tag-badge" style="background: rgba(59, 130, 246, 0.2); color: #93C5FD;">ATS Compatibility</span>
                    <div style="font-size: 2.2rem; font-weight: 700; color: #94A3B8;">--%</div>
                    <div style="font-size: 0.82rem; color: #94A3B8; margin-top: 6px;">Upload a resume to analyze parsing risks.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_s3:
            st.markdown(
                """
                <div class="score-trio-card score-job">
                    <span class="score-tag-badge" style="background: rgba(16, 185, 129, 0.2); color: #6EE7B7;">Job Description Match</span>
                    <div style="font-size: 2.2rem; font-weight: 700; color: #94A3B8;">--%</div>
                    <div style="font-size: 0.82rem; color: #94A3B8; margin-top: 6px;">Paste a job description to assess keyword fit.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Secondary Metrics & Quick Actions
    col_d1, col_d2 = st.columns([2, 1])

    with col_d1:
        with st.container(border=True):
            st.markdown("### 🎯 Prioritized Next Actions")
            if has_active_analysis:
                q_findings = st.session_state["quality_analysis"]["findings"]
                ats_fixes = st.session_state["ats_analysis"]["prioritized_fixes"]

                high_priority = [f for f in q_findings if f["priority"] == "High"]
                if high_priority:
                    st.error(f"Found **{len(high_priority)} High-Priority Issue(s)** that directly affect screening:")
                    for h in high_priority[:3]:
                        st.markdown(f"- **{h['title']}** ({h['section']}): {h['recommendation']}")
                elif ats_fixes:
                    st.warning("ATS Parsing Improvements Suggested:")
                    for fix in ats_fixes[:2]:
                        st.markdown(f"- {fix}")
                else:
                    st.success("🎉 Outstanding! No critical issues or parsing risks detected.")
            else:
                st.info("No resume loaded yet. Click '🚀 Load Demo Resume & Job' in the sidebar or go to '📄 Upload & Parsed Resume' to begin.")

    with col_d2:
        with st.container(border=True):
            st.markdown("### ⚡ Quick Navigation")
            st.markdown(
                """
                - 📄 **Review Parsed Data:** Check name and extracted roles.
                - 🎯 **ATS Health Check:** See formatting and font risks.
                - 📋 **Match Job Post:** Compare required vs preferred skills.
                - ✍ **AI Optimizer:** Rewrite bullets with Google XYZ formula.
                - 🏗 **Export ATS Resume:** Download verified PDF or DOCX.
                """
            )

    # Historical Session Overview
    records = get_all_analyses(DB_PATH)
    if records:
        st.markdown("---")
        st.markdown("### 🕒 Recently Analyzed Sessions")
        recent_df = pd.DataFrame(
            [
                {
                    "ID": r["id"],
                    "Timestamp": r["timestamp"],
                    "Resume": r["resume_name"],
                    "Target Role": r["job_title"],
                    "Quality": f"{r.get('quality_score', r['overall_score'])}%",
                    "ATS": f"{r.get('ats_score', 85.0)}%",
                    "Job Match": f"{r.get('job_match_score', r['overall_score'])}%",
                }
                for r in records[:5]
            ]
        )
        st.dataframe(recent_df, hide_index=True)


# =============================================================================
# PAGE 2: UPLOAD & PARSED RESUME (EDITABLE)
# =============================================================================
elif selected_page == "📄 Upload & Parsed Resume":
    st.markdown("## 📄 Upload & Structured Resume Representation")
    st.caption("Upload your resume (PDF, DOCX, TXT) and inspect or correct parsed fields before analysis.")

    col_u1, col_u2 = st.columns([1, 1], gap="medium")

    with col_u1:
        uploaded_file = st.file_uploader(
            "Select Resume Document",
            type=["pdf", "docx", "txt"],
            help="Maximum file size 5MB. Image-only PDFs will be flagged for OCR.",
        )

        target_title_in = st.text_input("Target Job Title (Optional)", value=st.session_state.get("target_job_title", ""), placeholder="e.g. Senior Backend Engineer")
        target_jd_in = st.text_area("Target Job Description (Optional)", value=st.session_state.get("target_jd", ""), height=180, placeholder="Paste job posting here to evaluate match...")

        if st.button("⚡ Parse & Analyze Uploaded Resume", type="primary"):
            if uploaded_file is not None:
                bytes_data = uploaded_file.getvalue()
                valid, msg = validate_file_upload(uploaded_file.name, len(bytes_data))
                if not valid:
                    st.error(msg)
                else:
                    text, pages, warning = extract_text_from_file(bytes_data, uploaded_file.name)
                    if warning and "scanned" in warning.lower():
                        st.warning(warning)
                    run_full_analysis(text, uploaded_file.name, target_jd_in, target_title_in)
                    st.success("Resume parsed successfully!")
                    st.rerun()
            else:
                st.error("Please select a file to upload or load demo data.")

    with col_u2:
        if "structured_resume" in st.session_state:
            sr = st.session_state["structured_resume"]
            st.markdown("### ✏️ Verified Structured Profile")
            st.caption("Review extracted fields. You can correct any OCR or parsing misreadings below:")

            with st.form("edit_parsed_resume_form"):
                e_name = st.text_input("Full Name", value=sr.get("candidate_name", ""))
                e_email = st.text_input("Email Address", value=sr.get("contact", {}).get("email") or "")
                e_phone = st.text_input("Phone Number", value=sr.get("contact", {}).get("phone") or "")
                e_location = st.text_input("Location", value=sr.get("contact", {}).get("location") or "")
                e_linkedin = st.text_input("LinkedIn Profile", value=sr.get("contact", {}).get("linkedin") or "")
                e_github = st.text_input("GitHub Profile", value=sr.get("contact", {}).get("github") or "")
                e_summary = st.text_area("Professional Summary", value=sr.get("summary", ""), height=100)

                submit_edits = st.form_submit_button("💾 Save Verified Profile & Re-Score")
                if submit_edits:
                    sr["candidate_name"] = e_name
                    sr["contact"]["email"] = e_email
                    sr["contact"]["phone"] = e_phone
                    sr["contact"]["location"] = e_location
                    sr["contact"]["linkedin"] = e_linkedin
                    sr["contact"]["github"] = e_github
                    sr["summary"] = e_summary

                    # Update raw text with corrected header
                    updated_text = f"{e_name}\n{e_email} | {e_phone} | {e_location}\n{e_summary}\n\n" + st.session_state["raw_resume_text"]
                    run_full_analysis(updated_text, sr["file_name"], target_jd_in, target_title_in)
                    st.success("Profile updated and re-analyzed!")
                    st.rerun()
        else:
            st.info("Upload a document on the left or click '🚀 Load Demo Resume & Job' in the sidebar.")


# =============================================================================
# PAGE 3: ATS COMPATIBILITY
# =============================================================================
elif selected_page == "🎯 ATS Compatibility":
    st.markdown("## 🎯 ATS Parsing Compatibility Diagnostics")
    st.caption("Detailed technical inspection measuring how reliably commercial Applicant Tracking Systems parse this resume.")

    if "ats_analysis" not in st.session_state:
        st.warning("Please upload a resume or load demo data to view ATS diagnostics.")
    else:
        ats = st.session_state["ats_analysis"]

        col_a1, col_a2 = st.columns([1, 1], gap="medium")

        with col_a1:
            with st.container(border=True):
                st.plotly_chart(
                    create_score_gauge(ats["ats_score"], "ATS Parsing Score", THEME_COLORS["accent_secondary"]),
                )
                st.markdown(f"**Readiness Level:** `{ats['score_category']}`")
                st.markdown(f"*{ats['summary']}*")
                st.caption(ats["disclaimer"])

        with col_a2:
            with st.container(border=True):
                st.markdown("#### Dimensional Breakdown")
                st.plotly_chart(
                    create_radar_breakdown(ats["breakdown"], "ATS Dimensions", THEME_COLORS["accent_secondary"]),
                )

        st.markdown("---")

        # Diagnostics Checks: Passed, Warnings, Risks
        c_p, c_w, c_r = st.columns(3)

        with c_p:
            st.markdown(f"#### ✅ Passed Checks ({len(ats['passed_checks'])})")
            for p in ats["passed_checks"]:
                st.markdown(
                    f"""
                    <div style="background: #1E293B; border-left: 3px solid #10B981; padding: 10px; border-radius: 6px; margin-bottom: 8px; font-size: 0.85rem;">
                        <strong>{p['title']}</strong><br>
                        <span style="color: #94A3B8;">{p['description']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with c_w:
            st.markdown(f"#### ⚠️ Parsing Warnings ({len(ats['warning_checks'])})")
            if ats["warning_checks"]:
                for w in ats["warning_checks"]:
                    st.markdown(
                        f"""
                        <div style="background: #1E293B; border-left: 3px solid #F59E0B; padding: 10px; border-radius: 6px; margin-bottom: 8px; font-size: 0.85rem;">
                            <strong>{w['title']}</strong><br>
                            <span style="color: #CBD5E1;">{w['description']}</span><br>
                            <em style="color: #FCD34D;">Recommendation: {w.get('recommendation', '')}</em>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No formatting warnings detected.")

        with c_r:
            st.markdown(f"#### ❌ Critical Risks ({len(ats['risk_checks'])})")
            if ats["risk_checks"]:
                for r in ats["risk_checks"]:
                    st.markdown(
                        f"""
                        <div style="background: #1E293B; border-left: 3px solid #EF4444; padding: 10px; border-radius: 6px; margin-bottom: 8px; font-size: 0.85rem;">
                            <strong>{r['title']}</strong><br>
                            <span style="color: #FCA5A5;">{r['description']}</span><br>
                            <em>Fix: {r.get('recommendation', '')}</em>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.success("Zero critical ATS extraction risks identified!")


# =============================================================================
# PAGE 4: JOB DESCRIPTION MATCH
# =============================================================================
elif selected_page == "📋 Job Description Match":
    st.markdown("## 📋 Job Description Match & Requirements Engine")
    st.caption("Compares candidate qualifications against required and preferred job posting specifications.")

    if "job_match_analysis" not in st.session_state:
        st.warning("Please upload a resume first.")
    else:
        jm = st.session_state["job_match_analysis"]

        if not jm.get("has_job_description"):
            st.info("No job description has been provided for this evaluation. Paste a job description below:")
            jd_input = st.text_area("Target Job Description", height=240, placeholder="Paste requirements, responsibilities, and required qualifications...")
            jt_input = st.text_input("Target Job Title", placeholder="e.g. Senior Python Backend Engineer")
            if st.button("Evaluate Job Match", type="primary"):
                run_full_analysis(
                    st.session_state["raw_resume_text"],
                    st.session_state["resume_file_name"],
                    jd_input,
                    jt_input,
                )
                st.rerun()
        else:
            col_m1, col_m2 = st.columns([1, 1], gap="medium")

            with col_m1:
                with st.container(border=True):
                    st.plotly_chart(
                        create_score_gauge(jm["job_match_score"], "Job Match Score", THEME_COLORS["success"]),
                    )
                    st.markdown(f"**Fit Level:** `{jm['fit_level']}`")
                    st.markdown(f"*{jm['summary']}*")
                    st.caption(jm["disclaimer"])

            with col_m2:
                with st.container(border=True):
                    st.markdown("#### Requirements Alignment")
                    req = jm["required_skills"]
                    pref = jm["preferred_skills"]

                    st.markdown(f"**Required Skills Coverage:** `{req['coverage_pct']}%` ({len(req['matched'])} of {req['total']} met)")
                    st.markdown(f"**Preferred Skills Coverage:** `{pref['coverage_pct']}%` ({len(pref['matched'])} of {pref['total']} met)")
                    st.markdown(f"**TF-IDF Vocabulary Alignment:** `{jm['tfidf_score_pct']}%`")
                    st.markdown(f"**Role Title Alignment:** `{jm['experience_alignment_pct']}%`")

            st.markdown("---")

            # Matched vs Missing Requirements
            c_req1, c_req2 = st.columns(2)

            with c_req1:
                st.markdown(f"#### ✅ Matched Required Skills ({len(req['matched'])})")
                if req["matched"]:
                    pills = "".join([f"<span class='skill-pill skill-matched'>{s}</span>" for s in req["matched"]])
                    st.markdown(f"<div class='skill-pill-container'>{pills}</div>", unsafe_allow_html=True)
                else:
                    st.caption("No required technical skills matched.")

                if pref["matched"]:
                    st.markdown(f"#### 🌟 Matched Preferred Skills ({len(pref['matched'])})")
                    pref_pills = "".join([f"<span class='skill-pill skill-additional'>{s}</span>" for s in pref["matched"]])
                    st.markdown(f"<div class='skill-pill-container'>{pref_pills}</div>", unsafe_allow_html=True)

            with c_req2:
                st.markdown(f"#### ❌ Missing Required Skills ({len(req['missing'])})")
                if req["missing"]:
                    pills = "".join([f"<span class='skill-pill skill-missing'>{s}</span>" for s in req["missing"]])
                    st.markdown(f"<div class='skill-pill-container'>{pills}</div>", unsafe_allow_html=True)
                else:
                    st.success("All required skills found on your resume!")

                if pref["missing"]:
                    st.markdown(f"#### ⚪ Missing Preferred Skills ({len(pref['missing'])})")
                    pref_missing = "".join([f"<span class='skill-pill skill-neutral'>{s}</span>" for s in pref["missing"]])
                    st.markdown(f"<div class='skill-pill-container'>{pref_missing}</div>", unsafe_allow_html=True)

            # Evidence Mapping
            st.markdown("---")
            st.markdown("### 🔍 Verified Evidence Snippets in Resume")
            st.caption("Shows where matched keywords actually appear in your work history or projects:")

            if jm["evidence_map"]:
                for skill, snippet in list(jm["evidence_map"].items())[:6]:
                    st.markdown(f"- **{skill}:** *\"{snippet}\"*")
            else:
                st.caption("No evidence snippets mapped.")

            # Keyword Stuffing Warnings
            if jm.get("keyword_stuffing_warnings"):
                st.markdown("---")
                st.warning("⚠️ Keyword Stuffing Alert:")
                for st_warn in jm["keyword_stuffing_warnings"]:
                    st.markdown(f"- {st_warn['warning']}")


# =============================================================================
# PAGE 5: SKILLS & KEYWORDS
# =============================================================================
elif selected_page == "🛠 Skills & Keywords":
    st.markdown("## 🛠 Skills & Keywords Taxonomy Analysis")
    st.caption("Categorization of technical competencies, tools, frameworks, and domain expertise.")

    if "skills_data" not in st.session_state:
        st.warning("Please upload a resume first.")
    else:
        sk_data = st.session_state["skills_data"]
        detected = st.session_state["detected_skills"]

        st.markdown(f"Total Unique Skills Detected: **{len(detected)}**")

        for cat, skills in sk_data["by_category"].items():
            st.markdown(f"#### {cat} ({len(skills)})")
            pills = "".join([f"<span class='skill-pill skill-matched'>{s}</span>" for s in skills])
            st.markdown(f"<div class='skill-pill-container'>{pills}</div>", unsafe_allow_html=True)


# =============================================================================
# PAGE 6: EXPERIENCE & ACHIEVEMENTS
# =============================================================================
elif selected_page == "💼 Experience & Achievements":
    st.markdown("## 💼 Work Experience & Achievement Audit")
    st.caption("Audits bullet points for action verbs, quantifiable metrics, and active ownership.")

    if "quality_analysis" not in st.session_state:
        st.warning("Please upload a resume first.")
    else:
        audit = st.session_state["quality_analysis"]["bullet_audit"]

        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            st.metric("Total Experience Bullets", audit["total_bullets"])
        with col_b2:
            st.metric("Quantified Metric Bullets", f"{audit['metric_bullets']} ({int(audit['metric_ratio']*100)}%)")
        with col_b3:
            st.metric("Action Verb Openings", f"{audit['action_verb_bullets']} ({int(audit['action_verb_ratio']*100)}%)")

        st.markdown("---")

        if audit["weak_examples"]:
            st.markdown("### ⚠️ Bullets Flagged for Passive Phrasing")
            st.caption("Replace passive duties with active business outcomes:")
            for we in audit["weak_examples"]:
                st.markdown(f"- ❌ *\"{we}\"*")
                improved = st.session_state["ai_assistant"].improve_bullet_point(we)
                st.markdown(f"  - ✅ **Recommended:** *\"{improved['improved']}\"*")

        if audit["metric_examples"]:
            st.markdown("### 🌟 High-Impact Quantified Examples")
            for me in audit["metric_examples"]:
                st.markdown(f"- 🟢 *\"{me}\"*")


# =============================================================================
# PAGE 7: AI RESUME ASSISTANT & OPTIMIZER
# =============================================================================
elif selected_page == "✍ AI Resume Assistant":
    st.markdown("## ✍ AI Resume Assistant & Section Optimizer")
    st.caption("Rewrites weak bullet points, optimizes summaries, and explains score findings.")

    if "structured_resume" not in st.session_state:
        st.warning("Please upload a resume first.")
    else:
        assistant = st.session_state["ai_assistant"]
        sr = st.session_state["structured_resume"]

        tab_rewrite, tab_bullets, tab_qa = st.tabs(
            ["📝 Professional Summary Rewriter", "⚡ Bullet Point Enhancer", "💬 Score Explainer Q&A"]
        )

        with tab_rewrite:
            st.markdown("#### ATS-Optimized Summary Generator")
            curr_summary = sr.get("summary", "")
            target_role = st.session_state.get("target_job_title", "")

            if st.button("Generate Improved Summary", type="primary"):
                top_skills = list(st.session_state.get("detected_skills", []))
                res_sum = assistant.rewrite_summary(curr_summary, sr["candidate_name"], top_skills, target_role)

                c_orig, c_imp = st.columns(2)
                with c_orig:
                    st.markdown("**Original Summary:**")
                    st.markdown(f"*{res_sum['original']}*")
                with c_imp:
                    st.markdown("**AI-Improved Summary:**")
                    st.markdown(f"*{res_sum['improved']}*")
                    st.caption(f"Rationale: {res_sum['rationale']}")

        with tab_bullets:
            st.markdown("#### Transform Bullet with Google XYZ Formula")
            user_bullet = st.text_input("Enter a bullet point to improve:", value="Worked on backend features and fixed bugs.")
            if st.button("Enhance Bullet Point", type="primary"):
                imp = assistant.improve_bullet_point(user_bullet)
                st.markdown(
                    f"""
                    <div class="comparison-box">
                        <div class="comparison-label">Original:</div>
                        <div class="comparison-original">{imp['original']}</div>
                        <div style="height: 10px;"></div>
                        <div class="comparison-label">Improved:</div>
                        <div class="comparison-improved">{imp['improved']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if imp.get("metric_note"):
                    st.warning(imp["metric_note"])

        with tab_qa:
            st.markdown("#### Ask Questions About Your Evaluation")
            user_q = st.text_input("Ask a question about your scores, skill gaps, or ATS readiness:", placeholder="Why is my ATS score 75%?")
            if st.button("Ask Assistant", type="secondary"):
                if user_q:
                    q_score = st.session_state["quality_analysis"]["quality_score"]
                    a_score = st.session_state["ats_analysis"]["ats_score"]
                    j_score = st.session_state.get("job_match_analysis", {}).get("job_match_score", 0.0)
                    missing_skills = st.session_state.get("job_match_analysis", {}).get("required_skills", {}).get("missing", [])
                    ans = assistant.answer_analysis_question(user_q, q_score, a_score, j_score, missing_skills)
                    st.markdown(f"**Answer:**\n\n{ans}")


# =============================================================================
# PAGE 8: RESUME BUILDER & EXPORT
# =============================================================================
elif selected_page == "🏗 Resume Builder & Export":
    st.markdown("## 🏗 ATS-Friendly Resume Builder & Multi-Format Export")
    st.caption("Generate clean single-column resumes in vector PDF and Word DOCX formats with built-in text extractability verification.")

    if "structured_resume" not in st.session_state:
        st.warning("Please upload a resume first.")
    else:
        sr = st.session_state["structured_resume"]

        c_prev, c_exp = st.columns([1.4, 1], gap="medium")

        with c_prev:
            with st.container(border=True):
                st.markdown("### Document Preview")
                st.markdown(f"### {sr.get('candidate_name', 'Candidate Name').upper()}")
                contact = sr.get("contact", {})
                st.caption(f"{contact.get('email', '')} | {contact.get('phone', '')} | {contact.get('location', '')}")

                if sr.get("summary"):
                    st.markdown("**PROFESSIONAL SUMMARY**")
                    st.markdown(sr["summary"])

                if sr.get("experience"):
                    st.markdown("**WORK EXPERIENCE**")
                    for role in sr["experience"]:
                        st.markdown(f"**{role.get('title', '')}** | *{role.get('company', '')}* ({role.get('dates', '')})")
                        for b in role.get("bullets", []):
                            st.markdown(f"- {b}")

        with c_exp:
            with st.container(border=True):
                st.markdown("### 📥 Export Documents")

                # 1. Export DOCX
                docx_bytes = generate_docx_resume(sr)
                st.download_button(
                    label="📄 Download ATS-Standard DOCX (.docx)",
                    data=docx_bytes.getvalue(),
                    file_name=f"{sr.get('candidate_name', 'Resume').replace(' ', '_')}_ATS_Optimized.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                )

                # 2. Export PDF
                pdf_bytes = generate_pdf_resume(sr)
                st.download_button(
                    label="📑 Download Clean Vector PDF (.pdf)",
                    data=pdf_bytes.getvalue(),
                    file_name=f"{sr.get('candidate_name', 'Resume').replace(' ', '_')}_ATS_Optimized.pdf",
                    mime="application/pdf",
                    type="primary",
                )

                # 3. Export Comprehensive Analysis Report
                report_md = generate_analysis_report(
                    resume_name=sr.get("file_name", "Resume.pdf"),
                    job_title=st.session_state.get("target_job_title", ""),
                    quality_analysis=st.session_state["quality_analysis"],
                    ats_analysis=st.session_state["ats_analysis"],
                    job_match=st.session_state["job_match_analysis"],
                )
                st.download_button(
                    label="📊 Download Evaluation Report (.md)",
                    data=report_md.encode("utf-8"),
                    file_name="ResumeIQ_Evaluation_Report.md",
                    mime="text/markdown",
                    type="secondary",
                )

                st.markdown("---")
                st.markdown("#### 🔬 Self-Test Extractability Check")
                st.caption("Re-parses the generated PDF file to verify zero data loss for ATS systems:")

                if st.button("Verify PDF Extractability", type="secondary"):
                    is_ok, msg = verify_generated_resume_extractability(pdf_bytes.getvalue(), "generated.pdf")
                    if is_ok:
                        st.success(f"✓ {msg}")
                    else:
                        st.error(msg)


# =============================================================================
# PAGE 9: HISTORY & VERSION COMPARISONS
# =============================================================================
elif selected_page == "🕒 History & Comparisons":
    st.markdown("## 🕒 Analysis History & Version Comparison")
    st.caption("Track score progression across revisions and compare Version A against Version B.")

    # Save current run if available
    if "quality_analysis" in st.session_state:
        with st.expander("💾 Save Current Analysis Snapshot to History", expanded=False):
            col_sv1, col_sv2 = st.columns([3, 1])
            with col_sv1:
                v_label = st.text_input("Version Tag", value="v2.0 Revision", placeholder="e.g. Added Docker, v2.1")
                v_notes = st.text_input("Revision Notes", placeholder="e.g. Optimized metrics in experience bullets")
            with col_sv2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("Save Snapshot", type="primary"):
                    qa = st.session_state["quality_analysis"]
                    aa = st.session_state["ats_analysis"]
                    ja = st.session_state["job_match_analysis"]

                    save_analysis(
                        resume_name=st.session_state["resume_file_name"],
                        job_title=st.session_state.get("target_job_title", ""),
                        overall_score=qa["quality_score"],
                        tfidf_score=ja.get("tfidf_score_pct", 0.0),
                        skill_score=ja.get("required_skills", {}).get("coverage_pct", 0.0),
                        matched_skills=ja.get("required_skills", {}).get("matched", []),
                        missing_skills=ja.get("required_skills", {}).get("missing", []),
                        notes=v_notes,
                        quality_score=qa["quality_score"],
                        ats_score=aa["ats_score"],
                        job_match_score=ja.get("job_match_score", 0.0),
                        quality_breakdown=qa["breakdown"],
                        ats_breakdown=aa["breakdown"],
                        job_match_breakdown=ja.get("required_skills", {}),
                        version_label=v_label,
                        db_path=DB_PATH,
                    )
                    st.success("Snapshot recorded!")
                    st.rerun()

    records = get_all_analyses(DB_PATH)

    if not records:
        st.info("No saved records found. Run an analysis and save a snapshot to start tracking history.")
    else:
        # Comparison Selector
        if len(records) >= 2:
            st.markdown("### 🔀 Version Diff & Comparison")
            c_sel1, c_sel2, c_btn = st.columns([2, 2, 1])
            record_options = {r["id"]: f"#{r['id']}: {r['resume_name']} ({r.get('version_label', 'v1.0')}) - {r['timestamp']}" for r in records}

            with c_sel1:
                id_a = st.selectbox("Baseline (Version A)", options=list(record_options.keys()), index=1, format_func=lambda x: record_options[x])
            with c_sel2:
                id_b = st.selectbox("Updated (Version B)", options=list(record_options.keys()), index=0, format_func=lambda x: record_options[x])
            with c_btn:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                do_compare = st.button("Compare Versions", type="primary")

            if do_compare or "diff_result" in st.session_state:
                diff = compare_analysis_records(id_a, id_b, DB_PATH)
                if diff:
                    st.markdown("#### Score Deltas (Version B vs Version A)")
                    d_c1, d_c2, d_c3 = st.columns(3)
                    with d_c1:
                        st.metric("Quality Delta", f"{diff['record_b'].get('quality_score', 0)}%", f"{diff['quality_score_delta']:+0.1f}%")
                    with d_c2:
                        st.metric("ATS Compatibility Delta", f"{diff['record_b'].get('ats_score', 0)}%", f"{diff['ats_score_delta']:+0.1f}%")
                    with d_c3:
                        st.metric("Job Match Delta", f"{diff['record_b'].get('job_match_score', 0)}%", f"{diff['job_match_delta']:+0.1f}%")

                    if diff["newly_added_skills"]:
                        st.markdown(f"**Newly Added Skills:** `{', '.join(diff['newly_added_skills'])}`")
                    if diff["removed_skills"]:
                        st.markdown(f"**Removed Skills:** `{', '.join(diff['removed_skills'])}`")

        st.markdown("---")
        st.markdown("### 📋 All Saved Historical Records")

        col_act1, col_act2 = st.columns([4, 1])
        with col_act2:
            if st.button("🗑 Wipe All Records", type="secondary"):
                clear_all_analyses(DB_PATH)
                st.rerun()

        for rec in records:
            with st.expander(f"Record #{rec['id']}: {rec['resume_name']} [{rec.get('version_label', 'v1.0')}] — Quality: {rec.get('quality_score', rec['overall_score'])}% | ATS: {rec.get('ats_score', 85)}% ({rec['timestamp']})"):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.markdown(f"**Target Role:** {rec['job_title']}")
                    st.markdown(f"**Notes:** {rec['notes'] or 'None'}")
                with c2:
                    st.markdown(f"**Quality Score:** {rec.get('quality_score', rec['overall_score'])}%")
                    st.markdown(f"**ATS Compatibility:** {rec.get('ats_score', 85)}%")
                    st.markdown(f"**Job Match:** {rec.get('job_match_score', 0)}%")
                with c3:
                    if st.button("Delete", key=f"del_rec_{rec['id']}", type="secondary"):
                        delete_analysis(rec["id"], DB_PATH)
                        st.success(f"Record #{rec['id']} deleted.")
                        st.rerun()


# =============================================================================
# PAGE 10: SETTINGS & API CONFIGURATION
# =============================================================================
elif selected_page == "⚙ Settings & API":
    st.markdown("## ⚙ Settings & API Configuration")
    st.caption("Configure AI providers, inspect local data storage, and review privacy policies.")

    with st.container(border=True):
        st.markdown("### 🤖 AI Provider Configuration")
        provider_choice = st.selectbox(
            "Select Active AI Engine",
            ["local (Built-in Rule-Based / Zero-Key)", "gemini (Google Gemini API)", "openai (OpenAI API)"],
            index=0,
        )

        if "gemini" in provider_choice:
            gemini_key = st.text_input("Google Gemini API Key", type="password", value=AI_CONFIG["gemini_api_key"])
            if st.button("Save Gemini Key", type="primary"):
                os.environ["GEMINI_API_KEY"] = gemini_key
                AI_CONFIG["gemini_api_key"] = gemini_key
                AI_CONFIG["default_provider"] = "gemini"
                st.session_state.ai_assistant = ResumeAssistant(provider="gemini", api_key=gemini_key)
                st.success("Gemini API key configured!")
        elif "openai" in provider_choice:
            openai_key = st.text_input("OpenAI API Key", type="password", value=AI_CONFIG["openai_api_key"])
            if st.button("Save OpenAI Key", type="primary"):
                os.environ["OPENAI_API_KEY"] = openai_key
                AI_CONFIG["openai_api_key"] = openai_key
                AI_CONFIG["default_provider"] = "openai"
                st.session_state.ai_assistant = ResumeAssistant(provider="openai", api_key=openai_key)
                st.success("OpenAI API key configured!")
        else:
            st.info("Using built-in deterministic local engine. No external API keys or cloud calls required.")

    with st.container(border=True):
        st.markdown("### 🔒 Privacy & Data Retention")
        st.markdown(
            f"""
            - **Local Database Path:** `{DB_PATH}`
            - **Raw Resume Text Retention:** Never saved permanently to disk.
            - **Encrypted Transmission:** Zero network traffic sent during local mode.
            """
        )
        if st.button("Reset Local Database"):
            clear_all_analyses(DB_PATH)
            st.success("Database reset to clean state.")
