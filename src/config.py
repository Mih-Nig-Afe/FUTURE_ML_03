"""Project configuration for the resume screening system."""

from typing import Dict, List

SKILL_CATALOG: List[str] = [
    "python",
    "sql",
    "excel",
    "tableau",
    "power bi",
    "statistics",
    "machine learning",
    "deep learning",
    "nlp",
    "natural language processing",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "xgboost",
    "data visualization",
    "data cleaning",
    "feature engineering",
    "a/b testing",
    "time series",
    "forecasting",
    "data mining",
    "etl",
    "spark",
    "hadoop",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "git",
    "communication",
    "problem solving",
    "leadership",
    "project management",
]

SKILL_ALIASES: Dict[str, str] = {
    "nlp": "natural language processing",
    "ml": "machine learning",
    "powerbi": "power bi",
    "sklearn": "scikit-learn",
    "pytorch": "pytorch",
}

ROLE_PROFILES: Dict[str, Dict[str, List[str]]] = {
    "data_scientist": {
        "required": [
            "python",
            "sql",
            "statistics",
            "machine learning",
            "pandas",
            "scikit-learn",
            "data visualization",
        ],
        "important": [
            "deep learning",
            "natural language processing",
            "feature engineering",
            "aws",
            "docker",
            "communication",
        ],
    },
    "ml_engineer": {
        "required": [
            "python",
            "machine learning",
            "scikit-learn",
            "docker",
            "git",
        ],
        "important": [
            "pytorch",
            "tensorflow",
            "kubernetes",
            "aws",
            "feature engineering",
        ],
    },
    "data_analyst": {
        "required": [
            "sql",
            "excel",
            "tableau",
            "statistics",
            "data visualization",
            "data cleaning",
        ],
        "important": [
            "python",
            "power bi",
            "communication",
            "a/b testing",
        ],
    },
}

SCORING_WEIGHTS: Dict[str, float] = {
    "similarity": 0.50,
    "required": 0.35,
    "important": 0.15,
}
