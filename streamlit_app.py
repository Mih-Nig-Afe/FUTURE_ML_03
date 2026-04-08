"""Recruiter-facing Streamlit interface for resume screening and ranking."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import ROLE_PROFILES
from src.kaggle_ingestion import (
    DEFAULT_RESUME_DATASET,
    ingest_resume_dataset_from_kaggle,
)
from src.pipeline import ResumeScreeningPipeline

DEFAULT_RESUME_PATH = Path("data/raw/resumes_sample.csv")
DEFAULT_KAGGLE_MAPPED_PATH = Path("data/raw/resumes_kaggle_mapped.csv")
DEFAULT_JOB_PATH = Path("data/raw/job_description_data_scientist.txt")


def _load_text(path: Path, fallback: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return fallback


def _explode_skills(column: pd.Series) -> pd.Series:
    return (
        column.fillna("")
        .astype(str)
        .str.split(",")
        .explode()
        .str.strip()
        .replace("", pd.NA)
        .dropna()
    )


def _run_screening(
    resume_df: pd.DataFrame, job_description: str, role: str
) -> tuple[pd.DataFrame, dict]:
    pipeline = ResumeScreeningPipeline()
    ranking_df, summary = pipeline.score_resumes(
        resumes_df=resume_df,
        job_description=job_description,
        role=role,
    )
    return ranking_df, summary


def main() -> None:
    st.set_page_config(page_title="Recruiter Resume Screening", layout="wide")

    st.title("Recruiter Resume Screening Dashboard")
    st.caption(
        "Score, rank, and explain candidate fit against a target role using NLP-driven resume analysis."
    )

    with st.sidebar:
        st.header("Screening Setup")
        role = st.selectbox(
            "Target role", options=sorted(ROLE_PROFILES.keys()), index=0
        )

        source_type = st.radio(
            "Resume source",
            options=["Sample data", "Mapped Kaggle dataset", "Upload CSV"],
            index=0,
        )

        resume_df: pd.DataFrame | None = None

        if source_type == "Sample data":
            if DEFAULT_RESUME_PATH.exists():
                resume_df = pd.read_csv(DEFAULT_RESUME_PATH)
                st.success(f"Loaded sample resumes from {DEFAULT_RESUME_PATH}")
            else:
                st.error("Sample resume file not found.")

        elif source_type == "Mapped Kaggle dataset":
            st.write(
                "Required Kaggle source used for ingestion: "
                f"{DEFAULT_RESUME_DATASET}"
            )
            if st.button(
                "Download + map Kaggle resume dataset", use_container_width=True
            ):
                try:
                    output_path = ingest_resume_dataset_from_kaggle(
                        dataset_slug=DEFAULT_RESUME_DATASET,
                        download_dir=Path("data/raw/kaggle"),
                        extract_dir=Path("data/raw/kaggle/extracted/resume-dataset"),
                        output_csv=DEFAULT_KAGGLE_MAPPED_PATH,
                        skip_download=False,
                    )
                    st.success(f"Dataset mapped successfully: {output_path}")
                except Exception as exc:
                    st.error(f"Kaggle ingestion failed: {exc}")

            if DEFAULT_KAGGLE_MAPPED_PATH.exists():
                resume_df = pd.read_csv(DEFAULT_KAGGLE_MAPPED_PATH)
                st.success(
                    f"Loaded mapped Kaggle data from {DEFAULT_KAGGLE_MAPPED_PATH}"
                )
            else:
                st.info(
                    "No mapped Kaggle file found yet. Use the button above to create it."
                )

        else:
            uploaded_csv = st.file_uploader("Upload resumes CSV", type=["csv"])
            if uploaded_csv is not None:
                resume_df = pd.read_csv(uploaded_csv)
                st.success("Uploaded CSV loaded.")

        st.divider()
        st.subheader("Job Description")

        default_job_text = _load_text(
            DEFAULT_JOB_PATH,
            fallback=(
                "Data Scientist role requiring Python, SQL, Statistics, Machine Learning, "
                "pandas, scikit-learn, and data visualization."
            ),
        )
        uploaded_job = st.file_uploader("Upload job description (.txt)", type=["txt"])

        if uploaded_job is not None:
            job_description = uploaded_job.read().decode("utf-8", errors="ignore")
        else:
            job_description = st.text_area(
                "Job description text",
                value=default_job_text,
                height=260,
            )

        run_clicked = st.button(
            "Run Screening", type="primary", use_container_width=True
        )

    if not run_clicked:
        st.info("Configure inputs in the sidebar, then click Run Screening.")
        return

    if resume_df is None:
        st.error("No resume dataset is currently loaded.")
        return

    if "resume_text" not in resume_df.columns:
        st.error("Resume input must include a resume_text column.")
        return

    try:
        ranking_df, summary = _run_screening(
            resume_df=resume_df,
            job_description=job_description,
            role=role,
        )
    except Exception as exc:
        st.error(f"Screening failed: {exc}")
        return

    top_candidate = summary.get("top_candidate", "N/A")
    avg_score = (
        float(ranking_df["final_fit_score"].mean()) if not ranking_df.empty else 0.0
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Candidates screened", int(summary.get("total_candidates", 0)))
    col2.metric("Top candidate", str(top_candidate))
    col3.metric("Average fit score", f"{avg_score:.2f}")

    st.subheader("Candidate Ranking")
    st.dataframe(
        ranking_df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Top 10 Fit Scores")
    top_10 = ranking_df.head(10).set_index("candidate_name")
    st.bar_chart(top_10["final_fit_score"])

    st.subheader("Skill Gap Explorer")
    candidate_names = ranking_df["candidate_name"].tolist()
    selected_candidate = st.selectbox("Select candidate", options=candidate_names)
    selected_row = ranking_df[ranking_df["candidate_name"] == selected_candidate].iloc[
        0
    ]

    gap_col1, gap_col2, gap_col3 = st.columns(3)
    gap_col1.write("Matched required skills")
    gap_col1.write(selected_row["matched_required_skills"] or "None")

    gap_col2.write("Matched important skills")
    gap_col2.write(selected_row["matched_important_skills"] or "None")

    gap_col3.write("Missing required skills")
    gap_col3.write(selected_row["missing_required_skills"] or "None")

    st.subheader("Most Frequent Missing Required Skills")
    missing_skills = _explode_skills(ranking_df["missing_required_skills"])
    if missing_skills.empty:
        st.success("No required skill gaps detected in this run.")
    else:
        missing_counts = missing_skills.value_counts().head(15)
        st.bar_chart(missing_counts)

    csv_data = ranking_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download ranking CSV",
        data=csv_data,
        file_name="candidate_ranking_streamlit.csv",
        mime="text/csv",
    )

    st.download_button(
        label="Download screening summary JSON",
        data=json.dumps(summary, indent=2).encode("utf-8"),
        file_name="screening_summary_streamlit.json",
        mime="application/json",
    )


if __name__ == "__main__":
    main()
