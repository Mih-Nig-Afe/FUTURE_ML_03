"""Text normalization and preprocessing helpers."""

import re
from typing import Iterable, List

from nltk.stem import SnowballStemmer
from nltk.tokenize import RegexpTokenizer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

TOKENIZER = RegexpTokenizer(r"[A-Za-z][A-Za-z0-9\+\#\-\.]*")
STEMMER = SnowballStemmer("english")
STOPWORDS = set(ENGLISH_STOP_WORDS)


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and strip outer spaces."""
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text: str) -> str:
    """Lowercase and remove non-ASCII symbols that are not useful for matching."""
    lowered = text.lower()
    normalized = re.sub(r"[^a-z0-9\s\+\#\-\.\/]", " ", lowered)
    return normalize_whitespace(normalized)


def tokenize(text: str) -> List[str]:
    """Tokenize text while preserving terms like c++ or scikit-learn."""
    return TOKENIZER.tokenize(text)


def remove_stopwords(tokens: Iterable[str]) -> List[str]:
    """Remove common stop words and very short tokens."""
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def stem_tokens(tokens: Iterable[str]) -> List[str]:
    """Apply stemming for robust lexical comparison."""
    return [STEMMER.stem(token) for token in tokens]


def preprocess_for_vectorizer(text: str, use_stemming: bool = False) -> str:
    """Convert raw text into normalized text suitable for TF-IDF vectorization."""
    cleaned = clean_text(text)
    tokens = tokenize(cleaned)
    filtered_tokens = remove_stopwords(tokens)
    if use_stemming:
        filtered_tokens = stem_tokens(filtered_tokens)
    return " ".join(filtered_tokens)
