# Resume Screening Architecture

## Pipeline Stages

1. Input loading

- Resume records (CSV/JSON)
- Job description text

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
