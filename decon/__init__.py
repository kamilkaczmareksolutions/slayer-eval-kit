"""decon: dekontaminacja zbiorow treningowych wzgledem zbiorow testowych (PL)."""

from .core import (
    normalize,
    tokenize,
    word_ngrams,
    iter_records,
    TestIndex,
    scan_corpus,
)

__all__ = [
    "normalize",
    "tokenize",
    "word_ngrams",
    "iter_records",
    "TestIndex",
    "scan_corpus",
]

__version__ = "0.1.0"
