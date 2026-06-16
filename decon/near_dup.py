"""
decon.near_dup: opcjonalne detektory near-duplicate (MinHash, embeddingi).

Oba sa OPCJONALNE i wlaczane flagami CLI. Importy bibliotek sa lazy/guarded,
zeby rdzen n-gramowy dzialal na czystym stdlib.

  --minhash  -> datasketch (MinHashLSH); wykrywa near-dupy calych dokumentow
  --embed    -> sentence-transformers (CPU); wykrywa parafrazy/semantyczne dupy
"""

from __future__ import annotations

from pathlib import Path

from .core import TestIndex, Match, iter_records, tokenize


def _shingles(tokens: list[str], k: int) -> set[str]:
    if len(tokens) < k:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i:i + k]) for i in range(len(tokens) - k + 1)}


def scan_minhash(corpus_path: str | Path, index: TestIndex, corpus_field: str,
                 threshold: float = 0.8, num_perm: int = 128, shingle: int = 5):
    """Near-dup MinHash/Jaccard. Wymaga `pip install datasketch`."""
    try:
        from datasketch import MinHash, MinHashLSH
    except ImportError as e:
        raise RuntimeError(
            "Tryb --minhash wymaga pakietu datasketch: pip install datasketch"
        ) from e

    def make_mh(text: str):
        toks = tokenize(text, fold_diacritics=index.fold_diacritics)
        mh = MinHash(num_perm=num_perm)
        for sh in _shingles(toks, shingle):
            mh.update(sh.encode("utf-8"))
        return mh

    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    mh_by_item: dict[int, "MinHash"] = {}
    for i, item in enumerate(index.items):
        mh = make_mh(item.text)
        mh_by_item[i] = mh
        lsh.insert(str(i), mh)

    matches: list[Match] = []
    n_docs = 0
    for cid, ctext in iter_records(corpus_path, corpus_field):
        n_docs += 1
        mh = make_mh(ctext)
        for cand in lsh.query(mh):
            i = int(cand)
            jacc = mh.jaccard(mh_by_item[i])
            if jacc >= threshold:
                item = index.items[i]
                matches.append(Match(
                    corpus_id=cid, set_name=item.set_name, item_id=item.item_id,
                    shared_ngrams=0, containment=round(float(jacc), 4),
                    method="minhash",
                ))
    return matches, n_docs


def scan_embed(corpus_path: str | Path, index: TestIndex, corpus_field: str,
               threshold: float = 0.85, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
    """Near-dup embeddingowy (CPU). Wymaga `pip install sentence-transformers`.
    Uwaga: O(korpus x testy), tylko dla malych korpusow / probek."""
    try:
        from sentence_transformers import SentenceTransformer, util
    except ImportError as e:
        raise RuntimeError(
            "Tryb --embed wymaga sentence-transformers: pip install sentence-transformers"
        ) from e

    model = SentenceTransformer(model_name, device="cpu")
    item_texts = [it.text for it in index.items]
    item_emb = model.encode(item_texts, convert_to_tensor=True, normalize_embeddings=True,
                            show_progress_bar=False)

    corpus = list(iter_records(corpus_path, corpus_field))
    n_docs = len(corpus)
    if n_docs == 0:
        return [], 0
    doc_emb = model.encode([t for _, t in corpus], convert_to_tensor=True,
                           normalize_embeddings=True, show_progress_bar=False)
    sims = util.cos_sim(doc_emb, item_emb)  # [n_docs, n_items]

    matches: list[Match] = []
    for di in range(n_docs):
        row = sims[di]
        for ii in range(len(index.items)):
            score = float(row[ii])
            if score >= threshold:
                item = index.items[ii]
                matches.append(Match(
                    corpus_id=corpus[di][0], set_name=item.set_name, item_id=item.item_id,
                    shared_ngrams=0, containment=round(score, 4), method="embed",
                ))
    return matches, n_docs
