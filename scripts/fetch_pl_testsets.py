"""
fetch_pl_testsets.py: pobiera REALNE, publiczne dane PL do testu dekontaminacji.

Pobiera:
  - korpus: probka Polskiej Wikipedii (stand-in za korpus pretreningowy; Wikipedia
    jest skladnikiem wiekszosci korpusow PL, w tym SpeakLeash), strumieniowo.
  - zbiory testowe: Belebele (pol_Latn) + PolEmo2 (test), realne benchmarki PL.
  - kontrola pozytywna: K wycinkow artykulow z korpusu uzytych jako "benchmark
    wywodzacy sie z Wikipedii" (symuluje DYK/PolQA), do pomiaru recall detektora.

Wszystko laduje do data/downloaded/. Pisze DATA_CARD.md (lineage + licencje).

Uzycie:
    python scripts/fetch_pl_testsets.py --corpus-size 1500 --control 30
"""

import argparse
import json
from pathlib import Path


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(rows)


def fetch_wikipedia(n: int, max_chars: int):
    from datasets import load_dataset
    last_err = None
    for repo, cfg in (("wikimedia/wikipedia", "20231101.pl"),
                      ("graelo/wikipedia", "20230901.pl")):
        try:
            ds = load_dataset(repo, cfg, split="train", streaming=True)
            rows = []
            for i, ex in enumerate(ds):
                if len(rows) >= n:
                    break
                text = (ex.get("text") or "").strip()
                if len(text) < 200:
                    continue
                rows.append({"id": f"wiki_{ex.get('id', i)}", "text": text[:max_chars]})
            if rows:
                print(f"  Wikipedia: {len(rows)} artykulow z {repo}/{cfg}")
                return rows, f"{repo}/{cfg}"
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"  Wikipedia {repo}/{cfg} nieudane: {e}")
    raise RuntimeError(f"Nie udalo sie pobrac Wikipedii: {last_err}")


def fetch_belebele():
    from datasets import load_dataset
    ds = load_dataset("facebook/belebele", "pol_Latn", split="test")
    seen, rows = set(), []
    for ex in ds:
        p = (ex.get("flores_passage") or "").strip()
        if p and p not in seen:
            seen.add(p)
            rows.append({"id": f"belebele_{len(rows)}", "text": p})
    print(f"  Belebele pol_Latn: {len(rows)} unikalnych passusow")
    return rows


def fetch_polemo2():
    from datasets import load_dataset, get_dataset_config_names
    try:
        cfgs = get_dataset_config_names("clarin-pl/polemo2-official", trust_remote_code=True)
    except Exception:
        cfgs = [None]
    cfg = cfgs[0] if cfgs else None
    ds = load_dataset("clarin-pl/polemo2-official", cfg, split="test", trust_remote_code=True) if cfg \
        else load_dataset("clarin-pl/polemo2-official", split="test", trust_remote_code=True)
    rows = []
    for ex in ds:
        t = (ex.get("text") or ex.get("sentence") or "").strip()
        if t:
            rows.append({"id": f"polemo2_{len(rows)}", "text": t})
    print(f"  PolEmo2 test ({cfg}): {len(rows)} itemow")
    return rows


def make_control(corpus_rows, k: int, words: int = 40):
    """Pozytywna kontrola: wycinki artykulow korpusu jako 'benchmark z Wikipedii'."""
    rows = []
    for r in corpus_rows[:k]:
        toks = r["text"].split()
        if len(toks) < 20:
            continue
        snippet = " ".join(toks[3:3 + words])  # pomijamy tytulowe pierwsze slowa
        rows.append({"id": f"control_{r['id']}", "text": snippet, "source_corpus_id": r["id"]})
    print(f"  Kontrola pozytywna: {len(rows)} itemow (wycinki Wikipedii)")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="data/downloaded")
    ap.add_argument("--corpus-size", type=int, default=1500)
    ap.add_argument("--max-chars", type=int, default=4000)
    ap.add_argument("--control", type=int, default=30)
    args = ap.parse_args()

    out = Path(args.out_dir)
    tests_dir = out / "tests"
    sources = {}

    print("Pobieram korpus (Wikipedia PL, strumieniowo)...")
    corpus_rows, wiki_src = fetch_wikipedia(args.corpus_size, args.max_chars)
    n_corpus = write_jsonl(out / "corpus_wikipedia_pl.jsonl", corpus_rows)
    sources["corpus"] = {"file": "corpus_wikipedia_pl.jsonl", "n": n_corpus,
                         "source": wiki_src, "license": "CC BY-SA 4.0"}

    print("Pobieram zbiory testowe...")
    for name, fn, lic in (
        ("belebele_pol", fetch_belebele, "CC BY-SA 4.0 (Belebele/FLORES)"),
        ("polemo2_test", fetch_polemo2, "CC BY-NC-SA 4.0 (PolEmo2)"),
    ):
        try:
            rows = fn()
            n = write_jsonl(tests_dir / f"{name}.jsonl", rows)
            sources[name] = {"file": f"tests/{name}.jsonl", "n": n, "license": lic}
        except Exception as e:  # noqa: BLE001
            print(f"  [pominieto] {name}: {e}")
            sources[name] = {"error": str(e)}

    ctrl = make_control(corpus_rows, args.control)
    n_ctrl = write_jsonl(tests_dir / "_control_wiki.jsonl", ctrl)
    sources["_control_wiki"] = {"file": "tests/_control_wiki.jsonl", "n": n_ctrl,
                                "note": "pozytywna kontrola recall (wycinki korpusu)"}

    card = ["# DATA CARD: realne dane do dekontaminacji", "",
            "Pobrane przez `scripts/fetch_pl_testsets.py`. Wylacznie do EWALUACJI.", ""]
    card.append("| Rola | Plik | N | Zrodlo / licencja |")
    card.append("|------|------|--:|-------------------|")
    for k, v in sources.items():
        if "error" in v:
            card.append(f"| {k} | brak | brak | BLAD: {v['error']} |")
        else:
            lic = v.get("source", "") + (" / " if v.get("source") else "") + v.get("license", v.get("note", ""))
            card.append(f"| {k} | `{v['file']}` | {v['n']} | {lic} |")
    card += ["", "Uwaga: Wikipedia jest stand-inem za korpus pretreningowy (sklada sie na "
             "wiekszosc korpusow PL, w tym SpeakLeash). Benchmarki wywodzace sie z Wikipedii "
             "(np. DYK, PolQA) sa szczegolnie narazone na kontaminacje takim korpusem.", ""]
    # DATA_CARD piszemy do data/ (poza data/downloaded/, ktore jest gitignore/cursorignore)
    card_path = out.parent / "DATA_CARD.md"
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text("\n".join(card), encoding="utf-8")
    print(f"\nGotowe. DATA_CARD: {card_path}")


if __name__ == "__main__":
    main()
