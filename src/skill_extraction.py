"""Skill extraction powered by spaCy PhraseMatcher."""

from typing import Iterable, Set

import spacy
from spacy.matcher import PhraseMatcher

from src.config import SKILL_ALIASES, SKILL_CATALOG


class SkillExtractor:
    """Extract normalized skills from text using a curated skill catalog."""

    def __init__(self, skill_catalog: Iterable[str] | None = None) -> None:
        self.nlp = spacy.blank("en")
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

        catalog = list(skill_catalog) if skill_catalog is not None else SKILL_CATALOG
        patterns = [self.nlp.make_doc(skill) for skill in catalog]
        self.matcher.add("SKILL", patterns)

    def _canonicalize(self, skill: str) -> str:
        normalized = skill.strip().lower()
        return SKILL_ALIASES.get(normalized, normalized)

    def extract(self, text: str) -> Set[str]:
        doc = self.nlp(text)
        matches = self.matcher(doc)
        extracted = {
            self._canonicalize(doc[start:end].text) for _, start, end in matches
        }
        return extracted
