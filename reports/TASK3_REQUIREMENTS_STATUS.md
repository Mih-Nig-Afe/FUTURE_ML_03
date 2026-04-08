# ML Task 3 Requirements Status

## Mandatory Features

- [x] Resume text cleaning and preprocessing
- [x] Skill extraction using NLP (spaCy PhraseMatcher + curated catalog)
- [x] Job description parsing
- [x] Resume-to-role similarity scoring (TF-IDF cosine similarity)
- [x] Candidate ranking based on role fit
- [x] Skill gap identification (missing required skills per candidate)
- [x] Explainable score breakdown for non-technical users
- [x] Dockerized execution

## Explainability Provided

- Similarity score (text relevance)
- Required skill score (core must-have coverage)
- Important skill score (nice-to-have coverage)
- Final weighted fit score
- Missing required skills list

## Output Artifacts

- `data/processed/candidate_ranking.csv`
- `data/processed/screening_summary.json`
