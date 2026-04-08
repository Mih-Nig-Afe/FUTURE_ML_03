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
- Direct ingestion and mapping of Kaggle resume dataset
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
- select resume source (sample, mapped Kaggle data, or uploaded CSV),
- provide job description text,
- run scoring and ranking,
- inspect missing required skills per candidate,
- download ranking and summary outputs.

## Kaggle Ingestion (Direct)

This project directly ingests one required dataset:

- `snehaanbhawal/resume-dataset`

Mapped output used by pipeline:

- `data/raw/resumes_kaggle_mapped.csv`

Run ingestion:

```bash
bash scripts/ingest_kaggle_resume_dataset.sh
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
