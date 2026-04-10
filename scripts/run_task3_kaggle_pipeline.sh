#!/usr/bin/env bash
set -euo pipefail

RESUMES_PATH="data/raw/resumes_kaggle_mapped.csv"
JOBS_MAPPED_PATH="data/raw/job_descriptions_kaggle_mapped.csv"
RUNTIME_RESUMES_PATH="/tmp/task3_resumes_kaggle_mapped.csv"
RUNTIME_JOBS_PATH="/tmp/task3_job_descriptions_kaggle_mapped.csv"
RUNTIME_JOB_PATH="/tmp/task3_job_description_generated_data_scientist.txt"

if [[ ! -f "$RESUMES_PATH" ]]; then
  echo "Missing $RESUMES_PATH. Run scripts/ingest_kaggle_resume_dataset.sh first."
  exit 1
fi

if [[ ! -f "$JOBS_MAPPED_PATH" ]]; then
  echo "Missing $JOBS_MAPPED_PATH. Run scripts/ingest_kaggle_resume_dataset.sh first."
  exit 1
fi

cp "$RESUMES_PATH" "$RUNTIME_RESUMES_PATH"
cp "$JOBS_MAPPED_PATH" "$RUNTIME_JOBS_PATH"

python - <<'PY'
from pathlib import Path

import pandas as pd

from src.kaggle_ingestion import build_role_job_description_text

jobs_df = pd.read_csv("/tmp/task3_job_descriptions_kaggle_mapped.csv")
job_description = build_role_job_description_text(
    mapped_jobs_df=jobs_df,
    role_key="data_scientist",
)

if not job_description.strip():
    raise RuntimeError(
        "Generated job description is empty. Verify mapped jobs CSV content."
    )

Path("/tmp/task3_job_description_generated_data_scientist.txt").write_text(
    job_description,
    encoding="utf-8",
)
PY

python -m src.run_pipeline \
  --resumes "$RUNTIME_RESUMES_PATH" \
  --job "$RUNTIME_JOB_PATH" \
  --role data_scientist \
  --output data/processed
