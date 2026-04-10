"""Recruiter-facing Streamlit interface for resume screening and ranking."""

from __future__ import annotations

import errno
import json
import time
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import ROLE_PROFILES
from src.kaggle_ingestion import (
    DEFAULT_JOB_DATASET,
    DEFAULT_JOB_DESCRIPTION_DATASET,
    DEFAULT_RESUME_DATASET,
    ingest_task3_required_datasets,
)
from src.pipeline import ResumeScreeningPipeline

DEFAULT_KAGGLE_MAPPED_PATH = Path("data/raw/resumes_kaggle_mapped.csv")
DEFAULT_JOBS_MAPPED_PATH = Path("data/raw/job_descriptions_kaggle_mapped.csv")
DEFAULT_GENERATED_JD_PATH = Path(
    "data/raw/job_description_generated_data_scientist.txt"
)
DEFAULT_KAGGLE_DOWNLOAD_DIR = Path("data/raw/kaggle")
TASK3_REQUIRED_ARCHIVES = (
    DEFAULT_KAGGLE_DOWNLOAD_DIR / "resume-dataset.zip",
    DEFAULT_KAGGLE_DOWNLOAD_DIR / "job-description-dataset.zip",
    DEFAULT_KAGGLE_DOWNLOAD_DIR / "us-jobs-on-monstercom.zip",
)
EDEADLOCK_RETRIES = 5
EDEADLOCK_INITIAL_DELAY_SECONDS = 0.2


def _read_path_bytes_with_retry(path: Path) -> bytes:
    delay = EDEADLOCK_INITIAL_DELAY_SECONDS
    for attempt in range(1, EDEADLOCK_RETRIES + 1):
        try:
            return path.read_bytes()
        except OSError as exc:
            if exc.errno != errno.EDEADLK or attempt == EDEADLOCK_RETRIES:
                raise
            time.sleep(delay)
            delay *= 2

    raise RuntimeError("Unreachable retry state while reading file bytes.")


def _load_csv(path: Path) -> pd.DataFrame:
    payload = _read_path_bytes_with_retry(path)
    return pd.read_csv(BytesIO(payload))


def _load_text(path: Path, fallback: str) -> str:
    if not path.exists():
        return fallback

    try:
        payload = _read_path_bytes_with_retry(path)
    except OSError as exc:
        if exc.errno == errno.EDEADLK:
            return fallback
        raise

    return payload.decode("utf-8", errors="ignore")


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
            options=["Mapped Task 3 Kaggle data", "Upload CSV"],
            index=0,
        )

        resume_df: pd.DataFrame | None = None

        if source_type == "Mapped Task 3 Kaggle data":
            st.write(
                "Required Task 3 Kaggle datasets used: "
                f"{DEFAULT_RESUME_DATASET}, "
                f"{DEFAULT_JOB_DATASET}, "
                f"{DEFAULT_JOB_DESCRIPTION_DATASET}"
            )
            if st.button(
                "Download + map all Task 3 Kaggle datasets", use_container_width=True
            ):
                try:
                    use_local_archives = all(
                        archive_path.exists()
                        for archive_path in TASK3_REQUIRED_ARCHIVES
                    )
                    artifacts = ingest_task3_required_datasets(
                        download_dir=DEFAULT_KAGGLE_DOWNLOAD_DIR,
                        extract_dir=Path("data/raw/kaggle/extracted"),
                        resumes_output_csv=DEFAULT_KAGGLE_MAPPED_PATH,
                        jobs_output_csv=DEFAULT_JOBS_MAPPED_PATH,
                        generated_jd_output_txt=DEFAULT_GENERATED_JD_PATH,
                        role_key=role,
                        skip_download=use_local_archives,
                    )
                    if use_local_archives:
                        st.info(
                            "Using existing Kaggle ZIP archives from data/raw/kaggle. "
                            "Delete those ZIP files if you want to force fresh download."
                        )
                    st.success("Task 3 datasets mapped successfully.")
                    st.write(artifacts)
                except Exception as exc:
                    st.error(f"Kaggle ingestion failed: {exc}")

            if DEFAULT_KAGGLE_MAPPED_PATH.exists():
                try:
                    resume_df = _load_csv(DEFAULT_KAGGLE_MAPPED_PATH)
                    st.success(
                        f"Loaded mapped Kaggle data from {DEFAULT_KAGGLE_MAPPED_PATH}"
                    )
                except Exception as exc:
                    st.error(f"Could not load mapped Kaggle resumes: {exc}")
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

        job_source = st.radio(
            "Job description source",
            options=[
                "Generated from mapped Task 3 job datasets",
                "Upload .txt / edit manually",
            ],
            index=0,
        )

        default_job_text = (
            "Paste a role-specific job description here or upload a .txt file."
        )

        generated_job_text = _load_text(
            DEFAULT_GENERATED_JD_PATH,
            fallback="",
        )
        if DEFAULT_GENERATED_JD_PATH.exists() and not generated_job_text:
            st.warning(
                "Generated job description file exists but could not be read right now. "
                "You can still paste/upload text or regenerate Task 3 datasets."
            )

        if job_source == "Generated from mapped Task 3 job datasets":
            if not DEFAULT_GENERATED_JD_PATH.exists():
                st.info(
                    "Generated job description not found yet. "
                    "Run Task 3 Kaggle ingestion from the resume source section."
                )
            job_description = st.text_area(
                "Generated job description text",
                value=generated_job_text or default_job_text,
                height=260,
                key="job_description_generated",
            )
        else:
            uploaded_job = st.file_uploader(
                "Upload job description (.txt)",
                type=["txt"],
                key="uploaded_job_description",
            )
            if uploaded_job is not None:
                default_job_text = uploaded_job.read().decode("utf-8", errors="ignore")
            job_description = st.text_area(
                "Job description text",
                value=default_job_text,
                height=260,
                key="job_description_manual",
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
