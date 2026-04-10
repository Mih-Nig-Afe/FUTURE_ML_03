#!/usr/bin/env bash
set -euo pipefail

# Required download format from task prompt:
# {#!/bin/bash
# kaggle datasets download snehaanbhawal/resume-dataset
# }
# {#!/bin/bash
# kaggle datasets download ravindrasinghrana/job-description-dataset
# }
# {#!/bin/bash
# kaggle datasets download PromptCloudHQ/us-jobs-on-monstercom
# }

mkdir -p data/raw/kaggle

if [[ -z "${KAGGLE_API_TOKEN:-}" ]] && [[ -z "${KAGGLE_USERNAME:-}" || -z "${KAGGLE_KEY:-}" ]]; then
  KAGGLE_CONFIG_FILE="${KAGGLE_CONFIG_DIR:-$HOME/.kaggle}/kaggle.json"
  if [[ ! -f "$KAGGLE_CONFIG_FILE" ]]; then
    echo "Kaggle credentials not found."
    echo "Set KAGGLE_API_TOKEN (preferred) or KAGGLE_USERNAME and KAGGLE_KEY, or mount/create $KAGGLE_CONFIG_FILE"
    exit 1
  fi

  HAS_USER_KEY=false
  HAS_TOKEN=false

  if grep -q '"username"' "$KAGGLE_CONFIG_FILE" && grep -q '"key"' "$KAGGLE_CONFIG_FILE"; then
    HAS_USER_KEY=true
  fi
  if grep -q '"api_token"' "$KAGGLE_CONFIG_FILE" || grep -q '"token"' "$KAGGLE_CONFIG_FILE"; then
    HAS_TOKEN=true
  fi

  if [[ "$HAS_USER_KEY" != true && "$HAS_TOKEN" != true ]]; then
    echo "Invalid Kaggle config file: $KAGGLE_CONFIG_FILE"
    echo "Expected JSON keys: api_token OR username and key"
    exit 1
  fi
fi

kaggle datasets download snehaanbhawal/resume-dataset -p data/raw/kaggle
kaggle datasets download ravindrasinghrana/job-description-dataset -p data/raw/kaggle
kaggle datasets download PromptCloudHQ/us-jobs-on-monstercom -p data/raw/kaggle

python -m src.kaggle_ingestion \
  --mode all \
  --download-dir data/raw/kaggle \
  --extract-dir data/raw/kaggle/extracted \
  --resumes-output data/raw/resumes_kaggle_mapped.csv \
  --jobs-output data/raw/job_descriptions_kaggle_mapped.csv \
  --generated-jd-output data/raw/job_description_generated_data_scientist.txt \
  --role data_scientist \
  --skip-download

echo "Mapped resume dataset ready at data/raw/resumes_kaggle_mapped.csv"
echo "Mapped job datasets ready at data/raw/job_descriptions_kaggle_mapped.csv"
echo "Generated role job description at data/raw/job_description_generated_data_scientist.txt"
