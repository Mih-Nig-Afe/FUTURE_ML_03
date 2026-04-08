"""Direct Kaggle ingestion helpers for ML Task 3 resume screening."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile

import pandas as pd

DEFAULT_RESUME_DATASET = "snehaanbhawal/resume-dataset"

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

CATEGORY_COLUMN_CANDIDATES: tuple[str, ...] = (
    "category",
    "job_category",
    "label",
)


def _pick_first_existing(
    columns: Iterable[str], candidates: tuple[str, ...]
) -> str | None:
    lowered_map = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate in lowered_map:
            return lowered_map[candidate]
    return None


def _slug_to_archive_name(dataset_slug: str) -> str:
    return f"{dataset_slug.split('/')[-1]}.zip"


def download_kaggle_dataset(dataset_slug: str, download_dir: Path) -> Path:
    """Download dataset archive using the Kaggle CLI command format requested in task prompt."""
    download_dir.mkdir(parents=True, exist_ok=True)

    command = [
        "kaggle",
        "datasets",
        "download",
        dataset_slug,
        "-p",
        str(download_dir),
    ]
    subprocess.run(command, check=True)

    expected_archive = download_dir / _slug_to_archive_name(dataset_slug)
    if expected_archive.exists():
        return expected_archive

    candidates = sorted(
        download_dir.glob("*.zip"), key=lambda item: item.stat().st_mtime
    )
    if not candidates:
        raise FileNotFoundError(
            "Kaggle download finished but no ZIP archive was found."
        )
    return candidates[-1]


def extract_archive(archive_path: Path, extract_dir: Path) -> None:
    extract_dir.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)


def _find_resume_source_file(extract_dir: Path) -> Path:
    csv_files = sorted(extract_dir.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError("No CSV files found in extracted Kaggle dataset.")

    for csv_file in csv_files:
        try:
            probe = pd.read_csv(csv_file, nrows=20)
        except Exception:
            continue
        text_column = _pick_first_existing(probe.columns, TEXT_COLUMN_CANDIDATES)
        if text_column:
            return csv_file

    raise ValueError(
        "Could not find a resume-like CSV file with a supported text column "
        f"{TEXT_COLUMN_CANDIDATES}."
    )


def map_resume_dataframe(input_df: pd.DataFrame) -> pd.DataFrame:
    """Map source dataframe into the pipeline-required resume schema."""
    name_column = _pick_first_existing(input_df.columns, NAME_COLUMN_CANDIDATES)
    category_column = _pick_first_existing(input_df.columns, CATEGORY_COLUMN_CANDIDATES)

    working = pd.DataFrame({
        "resume_text": input_df[text_column].fillna("").astype(str),
        "candidate_name": (
            input_df[name_column].fillna("").astype(str)
            if name_column
            else ""
        ),
        "source_category": (
            input_df[category_column].fillna("").astype(str)
            if category_column
            else "unknown"
        ),
    })

    working = working[working["resume_text"].str.strip().ne("")].copy().reset_index(drop=True)

    fallback_names = [f"Kaggle Candidate {idx}" for idx in range(1, len(working) + 1)]
    if name_column:
        working["candidate_name"] = working["candidate_name"].replace("", pd.NA).fillna(
            pd.Series(fallback_names)
        )
    else:
        working["candidate_name"] = fallback_names

    working.insert(0, "candidate_id", [f"KG_{idx:05d}" for idx in range(1, len(working) + 1)])
    return working[["candidate_id", "candidate_name", "resume_text", "source_category"]]
        mapped["candidate_name"]
        .replace("", pd.NA)
        .fillna(
            pd.Series([f"Kaggle Candidate {idx}" for idx in range(1, len(mapped) + 1)])
        )
    )

    mapped.insert(
        0, "candidate_id", [f"KG_{idx:05d}" for idx in range(1, len(mapped) + 1)]
    )

    if category_column:
        mapped["source_category"] = (
            input_df.loc[mapped.index, category_column].fillna("").astype(str)
        )
    else:
        mapped["source_category"] = "unknown"

    return mapped[["candidate_id", "candidate_name", "resume_text", "source_category"]]


def ingest_resume_dataset_from_kaggle(
    dataset_slug: str,
    download_dir: Path,
    extract_dir: Path,
    output_csv: Path,
    skip_download: bool = False,
) -> Path:
    """Download, extract, and map a Kaggle resume dataset into pipeline schema."""
    archive_path = download_dir / _slug_to_archive_name(dataset_slug)
    if not skip_download:
        archive_path = download_kaggle_dataset(
            dataset_slug=dataset_slug, download_dir=download_dir
        )

    if not archive_path.exists():
        raise FileNotFoundError(
            f"Expected dataset archive at {archive_path}. Download it first or disable skip_download."
        )

    extract_archive(archive_path=archive_path, extract_dir=extract_dir)
    source_csv = _find_resume_source_file(extract_dir)

    source_df = pd.read_csv(source_csv)
    mapped_df = map_resume_dataframe(source_df)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    mapped_df.to_csv(output_csv, index=False)
    return output_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest one Kaggle resume dataset and map it to candidate_id/candidate_name/resume_text format."
    )
    parser.add_argument(
        "--dataset",
        default=DEFAULT_RESUME_DATASET,
        help="Kaggle dataset slug, e.g. snehaanbhawal/resume-dataset",
    )
    parser.add_argument(
        "--download-dir",
        default="data/raw/kaggle",
        help="Directory where Kaggle ZIP archive will be stored.",
    )
    parser.add_argument(
        "--extract-dir",
        default="data/raw/kaggle/extracted/resume-dataset",
        help="Directory for extracted dataset files.",
    )
    parser.add_argument(
        "--output",
        default="data/raw/resumes_kaggle_mapped.csv",
        help="Mapped output CSV path for the resume pipeline.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip the Kaggle download command and use an existing local ZIP archive.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = ingest_resume_dataset_from_kaggle(
        dataset_slug=args.dataset,
        download_dir=Path(args.download_dir),
        extract_dir=Path(args.extract_dir),
        output_csv=Path(args.output),
        skip_download=args.skip_download,
    )
    print(f"Mapped resume dataset saved to: {output}")


if __name__ == "__main__":
    main()
