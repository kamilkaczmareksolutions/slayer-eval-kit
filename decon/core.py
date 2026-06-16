"""
decon.core: detekcja kontaminacji n-gramowej (+ opcjonalnie MinHash).

Strategia pamieciowa: zbiory testowe sa male -> indeks n-gramow testow trzymamy
w RAM. Korpus treningowy bywa ogromny -> czytamy go strumieniowo, rekord po
rekordzie, i nie materializujemy w pamieci.

Detekcja n-gramowa zglasza dokument korpusu jako skazony, jezeli zawiera
przynajmniej `min_hits` wspolnych n-gramow (slownych) z jakims itemem testowym.
Score = containment = ile n-gramow itemu testowego znaleziono w dokumencie /
liczba n-gramow itemu (1.0 = caly item testowy obecny w dokumencie treningowym).
"""

from __future__ import annotations

import json
import re
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Iterable


# ─── Normalizacja swiadoma jezyka polskiego ──────────────────────────────────

_PL_FOLD = str.maketrans({
    "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n",
    "ó": "o", "ś": "s", "ź": "z", "ż": "z",
})

_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WS_RE = re.compile(r"\s+", re.UNICODE)


def normalize(text: str, fold_diacritics: bool = False, keep_punct: bool = False) -> str:
    """Lowercase + redukcja bialych znakow; domyslnie usuwa interpunkcje.

    fold_diacritics=True dodatkowo sprowadza polskie znaki do ASCII (lapie
    duplikaty rozniace sie tylko diakrytykami)."""
    t = text.lower()
    if not keep_punct:
        t = _PUNCT_RE.sub(" ", t)
    if fold_diacritics:
        t = t.translate(_PL_FOLD)
    t = _WS_RE.sub(" ", t).strip()
    return t


def tokenize(text: str, fold_diacritics: bool = False) -> list[str]:
    n = normalize(text, fold_diacritics=fold_diacritics)
    return n.split(" ") if n else []


def word_ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    """N-gramy slowne. Dla tekstow krotszych niz n zwraca jeden n-gram = caly tekst."""
    if not tokens:
        return []
    if len(tokens) < n:
        return [tuple(tokens)]
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def _hash_gram(gram: tuple[str, ...]) -> int:
    h = hashlib.blake2b(" ".join(gram).encode("utf-8"), digest_size=8)
    return int.from_bytes(h.digest(), "big")


# ─── Wejscie: jsonl / txt / katalog ──────────────────────────────────────────

def _iter_file(path: Path, field: str) -> Iterator[tuple[str, str]]:
    suf = path.suffix.lower()
    if suf == ".jsonl":
        with path.open(encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text = obj.get(field)
                if text is None:
                    text = " ".join(str(v) for v in obj.values() if isinstance(v, str))
                rid = str(obj.get("id", f"{path.name}:{i}"))
                if text:
                    yield rid, str(text)
    elif suf in (".txt", ".md"):
        with path.open(encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if line:
                    yield f"{path.name}:{i}", line
    else:
        return


def iter_records(path: str | Path, field: str = "text") -> Iterator[tuple[str, str]]:
    """Strumien (id, text). Sciezka = plik (.jsonl/.txt/.md) lub katalog."""
    p = Path(path)
    if p.is_dir():
        for fp in sorted(p.iterdir()):
            if fp.suffix.lower() in (".jsonl", ".txt", ".md"):
                yield from _iter_file(fp, field)
    else:
        yield from _iter_file(p, field)


def list_test_sets(path: str | Path) -> list[Path]:
    """Zwraca liste plikow zbiorow testowych (kazdy plik = osobny zbior)."""
    p = Path(path)
    if p.is_dir():
        return [fp for fp in sorted(p.iterdir())
                if fp.suffix.lower() in (".jsonl", ".txt", ".md")]
    return [p]


# ─── Indeks n-gramow testow ──────────────────────────────────────────────────

@dataclass
class TestItem:
    set_name: str
    item_id: str
    n_tokens: int
    n_grams: int
    text: str


@dataclass
class TestIndex:
    n: int
    fold_diacritics: bool = False
    min_ngram_tokens: int = 5
    # hash n-gramu -> lista indeksow itemow (do listy self.items)
    gram_to_items: dict[int, list[int]] = field(default_factory=dict)
    items: list[TestItem] = field(default_factory=list)
    per_set_counts: dict[str, int] = field(default_factory=dict)
    short_items: int = 0

    def add_record(self, set_name: str, item_id: str, text: str) -> None:
        toks = tokenize(text, fold_diacritics=self.fold_diacritics)
        grams = word_ngrams(toks, self.n)
        idx = len(self.items)
        self.items.append(TestItem(
            set_name=set_name, item_id=item_id,
            n_tokens=len(toks), n_grams=len(grams),
            text=text,
        ))
        self.per_set_counts[set_name] = self.per_set_counts.get(set_name, 0) + 1
        if len(toks) < self.min_ngram_tokens:
            self.short_items += 1
        for g in grams:
            h = _hash_gram(g)
            self.gram_to_items.setdefault(h, []).append(idx)

    @classmethod
    def build(cls, test_paths: Iterable[Path], field_name: str, n: int,
              fold_diacritics: bool, min_ngram_tokens: int) -> "TestIndex":
        ti = cls(n=n, fold_diacritics=fold_diacritics, min_ngram_tokens=min_ngram_tokens)
        for tp in test_paths:
            set_name = tp.stem
            for rid, text in _iter_file(tp, field_name):
                ti.add_record(set_name, rid, text)
        return ti


# ─── Skan korpusu (strumieniowy) ─────────────────────────────────────────────

@dataclass
class Match:
    corpus_id: str
    set_name: str
    item_id: str
    shared_ngrams: int
    containment: float  # shared / liczba n-gramow itemu testowego
    method: str = "ngram"


def scan_corpus(corpus_path: str | Path, index: TestIndex, corpus_field: str = "text",
                min_hits: int = 1, min_containment: float = 0.0,
                progress_every: int = 0) -> tuple[list[Match], int]:
    """Strumieniowy skan. Zwraca (lista dopasowan, liczba_dokumentow_korpusu).

    Dla kazdego dokumentu korpusu liczymy, ile jego n-gramow trafia w n-gramy
    poszczegolnych itemow testowych; raportujemy najlepsze dopasowanie na item."""
    matches: list[Match] = []
    n_docs = 0
    for cid, ctext in iter_records(corpus_path, corpus_field):
        n_docs += 1
        if progress_every and n_docs % progress_every == 0:
            print(f"  ...przeskanowano {n_docs} dokumentow korpusu", flush=True)
        toks = tokenize(ctext, fold_diacritics=index.fold_diacritics)
        if not toks:
            continue
        grams = word_ngrams(toks, index.n)
        # dedup n-gramow dokumentu, by liczyc pokrycie itemu, nie powtorzenia
        seen_for_item: dict[int, set[int]] = {}
        for g in set(grams):
            h = _hash_gram(g)
            hit = index.gram_to_items.get(h)
            if not hit:
                continue
            for item_idx in hit:
                seen_for_item.setdefault(item_idx, set()).add(h)
        for item_idx, hset in seen_for_item.items():
            item = index.items[item_idx]
            shared = len(hset)
            denom = max(1, item.n_grams)
            containment = shared / denom
            if shared >= min_hits and containment >= min_containment:
                matches.append(Match(
                    corpus_id=cid, set_name=item.set_name, item_id=item.item_id,
                    shared_ngrams=shared, containment=round(containment, 4),
                ))
    return matches, n_docs
