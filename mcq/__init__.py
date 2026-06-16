"""mcq: maly harness MCQ (PL) z dwoma trybami scoringu: generative-letter i likelihood."""

from .harness import (
    load_mcq,
    build_messages,
    score_generative,
    score_likelihood,
    LETTERS,
)

__all__ = ["load_mcq", "build_messages", "score_generative", "score_likelihood", "LETTERS"]
__version__ = "0.1.0"
