#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]] && [[ -z "${KAGGLE_API_TOKEN:-}" ]] && [[ -z "${KAGGLE_USERNAME:-}" || -z "${KAGGLE_KEY:-}" ]]; then
  echo "Missing Kaggle credentials."
  echo "Create .env from .env.example, or export KAGGLE_API_TOKEN (preferred), or KAGGLE_USERNAME and KAGGLE_KEY."
  exit 1
fi

echo "Step 1/3: Download and map required Kaggle datasets"
docker compose --profile kaggle run --rm --build task3-kaggle-ingestion

echo "Step 2/3: Run pipeline with mapped Kaggle artifacts"
docker compose run --rm --build resume-screening

echo "Step 3/3: Start recruiter UI at http://localhost:8501"
docker compose up --build recruiter-ui
