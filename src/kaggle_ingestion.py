"""Kaggle ingestion helpers for Future Interns ML Task 3 resume screening."""

from __future__ import annotations

import argparse
import errno
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile

import pandas as pd

DEFAULT_RESUME_DATASET = "snehaanbhawal/resume-dataset"
DEFAULT_JOB_DATASET = "ravindrasinghrana/job-description-dataset"
DEFAULT_JOB_DESCRIPTION_DATASET = "PromptCloudHQ/us-jobs-on-monstercom"

REQUIRED_TASK3_DATASETS: tuple[str, ...] = (
    DEFAULT_RESUME_DATASET,
    DEFAULT_JOB_DATASET,
    DEFAULT_JOB_DESCRIPTION_DATASET,
)
EDEADLOCK_RETRIES = 5
EDEADLOCK_INITIAL_DELAY_SECONDS = 0.2

TEXT_COLUMN_CANDIDATES: tuple[str, ...] = (
    "resume_text",
    "resume_str",
    "resume",
    "text",
    "description",
    "content",
)

NAME_COLUMN_CANDIDATES: tuple[str, ...] = (
    "candidate_name",
    "name",
    "full_name",
    "applicant_name",
)

RESUME_CATEGORY_COLUMN_CANDIDATES: tuple[str, ...] = (
    "category",
    "job_category",
    "label",
)

JOB_DESCRIPTION_COLUMN_CANDIDATES: tuple[str, ...] = (
    "job_description",
    "jobdescription",
    "description",
    "details",
    "text",
    "content",
    "summary",
)

JOB_TITLE_COLUMN_CANDIDATES: tuple[str, ...] = (
    "job_title",
    "title",
    "designation",
    "position",
    "role",
)

JOB_CATEGORY_COLUMN_CANDIDATES: tuple[str, ...] = (
    "category",
    "industry",
    "job_category",
    "function",
    "department",
    "employment_type",
)


def _normalize_column_name(column_name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", column_name.strip().lower())


def _pick_first_existing(
    columns: Iterable[str], candidates: tuple[str, ...]
) -> str | None:
    normalized = {_normalize_column_name(column): column for column in columns}
    for candidate in candidates:
        normalized_candidate = _normalize_column_name(candidate)
        if normalized_candidate in normalized:
            return normalized[normalized_candidate]
    return None


def _slug_to_archive_name(dataset_slug: str) -> str:
    return f"{dataset_slug.split('/')[-1]}.zip"


def _slug_to_folder_name(dataset_slug: str) -> str:
    return dataset_slug.split("/")[-1]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _resolve_kaggle_config_path() -> Path:
    config_dir = os.getenv("KAGGLE_CONFIG_DIR")
    if config_dir:
        return Path(config_dir) / "kaggle.json"
    return Path.home() / ".kaggle" / "kaggle.json"


def _run_with_deadlock_retry(action):
    delay = EDEADLOCK_INITIAL_DELAY_SECONDS
    for attempt in range(1, EDEADLOCK_RETRIES + 1):
        try:
            return action()
        except OSError as exc:
            if exc.errno != errno.EDEADLK or attempt == EDEADLOCK_RETRIES:
                raise
            time.sleep(delay)
            delay *= 2

    raise RuntimeError("Unreachable retry state while handling file operation.")


def _validate_kaggle_credentials() -> None:
    api_token = os.getenv("KAGGLE_API_TOKEN", "").strip()
    if api_token:
        return

    username = os.getenv("KAGGLE_USERNAME", "").strip()
    key = os.getenv("KAGGLE_KEY", "").strip()
    if username and key:
        return

    config_path = _resolve_kaggle_config_path()
    if not config_path.exists():
        raise RuntimeError(
            "Kaggle credentials not found. Set KAGGLE_API_TOKEN (preferred) "
            "or KAGGLE_USERNAME and KAGGLE_KEY, "
            f"or provide a valid {config_path}."
        )

    try:
        payload = json.loads(
            _run_with_deadlock_retry(lambda: config_path.read_text(encoding="utf-8"))
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Invalid Kaggle config at {config_path}: {exc}") from exc

    if payload.get("api_token") or payload.get("token"):
        return

    if payload.get("username") and payload.get("key"):
        return

    raise RuntimeError(
        f"Invalid Kaggle config at {config_path}: expected api_token or username/key fields."
    )


def download_kaggle_dataset(dataset_slug: str, download_dir: Path) -> Path:
    """Download dataset archive using the Kaggle CLI command format required by Task 3."""
    _validate_kaggle_credentials()
    download_dir.mkdir(parents=True, exist_ok=True)

    command = [
        "kaggle",
        "datasets",
        "download",
        dataset_slug,
        "-p",
        str(download_dir),
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        details = stderr or stdout or "No additional output from Kaggle CLI."
        raise RuntimeError(f"Kaggle download failed for {dataset_slug}. {details}")

    expected_archive = download_dir / _slug_to_archive_name(dataset_slug)
    if expected_archive.exists():
        return expected_archive

    archives = sorted(download_dir.glob("*.zip"), key=lambda item: item.stat().st_mtime)
    if not archives:
        raise FileNotFoundError(
            "Kaggle download finished but no ZIP archive was found in download_dir."
        )
    return archives[-1]


def extract_archive(archive_path: Path, extract_dir: Path) -> None:
    extract_dir.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)


def _safe_write_csv(dataframe: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        _run_with_deadlock_retry(output_path.unlink)
    _run_with_deadlock_retry(lambda: dataframe.to_csv(output_path, index=False))


def _safe_write_text(text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        _run_with_deadlock_retry(output_path.unlink)
    _run_with_deadlock_retry(lambda: output_path.write_text(text, encoding="utf-8"))


def _read_probe_csv(csv_path: Path, nrows: int = 50) -> pd.DataFrame | None:
    try:
        return pd.read_csv(csv_path, nrows=nrows)
    except Exception:
        return None


def _find_source_csv_by_columns(
    extract_dir: Path,
    required_any_columns: tuple[str, ...],
) -> Path:
    csv_files = sorted(extract_dir.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found under {extract_dir}")

    for csv_file in csv_files:
        probe = _read_probe_csv(csv_file)
        if probe is None:
            continue
        if _pick_first_existing(probe.columns, required_any_columns):
            return csv_file

    raise ValueError(
        "No compatible CSV file found with any of the candidate columns: "
        f"{required_any_columns}"
    )


def _read_probe_csv_from_archive_member(
    zip_ref: ZipFile,
    member_name: str,
    nrows: int = 50,
) -> pd.DataFrame | None:
    try:
        with zip_ref.open(member_name) as source:
            return pd.read_csv(source, nrows=nrows)
    except Exception:
        return None


def _load_source_dataframe_from_archive(
    archive_path: Path,
    required_any_columns: tuple[str, ...],
) -> pd.DataFrame:
    with ZipFile(archive_path, "r") as zip_ref:
        csv_members = sorted(
            member for member in zip_ref.namelist() if member.lower().endswith(".csv")
        )
        if not csv_members:
            raise FileNotFoundError(
                f"No CSV files found in archive {archive_path.name}."
            )

        selected_member: str | None = None
        for member_name in csv_members:
            probe = _read_probe_csv_from_archive_member(zip_ref, member_name)
            if probe is None:
                continue
            if _pick_first_existing(probe.columns, required_any_columns):
                selected_member = member_name
                break

        if selected_member is None:
            raise ValueError(
                "No compatible CSV file found in archive with candidate columns: "
                f"{required_any_columns}"
            )

        with zip_ref.open(selected_member) as source:
            return pd.read_csv(source)


def infer_role_key(text: str) -> str:
    lowered = text.lower()

    data_scientist_keywords = (
        "data scientist",
        "data science",
        "machine learning scientist",
    )
    ml_engineer_keywords = (
        "ml engineer",
        "machine learning engineer",
        "ai engineer",
        "mle",
    )
    data_analyst_keywords = (
        "data analyst",
        "business analyst",
        "analytics analyst",
    )

    if any(keyword in lowered for keyword in data_scientist_keywords):
        return "data_scientist"
    if any(keyword in lowered for keyword in ml_engineer_keywords):
        return "ml_engineer"
    if any(keyword in lowered for keyword in data_analyst_keywords):
        return "data_analyst"
    return "unknown"


def map_resume_dataframe(input_df: pd.DataFrame) -> pd.DataFrame:
    """Map source dataframe into candidate_id/candidate_name/resume_text schema."""
    text_column = _pick_first_existing(input_df.columns, TEXT_COLUMN_CANDIDATES)
    if not text_column:
        raise ValueError(
            "Could not map resume text column. Expected one of: "
            f"{TEXT_COLUMN_CANDIDATES}"
        )

    name_column = _pick_first_existing(input_df.columns, NAME_COLUMN_CANDIDATES)
    category_column = _pick_first_existing(
        input_df.columns, RESUME_CATEGORY_COLUMN_CANDIDATES
    )

    mapped = pd.DataFrame(
        {
            "resume_text": input_df[text_column].fillna("").astype(str),
            "candidate_name": (
                input_df[name_column].fillna("").astype(str) if name_column else ""
            ),
            "source_category": (
                input_df[category_column].fillna("").astype(str)
                if category_column
                else "unknown"
            ),
        }
    )

    mapped["resume_text"] = mapped["resume_text"].map(normalize_whitespace)
    mapped = mapped[mapped["resume_text"].ne("")].copy().reset_index(drop=True)

    fallback_names = [f"Kaggle Candidate {idx}" for idx in range(1, len(mapped) + 1)]
    if name_column:
        mapped["candidate_name"] = (
            mapped["candidate_name"]
            .replace("", pd.NA)
            .fillna(pd.Series(fallback_names))
        )
    else:
        mapped["candidate_name"] = fallback_names

    mapped.insert(
        0, "candidate_id", [f"KG_{idx:05d}" for idx in range(1, len(mapped) + 1)]
    )
    return mapped[["candidate_id", "candidate_name", "resume_text", "source_category"]]


def map_job_dataframe(input_df: pd.DataFrame, dataset_slug: str) -> pd.DataFrame:
    """Map job dataset rows into a normalized job description schema."""
    description_column = _pick_first_existing(
        input_df.columns, JOB_DESCRIPTION_COLUMN_CANDIDATES
    )
    if not description_column:
        raise ValueError(
            "Could not map job description text column. Expected one of: "
            f"{JOB_DESCRIPTION_COLUMN_CANDIDATES}"
        )

    title_column = _pick_first_existing(input_df.columns, JOB_TITLE_COLUMN_CANDIDATES)
    category_column = _pick_first_existing(
        input_df.columns, JOB_CATEGORY_COLUMN_CANDIDATES
    )

    mapped = pd.DataFrame(
        {
            "job_description_text": input_df[description_column].fillna("").astype(str),
            "job_title": (
                input_df[title_column].fillna("").astype(str) if title_column else ""
            ),
            "source_category": (
                input_df[category_column].fillna("").astype(str)
                if category_column
                else "unknown"
            ),
        }
    )

    mapped["job_description_text"] = mapped["job_description_text"].map(
        normalize_whitespace
    )
    mapped = mapped[mapped["job_description_text"].ne("")].copy().reset_index(drop=True)

    fallback_titles = [f"Job Posting {idx}" for idx in range(1, len(mapped) + 1)]
    mapped["job_title"] = (
        mapped["job_title"].replace("", pd.NA).fillna(pd.Series(fallback_titles))
    )

    mapped["role_key"] = (
        (
            mapped["job_title"]
            + " "
            + mapped["source_category"]
            + " "
            + mapped["job_description_text"]
        )
        .map(infer_role_key)
        .astype(str)
    )

    slug_label = _slug_to_folder_name(dataset_slug)
    mapped.insert(
        0,
        "job_id",
        [f"{slug_label[:3].upper()}_{idx:06d}" for idx in range(1, len(mapped) + 1)],
    )
    mapped["source_dataset"] = dataset_slug
    return mapped[
        [
            "job_id",
            "job_title",
            "role_key",
            "job_description_text",
            "source_category",
            "source_dataset",
        ]
    ]


def _prepare_archive(
    dataset_slug: str,
    download_dir: Path,
    extract_root_dir: Path,
    skip_download: bool,
) -> Path:
    _ = extract_root_dir
    archive_path = download_dir / _slug_to_archive_name(dataset_slug)
    if not skip_download:
        archive_path = download_kaggle_dataset(
            dataset_slug=dataset_slug, download_dir=download_dir
        )
    if not archive_path.exists():
        raise FileNotFoundError(
            f"Expected archive at {archive_path}. Download first or remove --skip-download."
        )

    return archive_path


def ingest_resume_dataset_from_kaggle(
    dataset_slug: str,
    download_dir: Path,
    extract_dir: Path,
    output_csv: Path,
    skip_download: bool = False,
) -> Path:
    """Download and map a Kaggle resume dataset into pipeline schema."""
    archive_path = _prepare_archive(
        dataset_slug=dataset_slug,
        download_dir=download_dir,
        extract_root_dir=extract_dir,
        skip_download=skip_download,
    )

    source_df = _load_source_dataframe_from_archive(
        archive_path=archive_path,
        required_any_columns=TEXT_COLUMN_CANDIDATES,
    )
    mapped_df = map_resume_dataframe(source_df)

    _safe_write_csv(mapped_df, output_csv)
    return output_csv


def ingest_job_dataset_from_kaggle(
    dataset_slug: str,
    download_dir: Path,
    extract_dir: Path,
    output_csv: Path,
    skip_download: bool = False,
) -> Path:
    """Download and map a Kaggle job dataset into normalized job schema."""
    archive_path = _prepare_archive(
        dataset_slug=dataset_slug,
        download_dir=download_dir,
        extract_root_dir=extract_dir,
        skip_download=skip_download,
    )

    source_df = _load_source_dataframe_from_archive(
        archive_path=archive_path,
        required_any_columns=JOB_DESCRIPTION_COLUMN_CANDIDATES,
    )
    mapped_df = map_job_dataframe(source_df, dataset_slug=dataset_slug)

    _safe_write_csv(mapped_df, output_csv)
    return output_csv


def build_role_job_description_text(
    mapped_jobs_df: pd.DataFrame,
    role_key: str,
    max_rows: int = 25,
) -> str:
    """Build a role-targeted job description text from mapped Kaggle job postings."""
    role_filtered = mapped_jobs_df[mapped_jobs_df["role_key"].eq(role_key)].copy()
    if role_filtered.empty:
        role_filtered = mapped_jobs_df.copy()

    selected = role_filtered.head(max_rows)
    chunks = selected["job_description_text"].fillna("").astype(str).tolist()
    chunks = [
        normalize_whitespace(chunk) for chunk in chunks if normalize_whitespace(chunk)
    ]

    return "\n\n".join(chunks)


def ingest_task3_required_datasets(
    download_dir: Path,
    extract_dir: Path,
    resumes_output_csv: Path,
    jobs_output_csv: Path,
    generated_jd_output_txt: Path,
    role_key: str = "data_scientist",
    skip_download: bool = False,
) -> dict[str, str]:
    """Ingest all required Task 3 datasets and produce normalized artifacts."""
    resumes_path = ingest_resume_dataset_from_kaggle(
        dataset_slug=DEFAULT_RESUME_DATASET,
        download_dir=download_dir,
        extract_dir=extract_dir,
        output_csv=resumes_output_csv,
        skip_download=skip_download,
    )

    mapped_job_frames: list[pd.DataFrame] = []
    for dataset_slug in (DEFAULT_JOB_DATASET, DEFAULT_JOB_DESCRIPTION_DATASET):
        output_path = (
            extract_dir / "mapped" / f"{_slug_to_folder_name(dataset_slug)}_mapped.csv"
        )
        ingest_job_dataset_from_kaggle(
            dataset_slug=dataset_slug,
            download_dir=download_dir,
            extract_dir=extract_dir,
            output_csv=output_path,
            skip_download=skip_download,
        )
        mapped_job_frames.append(pd.read_csv(output_path))

    combined_jobs = pd.concat(mapped_job_frames, ignore_index=True)
    _safe_write_csv(combined_jobs, jobs_output_csv)

    generated_jd = build_role_job_description_text(
        mapped_jobs_df=combined_jobs,
        role_key=role_key,
    )
    _safe_write_text(generated_jd, generated_jd_output_txt)

    return {
        "resumes": str(resumes_path),
        "jobs": str(jobs_output_csv),
        "generated_job_description": str(generated_jd_output_txt),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest required Kaggle datasets for Task 3 and map them into screening-ready schemas."
        )
    )

    parser.add_argument(
        "--mode",
        choices=["resume", "jobs", "all"],
        default="all",
        help="Ingestion mode: one resume dataset, one jobs dataset, or all required Task 3 datasets.",
    )
    parser.add_argument(
        "--dataset",
        default=DEFAULT_RESUME_DATASET,
        help="Kaggle dataset slug used for single-dataset resume/jobs modes.",
    )
    parser.add_argument(
        "--download-dir",
        default="data/raw/kaggle",
        help="Directory where Kaggle ZIP archives are stored.",
    )
    parser.add_argument(
        "--extract-dir",
        default="data/raw/kaggle/extracted",
        help="Root directory for extracted dataset files.",
    )
    parser.add_argument(
        "--output",
        default="data/raw/resumes_kaggle_mapped.csv",
        help="Output CSV path used for single-dataset resume/jobs modes.",
    )
    parser.add_argument(
        "--resumes-output",
        default="data/raw/resumes_kaggle_mapped.csv",
        help="Output CSV for mapped resumes in --mode all.",
    )
    parser.add_argument(
        "--jobs-output",
        default="data/raw/job_descriptions_kaggle_mapped.csv",
        help="Output CSV for combined mapped jobs in --mode all.",
    )
    parser.add_argument(
        "--generated-jd-output",
        default="data/raw/job_description_generated_data_scientist.txt",
        help="Output text file for generated role-specific job description in --mode all.",
    )
    parser.add_argument(
        "--role",
        default="data_scientist",
        help="Role key used when generating job_description text in --mode all.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip Kaggle download commands and use existing ZIP files from --download-dir.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    download_dir = Path(args.download_dir)
    extract_dir = Path(args.extract_dir)

    if args.mode == "resume":
        output = ingest_resume_dataset_from_kaggle(
            dataset_slug=args.dataset,
            download_dir=download_dir,
            extract_dir=extract_dir,
            output_csv=Path(args.output),
            skip_download=args.skip_download,
        )
        print(f"Mapped resume dataset saved to: {output}")
        return

    if args.mode == "jobs":
        output = ingest_job_dataset_from_kaggle(
            dataset_slug=args.dataset,
            download_dir=download_dir,
            extract_dir=extract_dir,
            output_csv=Path(args.output),
            skip_download=args.skip_download,
        )
        print(f"Mapped job dataset saved to: {output}")
        return

    artifacts = ingest_task3_required_datasets(
        download_dir=download_dir,
        extract_dir=extract_dir,
        resumes_output_csv=Path(args.resumes_output),
        jobs_output_csv=Path(args.jobs_output),
        generated_jd_output_txt=Path(args.generated_jd_output),
        role_key=args.role,
        skip_download=args.skip_download,
    )

    print("Task 3 Kaggle ingestion completed for required datasets:")
    for dataset_slug in REQUIRED_TASK3_DATASETS:
        print(f"- {dataset_slug}")
    print(f"Mapped resumes: {artifacts['resumes']}")
    print(f"Mapped jobs: {artifacts['jobs']}")
    print(f"Generated role JD: {artifacts['generated_job_description']}")


if __name__ == "__main__":
    main()
