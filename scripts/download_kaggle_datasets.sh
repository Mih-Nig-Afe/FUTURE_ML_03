#!/usr/bin/env bash
set -euo pipefail

# Optional helper script for downloading Task 3 datasets from Kaggle.
# Requires: kaggle CLI configured with ~/.kaggle/kaggle.json

mkdir -p data/raw/kaggle

kaggle datasets download snehaanbhawal/resume-dataset -p data/raw/kaggle
kaggle datasets download ravindrasinghrana/job-description-dataset -p data/raw/kaggle
kaggle datasets download PromptCloudHQ/us-jobs-on-monstercom -p data/raw/kaggle

echo "Downloaded archives to data/raw/kaggle"
