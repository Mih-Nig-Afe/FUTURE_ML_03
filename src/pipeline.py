"""Main orchestration pipeline for resume screening and ranking."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import ROLE_PROFILES, SCORING_WEIGHTS
from src.scoring import compute_candidate_score
from src.skill_extraction import SkillExtractor
from src.text_preprocessing import preprocess_for_vectorizer

REQUIRED_COLUMNS = {"resume_text"}


class ResumeScreeningPipeline:
    """End-to-end resume screening pipeline."""

    def __init__(self) -> None:
        self.skill_extractor = SkillExtractor()

    @staticmethod
    def _prepare_resumes_dataframe(resumes: pd.DataFrame) -> pd.DataFrame:
        """Validate and normalize resume dataframe into expected schema."""
        missing_columns = REQUIRED_COLUMNS.difference(resumes.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Missing required resume columns: {missing}")

        normalized = resumes.copy()

        if "candidate_id" not in normalized.columns:
            normalized["candidate_id"] = [
                f"CAND_{idx:03d}" for idx in range(1, len(normalized) + 1)
            ]

        if "candidate_name" not in normalized.columns:
            normalized["candidate_name"] = [
                f"Candidate {idx}" for idx in range(1, len(normalized) + 1)
            ]

        normalized = normalized[
            ["candidate_id", "candidate_name", "resume_text"]
        ].copy()
        normalized["resume_text"] = normalized["resume_text"].fillna("").astype(str)
        normalized["candidate_name"] = (
            normalized["candidate_name"].fillna("").astype(str).str.strip()
        )
        blank_name_mask = normalized["candidate_name"].eq("")
        if blank_name_mask.any():
            for row_index in normalized.index[blank_name_mask]:
                normalized.at[row_index, "candidate_name"] = (
                    f"Candidate {row_index + 1}"
                )

        normalized = normalized.reset_index(drop=True)
        return normalized

    def _load_resumes(self, resumes_path: str) -> pd.DataFrame:
        path = Path(resumes_path)
        if path.suffix.lower() == ".csv":
            resumes = pd.read_csv(path)
        elif path.suffix.lower() == ".json":
            resumes = pd.read_json(path)
        else:
            raise ValueError("Resumes file must be CSV or JSON.")

        return self._prepare_resumes_dataframe(resumes)

    @staticmethod
    def _load_job_description(job_description_path: str) -> str:
        return Path(job_description_path).read_text(encoding="utf-8")

    def _build_role_skill_targets(
        self, role: str, job_description_text: str
    ) -> Tuple[list[str], list[str]]:
        role_key = role.lower().strip()
        profile = ROLE_PROFILES.get(role_key, {"required": [], "important": []})
        jd_skills = self.skill_extractor.extract(job_description_text)

        required = {skill.lower() for skill in profile.get("required", [])}
        important = {skill.lower() for skill in profile.get("important", [])}

        # Any skill explicitly present in the JD but not in required list is treated as important.
        important.update(jd_skills.difference(required))

        return sorted(required), sorted(important)

    def score_resumes(
        self,
        resumes_df: pd.DataFrame,
        job_description: str,
        role: str,
    ) -> Tuple[pd.DataFrame, Dict[str, object]]:
        """Compute ranking dataframe and explainable summary without writing files."""
        resumes = self._prepare_resumes_dataframe(resumes_df)
        required_skills, important_skills = self._build_role_skill_targets(
            role, job_description
        )

        resumes["preprocessed_text"] = resumes["resume_text"].map(
            preprocess_for_vectorizer
        )
        job_description_preprocessed = preprocess_for_vectorizer(job_description)

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        matrix = vectorizer.fit_transform(
            [*resumes["preprocessed_text"].tolist(), job_description_preprocessed]
        )

        resume_vectors = matrix[:-1]
        job_vector = matrix[-1]
        similarities = cosine_similarity(resume_vectors, job_vector).flatten()

        scored_rows = []
        for idx, row in resumes.iterrows():
            extracted_skills = self.skill_extractor.extract(row["resume_text"])
            score = compute_candidate_score(
                similarity=float(similarities[idx]),
                resume_skills=extracted_skills,
                required_skills=required_skills,
                important_skills=important_skills,
                similarity_weight=SCORING_WEIGHTS["similarity"],
                required_weight=SCORING_WEIGHTS["required"],
                important_weight=SCORING_WEIGHTS["important"],
            )

            scored_rows.append(
                {
                    "candidate_id": row["candidate_id"],
                    "candidate_name": row["candidate_name"],
                    "final_fit_score": score.final_fit_score,
                    "similarity_score": score.similarity_score,
                    "required_skill_score": score.required_skill_score,
                    "important_skill_score": score.important_skill_score,
                    "matched_required_skills": ", ".join(
                        sorted(score.matched_required)
                    ),
                    "matched_important_skills": ", ".join(
                        sorted(score.matched_important)
                    ),
                    "missing_required_skills": ", ".join(
                        sorted(score.missing_required)
                    ),
                }
            )

        ranking_df = pd.DataFrame(scored_rows).sort_values(
            by="final_fit_score", ascending=False
        )
        ranking_df.insert(0, "rank", range(1, len(ranking_df) + 1))

        summary = {
            "role": role,
            "total_candidates": int(len(ranking_df)),
            "required_skills": required_skills,
            "important_skills": important_skills,
            "top_candidate": (
                ranking_df.iloc[0]["candidate_name"] if not ranking_df.empty else None
            ),
            "weights": SCORING_WEIGHTS,
        }

        return ranking_df, summary

    def run(
        self,
        resumes_path: str,
        job_description_path: str,
        role: str,
        output_dir: str,
    ) -> Dict[str, str]:
        resumes = self._load_resumes(resumes_path)
        job_description = self._load_job_description(job_description_path)
        ranking_df, summary = self.score_resumes(
            resumes_df=resumes,
            job_description=job_description,
            role=role,
        )

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        ranking_file = output_path / "candidate_ranking.csv"
        summary_file = output_path / "screening_summary.json"

        ranking_df.to_csv(ranking_file, index=False)

        summary["artifacts"] = {
            "ranking": str(ranking_file),
            "summary": str(summary_file),
        }

        summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        return {
            "ranking": str(ranking_file),
            "summary": str(summary_file),
        }
