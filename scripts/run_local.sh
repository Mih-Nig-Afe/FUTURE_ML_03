#!/usr/bin/env bash
set -euo pipefail

python -m src.run_pipeline \
  --resumes data/raw/resumes_sample.csv \
  --job data/raw/job_description_data_scientist.txt \
  --role data_scientist \
  --output data/processed
