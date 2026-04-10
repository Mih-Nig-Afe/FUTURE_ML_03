# Resume Screening Architecture

## Data Ingestion Layer

Required Task 3 Kaggle datasets:

- `snehaanbhawal/resume-dataset` (resume text)
- `ravindrasinghrana/job-description-dataset` (job descriptions)
- `PromptCloudHQ/us-jobs-on-monstercom` (job descriptions)

Ingestion module responsibilities:

- Download archives with Kaggle CLI
- Extract archives and detect source CSV files
- Map resume records to `candidate_id/candidate_name/resume_text`
- Map job records to normalized job-description schema
- Build generated role-focused job description text
- Save standardized artifacts for pipeline + UI

## Pipeline Stages

1. Input loading

- Resume records (CSV/JSON)
- Job description text (sample file, uploaded text, or generated from mapped Kaggle jobs)

1. Text preprocessing

- Lowercasing and cleanup
- Tokenization and stopword filtering
- TF-IDF-ready text

1. Skill extraction

- spaCy PhraseMatcher over curated skill catalog
- Alias normalization (e.g., NLP -> natural language processing)

1. Scoring

- Text similarity score via cosine similarity
- Required skill coverage score
- Important skill coverage score
- Final weighted fit score

1. Ranking and explainability

- Candidates ranked by final fit score
- Missing required skills highlighted
- Summary JSON for reporting/demo

## Scoring Formula

Final Fit Score =

- 0.50 x Similarity Score
- 0.35 x Required Skill Score
- 0.15 x Important Skill Score

## Deployment Paths

- Local CLI (`python -m src.run_pipeline`)
- Docker service (`resume-screening`)
- Streamlit Docker service (`recruiter-ui`)
- Task 3 Kaggle ingestion Docker profile (`task3-kaggle-ingestion`)
