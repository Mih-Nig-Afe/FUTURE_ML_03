# FUTURE_ML_03 - Resume / Candidate Screening System

Machine Learning Task 3 (2026) by Future Interns.

This project builds an end-to-end NLP resume screening system that:

- parses resume text,
- extracts skills,
- compares resumes against a job description,
- scores and ranks candidates,
- highlights missing required skills.

## Why This Project Matters

Hiring teams review hundreds of resumes per role. This solution speeds up shortlisting with consistent, explainable scoring so recruiters can focus on high-fit candidates.

## Features Implemented

- Resume text cleaning and preprocessing
- Skill extraction using spaCy NLP pipeline
- Job description parsing
- TF-IDF + cosine similarity scoring
- Weighted role-fit scoring
- Candidate ranking
- Skill-gap identification
- Recruiter-facing Streamlit web UI
- Direct ingestion and mapping of all required Task 3 Kaggle datasets
- Dockerized execution

## Project Structure

```text
FUTURE_ML_03/
  data/
    raw/
      resumes_sample.csv
      job_description_data_scientist.txt
    processed/
  docs/
    ARCHITECTURE.md
  notebooks/
    resume_screening_demo.ipynb
  reports/
    TASK3_REQUIREMENTS_STATUS.md
  scripts/
    download_kaggle_datasets.sh
    ingest_kaggle_resume_dataset.sh
    run_real_kaggle_docker_stack.sh
    run_local.sh
    run_streamlit.sh
  src/
    config.py
    kaggle_ingestion.py
    text_preprocessing.py
    skill_extraction.py
    scoring.py
    pipeline.py
    run_pipeline.py
  streamlit_app.py
  Dockerfile
  docker-compose.yml
  requirements.txt
```

## Scoring Logic (Explainable)

Each candidate receives:

- Similarity Score: semantic relevance of resume text to the job description.
- Required Skill Score: coverage of must-have skills.
- Important Skill Score: coverage of bonus/nice-to-have skills.

Final weighted score:

- 50% Similarity Score
- 35% Required Skill Score
- 15% Important Skill Score

This design keeps rankings transparent and recruiter-friendly.

## Local Run

1. Create environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

1. Run the pipeline:

```bash
python -m src.run_pipeline \
  --resumes data/raw/resumes_sample.csv \
  --job data/raw/job_description_data_scientist.txt \
  --role data_scientist \
  --output data/processed
```

1. View outputs:

- `data/processed/candidate_ranking.csv`
- `data/processed/screening_summary.json`

## Docker Run

### Option A: Docker

```bash
docker build -t future-ml-task3 .
docker run --rm -v "$(pwd)/data:/app/data" future-ml-task3
```

### Option B: Docker Compose

```bash
docker compose up --build
```

The default `resume-screening` service now runs with mapped Kaggle artifacts (not sample files).

### Task 3 Kaggle Ingestion in Docker (All Required Datasets)

This runs the required dataset downloads and mapping inside Docker.

```bash
docker compose --profile kaggle run --rm task3-kaggle-ingestion
```

Notes:

- Mounts host Kaggle credentials from `${HOME}/.kaggle` into container.
- Or provide `KAGGLE_API_TOKEN` environment variable (preferred).
- Legacy fallback: `KAGGLE_USERNAME` and `KAGGLE_KEY`.
- Produces mapped artifacts under `data/raw/`.

Quick credential setup:

```bash
cp .env.example .env
```

Then fill in your Kaggle username/key in `.env`.
If you are using the API token flow, set `KAGGLE_API_TOKEN` in `.env`.

### Streamlit UI with Docker Compose

```bash
docker compose up --build recruiter-ui
```

Then open: <http://localhost:8501>

## Streamlit Recruiter UI (Local)

```bash
bash scripts/run_streamlit.sh
```

The UI lets recruiters:

- choose role profile,
- select resume source (mapped Task 3 Kaggle data or uploaded CSV),
- choose job description source (generated from mapped Kaggle jobs or manual/uploaded),
- provide job description text,
- run scoring and ranking,
- inspect missing required skills per candidate,
- download ranking and summary outputs.

## Kaggle Ingestion (Direct, All Required Datasets)

This project directly ingests all required Task 3 datasets:

- `snehaanbhawal/resume-dataset`
- `ravindrasinghrana/job-description-dataset`
- `PromptCloudHQ/us-jobs-on-monstercom`

Mapped outputs used by the screening system:

- `data/raw/resumes_kaggle_mapped.csv`
- `data/raw/job_descriptions_kaggle_mapped.csv`
- `data/raw/job_description_generated_data_scientist.txt`

Run one-command Task 3 ingestion:

```bash
bash scripts/ingest_kaggle_resume_dataset.sh
```

Or run module directly:

```bash
python -m src.kaggle_ingestion \
  --mode all \
  --download-dir data/raw/kaggle \
  --extract-dir data/raw/kaggle/extracted \
  --resumes-output data/raw/resumes_kaggle_mapped.csv \
  --jobs-output data/raw/job_descriptions_kaggle_mapped.csv \
  --generated-jd-output data/raw/job_description_generated_data_scientist.txt \
  --role data_scientist
```

## Kaggle Dataset Commands (Optional)

Use the helper script:

```bash
bash scripts/download_kaggle_datasets.sh
```

Datasets referenced:

- Required command format from task prompt:

```bash
{#!/bin/bash
kaggle datasets download snehaanbhawal/resume-dataset}
```

```bash
{#!/bin/bash
kaggle datasets download ravindrasinghrana/job-description-dataset}
```

```bash
{#!/bin/bash
kaggle datasets download PromptCloudHQ/us-jobs-on-monstercom}
```

- <https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset>
- <https://www.kaggle.com/datasets/ravindrasinghrana/job-description-dataset>
- <https://www.kaggle.com/datasets/PromptCloudHQ/us-jobs-on-monstercom>

## End-to-End Docker Workflow

1. Ingest and map required Kaggle datasets:

```bash
docker compose --profile kaggle run --rm task3-kaggle-ingestion
```

1. Run scoring pipeline:

```bash
docker compose up --build resume-screening
```

Or run locally on mapped Kaggle artifacts:

```bash
bash scripts/run_task3_kaggle_pipeline.sh
```

1. Launch recruiter UI:

```bash
docker compose up --build recruiter-ui
```

One-command run (real Kaggle data + pipeline + UI):

```bash
bash scripts/run_real_kaggle_docker_stack.sh
```

## Business-Facing Interpretation

The top-ranked candidates are those with:

- high text relevance to the role,
- strong coverage of required skills,
- fewer or no critical skill gaps.

Recruiters can use the `missing_required_skills` field to decide:

- immediate shortlist,
- interview with upskilling concern,
- reject for role mismatch.

## Notes

- This repo includes sample data for reproducible demo runs.
- You can replace inputs with real or anonymized resumes and job descriptions.
- The pipeline supports both CSV and JSON resume files (must include `resume_text`).
