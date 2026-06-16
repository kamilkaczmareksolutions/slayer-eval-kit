"""
decon.report: agregaty + raport markdown + manifest usuniec.

Zasada Slayera: raport pokazuje TYLKO agregaty (per zbior testowy) i krotka
probke do diagnozy. Pelne itemy testowe nie sa wysypywane. Manifest dotyczy
WIERSZY KORPUSU TRENINGOWEGO do usuniecia (to one sa skazone), nie testow.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .core import TestIndex, Match


def aggregate(matches: list[Match], index: TestIndex, n_corpus_docs: int) -> dict:
    by_set_docs: dict[str, set] = defaultdict(set)
    by_set_items: dict[str, set] = defaultdict(set)
    by_method: dict[str, int] = defaultdict(int)
    flagged_docs: set = set()

    for m in matches:
        by_set_docs[m.set_name].add(m.corpus_id)
        by_set_items[m.set_name].add(m.item_id)
        by_method[m.method] += 1
        flagged_docs.add(m.corpus_id)

    per_set = {}
    for set_name, total_items in index.per_set_counts.items():
        flagged = len(by_set_docs.get(set_name, ()))
        hit_items = len(by_set_items.get(set_name, ()))
        per_set[set_name] = {
            "test_items": total_items,
            "test_items_hit": hit_items,
            "test_items_hit_pct": round(100 * hit_items / total_items, 2) if total_items else 0.0,
            "corpus_docs_flagged": flagged,
        }

    return {
        "n_corpus_docs": n_corpus_docs,
        "n_flagged_docs": len(flagged_docs),
        "flagged_pct": round(100 * len(flagged_docs) / n_corpus_docs, 4) if n_corpus_docs else 0.0,
        "by_method": dict(by_method),
        "per_set": per_set,
        "flagged_docs": flagged_docs,
    }


def write_manifest(path: str | Path, matches: list[Match]) -> int:
    """JSONL: jeden wiersz na skazony dokument korpusu = lista przyczyn."""
    by_doc: dict[str, list[Match]] = defaultdict(list)
    for m in matches:
        by_doc[m.corpus_id].append(m)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for cid, ms in by_doc.items():
            reasons = sorted(
                ({"test_set": m.set_name, "test_item": m.item_id,
                  "method": m.method, "score": m.containment,
                  "shared_ngrams": m.shared_ngrams} for m in ms),
                key=lambda r: r["score"], reverse=True,
            )
            best = reasons[0]["score"] if reasons else 0.0
            f.write(json.dumps({
                "corpus_id": cid, "action": "remove",
                "best_score": best, "n_reasons": len(reasons),
                "reasons": reasons,
            }, ensure_ascii=False) + "\n")
    return len(by_doc)


def build_report_md(agg: dict, index: TestIndex, matches: list[Match],
                    config: dict, max_samples: int = 20) -> str:
    L = []
    L.append("# Raport dekontaminacji")
    L.append("")
    L.append(f"- Wygenerowano: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    L.append(f"- Korpus: `{config.get('corpus')}` ({agg['n_corpus_docs']} dokumentow)")
    L.append(f"- Zbiory testowe: `{config.get('tests')}` ({len(index.per_set_counts)} zbiorow, "
             f"{len(index.items)} itemow; krotkich <{index.min_ngram_tokens} tok.: {index.short_items})")
    L.append(f"- Metoda: word {config.get('n')}-gram, fold_diacritics={index.fold_diacritics}, "
             f"min_hits={config.get('min_hits')}, min_containment={config.get('min_containment')}")
    if config.get("minhash"):
        L.append(f"  + MinHash (prog={config.get('minhash_threshold')}, num_perm={config.get('num_perm')})")
    if config.get("embed"):
        L.append(f"  + Embedding (prog={config.get('embed_threshold')}, model={config.get('embed_model')})")
    L.append("")

    L.append("## Podsumowanie")
    L.append("")
    L.append(f"- **Skazone dokumenty korpusu: {agg['n_flagged_docs']} / {agg['n_corpus_docs']} "
             f"({agg['flagged_pct']}%)**")
    L.append(f"- Trafienia wg metody: {agg['by_method'] or 'brak'}")
    L.append("")

    L.append("## Kontaminacja per zbior testowy")
    L.append("")
    L.append("| Zbior testowy | Itemy | Itemy trafione | % itemow | Dok. korpusu skazone |")
    L.append("|---------------|------:|---------------:|---------:|---------------------:|")
    for set_name, s in sorted(agg["per_set"].items()):
        L.append(f"| {set_name} | {s['test_items']} | {s['test_items_hit']} | "
                 f"{s['test_items_hit_pct']} | {s['corpus_docs_flagged']} |")
    L.append("")

    if matches:
        L.append("## Probka dopasowan (diagnostycznie)")
        L.append("")
        L.append("| corpus_id | zbior | item | score | metoda | fragment itemu testowego |")
        L.append("|-----------|-------|------|------:|--------|--------------------------|")
        item_text = {(it.set_name, it.item_id): it.text for it in index.items}
        top = sorted(matches, key=lambda m: m.containment, reverse=True)[:max_samples]
        for m in top:
            snip = item_text.get((m.set_name, m.item_id), "")
            snip = " ".join(snip.split())[:60]
            if len(snip) == 60:
                snip += "..."
            L.append(f"| `{m.corpus_id}` | {m.set_name} | {m.item_id} | "
                     f"{m.containment} | {m.method} | {snip} |")
        L.append("")

    L.append("## Co dalej")
    L.append("")
    L.append("1. Usun z korpusu treningowego wiersze z `corpus_id` wymienione w manifeście.")
    L.append("2. Powtorz skan -> oczekiwany wynik: 0 skazonych dokumentow.")
    L.append("3. Twierdzenia benchmarkowe formuluj dopiero na wyczyszczonym korpusie (held-out = held-out).")
    L.append("")
    return "\n".join(L)
