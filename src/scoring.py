"""Scoring and ranking helpers for resume screening."""

from dataclasses import dataclass
from typing import Iterable, Set


@dataclass
class CandidateScore:
    """Container for candidate-level scoring details."""

    similarity_score: float
    required_skill_score: float
    important_skill_score: float
    final_fit_score: float
    matched_required: Set[str]
    missing_required: Set[str]
    matched_important: Set[str]


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def compute_candidate_score(
    similarity: float,
    resume_skills: Iterable[str],
    required_skills: Iterable[str],
    important_skills: Iterable[str],
    similarity_weight: float,
    required_weight: float,
    important_weight: float,
) -> CandidateScore:
    """Compute explainable component scores and final weighted score."""
    resume_skill_set = {item.lower() for item in resume_skills}
    required_set = {item.lower() for item in required_skills}
    important_set = {item.lower() for item in important_skills}

    matched_required = resume_skill_set.intersection(required_set)
    missing_required = required_set.difference(resume_skill_set)
    matched_important = resume_skill_set.intersection(important_set)

    similarity_score = similarity * 100.0
    required_skill_score = _safe_ratio(len(matched_required), len(required_set)) * 100.0
    important_skill_score = (
        _safe_ratio(len(matched_important), len(important_set)) * 100.0
    )

    final_fit_score = (
        (similarity_weight * similarity_score)
        + (required_weight * required_skill_score)
        + (important_weight * important_skill_score)
    )

    return CandidateScore(
        similarity_score=round(similarity_score, 2),
        required_skill_score=round(required_skill_score, 2),
        important_skill_score=round(important_skill_score, 2),
        final_fit_score=round(final_fit_score, 2),
        matched_required=matched_required,
        missing_required=missing_required,
        matched_important=matched_important,
    )
