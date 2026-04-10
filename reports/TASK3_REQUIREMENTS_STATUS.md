<!--
 * @Author: Mih-Nig-Afe 90252194+Mih-Nig-Afe@users.noreply.github.com
 * @Date: 2026-04-08 17:27:43
 * @LastEditors: Mih-Nig-Afe 90252194+Mih-Nig-Afe@users.noreply.github.com
 * @LastEditTime: 2026-04-08 19:10:33
 * @FilePath: /FUTURE_ML_01/FUTURE_ML_03/reports/TASK3_REQUIREMENTS_STATUS.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
# ML Task 3 Requirements Status

## Mandatory Features

- [x] Resume text cleaning and preprocessing
- [x] Skill extraction using NLP (spaCy PhraseMatcher + curated catalog)
- [x] Job description parsing
- [x] Resume-to-role similarity scoring (TF-IDF cosine similarity)
- [x] Candidate ranking based on role fit
- [x] Skill gap identification (missing required skills per candidate)
- [x] Explainable score breakdown for non-technical users
- [x] Recruiter-facing Streamlit scoring and ranking UI
- [x] Direct Kaggle ingestion and mapping to pipeline format
- [x] Integration of all required datasets:
  - [x] snehaanbhawal/resume-dataset
  - [x] ravindrasinghrana/job-description-dataset
  - [x] PromptCloudHQ/us-jobs-on-monstercom
- [x] Dockerized execution
- [x] Docker Compose profile for Task 3 Kaggle ingestion

## Explainability Provided

- Similarity score (text relevance)
- Required skill score (core must-have coverage)
- Important skill score (nice-to-have coverage)
- Final weighted fit score
- Missing required skills list

## Output Artifacts

- `data/processed/candidate_ranking.csv`
- `data/processed/screening_summary.json`
- `data/raw/resumes_kaggle_mapped.csv`
- `data/raw/job_descriptions_kaggle_mapped.csv`
- `data/raw/job_description_generated_data_scientist.txt`
