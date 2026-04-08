#!/usr/bin/env bash
set -euo pipefail

# Required download format from task prompt:
# {#!/bin/bash
# kaggle datasets download snehaanbhawal/resume-dataset
# }

mkdir -p data/raw/kaggle

kaggle datasets download snehaanbhawal/resume-dataset -p data/raw/kaggle

python -m src.kaggle_ingestion \
  --dataset snehaanbhawal/resume-dataset \
  --download-dir data/raw/kaggle \
  --extract-dir data/raw/kaggle/extracted/resume-dataset \
  --output data/raw/resumes_kaggle_mapped.csv \
  --skip-download

echo "Mapped dataset ready at data/raw/resumes_kaggle_mapped.csv"
