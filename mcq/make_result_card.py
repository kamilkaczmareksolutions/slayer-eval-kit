"""
mcq.make_result_card: generator karty wynikow z plikow JSON z `python -m mcq`.

Sedno: porownanie generative-letter vs likelihood (ten sam prompt, inny odczyt)
oraz taksonomia bledow. Tylko agregaty per kategoria; pojedyncze itemy pokazywane
wylacznie diagnostycznie (nie sa eksportem datasetu).

Uzycie:
    python -m mcq.make_result_card mcq/results/llama32_3b.json mcq/results/qwen25_3b.json \
        --out mcq/results/RESULT_CARD.md
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def short_model(name):
    return name.replace("ollama/", "")


def acc(items, mode):
    n = len(items)
    c = sum(1 for r in items if r.get(mode, {}).get("correct"))
    return c, n


def pct(c, n):
    return f"{100*c/n:.1f}%" if n else "brak"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mcq.make_result_card")
    ap.add_argument("results", nargs="+", help="Pliki JSON z wynikami")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    runs = [load(p) for p in args.results]
    cats = sorted({r["category"] for run in runs for r in run["per_item"]})

    L = []
    L.append("# MCQ: karta wyniku (generative-letter vs likelihood)")
    L.append("")
    L.append("Harness: `python -m mcq`. Sędzia: dopasowanie litery (otwarty, deterministyczny). "
             "Dekodowanie: temp 0, seed 0. Koszt: $0 (lokalnie, Ollama/CPU+iGPU).")
    L.append("")

    # ── 1. Setup ──────────────────────────────────────────────────────────────
    L.append("## Konfiguracja")
    L.append("")
    L.append("| pole | wartość |")
    L.append("|---|---|")
    r0 = runs[0]
    L.append(f"| itemów (held-out) | {r0['n_items']} |")
    L.append(f"| few-shot | {r0['n_shots']}-shot (pula rozłączna z testem, zdekontaminowana) |")
    L.append(f"| tasowanie opcji | {'tak' if r0['shuffle_options'] else 'nie'} (anty-bias pozycji, seed {r0['seed']}) |")
    L.append(f"| kategorie | {', '.join(cats)} |")
    L.append(f"| modele | {', '.join(short_model(r['model']) for r in runs)} |")
    L.append("")

    # ── 2. Agregaty model × tryb ──────────────────────────────────────────────
    L.append("## Wynik zbiorczy (accuracy)")
    L.append("")
    L.append("| model | generative | likelihood | Δ (lik−gen) |")
    L.append("|---|---|---|---|")
    for run in runs:
        items = run["per_item"]
        gc, n = acc(items, "generative")
        lc, _ = acc(items, "likelihood")
        d = lc - gc
        L.append(f"| {short_model(run['model'])} | {gc}/{n} ({pct(gc,n)}) | "
                 f"{lc}/{n} ({pct(lc,n)}) | {d:+d} |")
    L.append("")

    # ── 3. Per kategoria ──────────────────────────────────────────────────────
    L.append("## Per kategoria")
    L.append("")
    header = "| model | tryb | " + " | ".join(cats) + " |"
    L.append(header)
    L.append("|" + "---|" * (len(cats) + 2))
    for run in runs:
        items = run["per_item"]
        for mode in run["modes"]:
            cells = []
            for cat in cats:
                sub = [r for r in items if r["category"] == cat]
                c, n = acc(sub, mode)
                cells.append(f"{c}/{n}")
            L.append(f"| {short_model(run['model'])} | {mode} | " + " | ".join(cells) + " |")
    L.append("")

    # ── 4. Porownanie generative vs likelihood (sedno wkladu) ──────────────────
    L.append("## Generative vs likelihood: zgodność predykcji")
    L.append("")
    L.append("Ten sam prompt, różny odczyt. „Zgodność\" = oba tryby wskazały tę samą opcję. "
             "Tabela rozkłada przypadki, w których tryby się różnią. To sygnał z dyskusji "
             "(#benchmarki): wybór protokołu potrafi zmienić werdykt na itemie.")
    L.append("")
    L.append("| model | zgodność predykcji | oba dobrze | oba źle | tylko gen | tylko lik |")
    L.append("|---|---|---|---|---|---|")
    disagreements = []
    for run in runs:
        items = run["per_item"]
        if not ("generative" in run["modes"] and "likelihood" in run["modes"]):
            continue
        agree = both_ok = both_bad = gen_only = lik_only = 0
        for r in items:
            g, l = r["generative"], r["likelihood"]
            if g["pred_idx"] == l["pred_idx"]:
                agree += 1
            else:
                disagreements.append((short_model(run["model"]), r))
            if g["correct"] and l["correct"]:
                both_ok += 1
            elif not g["correct"] and not l["correct"]:
                both_bad += 1
            elif g["correct"]:
                gen_only += 1
            else:
                lik_only += 1
        n = len(items)
        L.append(f"| {short_model(run['model'])} | {agree}/{n} ({pct(agree,n)}) | "
                 f"{both_ok} | {both_bad} | {gen_only} | {lik_only} |")
    L.append("")
    if disagreements:
        L.append("### Itemy, na których tryby się rozjechały")
        L.append("")
        L.append("| model | id | kat. | pop. odp. | gen | lik |")
        L.append("|---|---|---|---|---|---|")
        for m, r in disagreements:
            g, l = r["generative"], r["likelihood"]
            gt = "✓" if g["correct"] else "✗"
            lt = "✓" if l["correct"] else "✗"
            L.append(f"| {m} | {r['id']} | {r['category']} | {r['answer_text']} | "
                     f"{g['pred_text']} {gt} | {l['pred_text']} {lt} |")
        L.append("")
    else:
        L.append("_Brak rozbieżności gen/lik w tej próbce: przy tych modelach oba protokoły "
                 "dały tę samą predykcję na każdym itemie (różnica może ujawnić się przy słabszych "
                 "modelach lub trudniejszym zbiorze)._")
        L.append("")

    # ── 4b. Margines pewnosci (sygnal, ktory generative wyrzuca) ───────────────
    def mean(xs):
        xs = [x for x in xs if x is not None]
        return sum(xs) / len(xs) if xs else None

    def fmt(x):
        return f"{x:.2f}" if x is not None else "brak"

    has_margin = any(
        r.get("likelihood", {}).get("margin") is not None
        for run in runs for r in run["per_item"]
    )
    if has_margin:
        L.append("## Margines pewności likelihood (czego generative nie widzi)")
        L.append("")
        L.append("Argmax obu trybów bywa zgodny, ale likelihood podaje dodatkowo **margines** = "
                 "logprob(1. litera) − logprob(2. litera). To sygnał kalibracji, który tryb "
                 "generative bezpowrotnie traci. Jeśli margines na itemach poprawnych jest większy "
                 "niż na błędnych, model „wie, czego nie wie\", i to widać tylko w likelihood.")
        L.append("")
        L.append("| model | margines (poprawne) | margines (błędne) | rozdzielczość |")
        L.append("|---|---|---|---|")
        for run in runs:
            if "likelihood" not in run["modes"]:
                continue
            ok = [r["likelihood"]["margin"] for r in run["per_item"] if r["likelihood"]["correct"]]
            bad = [r["likelihood"]["margin"] for r in run["per_item"] if not r["likelihood"]["correct"]]
            mok, mbad = mean(ok), mean(bad)
            sep = fmt(mok - mbad) if (mok is not None and mbad is not None) else "brak"
            L.append(f"| {short_model(run['model'])} | {fmt(mok)} | {fmt(mbad)} | {sep} |")
        L.append("")
        L.append("_Margines w nats (logprob naturalny). Większa „rozdzielczość\" = lepsza "
                 "kalibracja: błędy padają przy niższej pewności._")
        L.append("")

    # ── 5. Taksonomia bledow (itemy oblane przez wszystkie runy) ───────────────
    L.append("## Taksonomia błędów (itemy oblane przez wszystkie modele i tryby)")
    L.append("")
    by_id = defaultdict(list)
    meta = {}
    for run in runs:
        for r in run["per_item"]:
            modes_ok = all(r[m]["correct"] for m in run["modes"])
            by_id[r["id"]].append(modes_ok)
            meta[r["id"]] = r
    consensus_hard = [i for i, oks in by_id.items() if not any(oks)]
    cat_counts = defaultdict(int)
    for i in consensus_hard:
        cat_counts[meta[i]["category"]] += 1
    if consensus_hard:
        L.append(f"Itemów oblanych przez wszystkie modele/tryby: **{len(consensus_hard)}**. "
                 "Rozkład po kategoriach:")
        L.append("")
        for cat in sorted(cat_counts, key=lambda c: -cat_counts[c]):
            L.append(f"- `{cat}`: {cat_counts[cat]}")
        L.append("")
        L.append("| id | kat. | pytanie | poprawna |")
        L.append("|---|---|---|---|")
        for i in sorted(consensus_hard):
            r = meta[i]
            q = r["question"].replace("|", "\\|")
            L.append(f"| {i} | {r['category']} | {q} | {r['answer_text']} |")
        L.append("")
    else:
        L.append("_Brak itemów oblanych jednocześnie przez wszystkie modele i tryby._")
        L.append("")

    # ── 6. Bramki Slayera ─────────────────────────────────────────────────────
    L.append("## Zgodność z bramkami Slayera")
    L.append("")
    L.append("- **Held-out**: zbiór testowy rozłączny z pulą few-shot; rozłączność potwierdzona "
             "`decon` (dogfooding, patrz `dogfood_decon_report.md`).")
    L.append("- **Tylko agregaty**: raport podaje wyniki per kategoria; pojedyncze itemy widoczne "
             "wyłącznie diagnostycznie, nie jako eksport datasetu.")
    L.append("- **Otwarty sędzia**: parsowanie litery + odczyt logprob; deterministyczne, bez modelu-sędziego.")
    L.append("- **Koszt = część wyniku**: $0 (lokalnie). Dla modeli API koszt należy dopisać do karty.")
    L.append("- **Reprodukcja**: `python -m mcq --data … --fewshot … --model … --mode both --n-shots 5` "
             "(temp 0, seed 0). Uwaga: backend potrafi dać rzadki dryf ±1 itemu między uruchomieniami.")
    L.append("")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(L), encoding="utf-8")
    print(f"Karta wyniku: {args.out}")
    print(f"  modele: {', '.join(short_model(r['model']) for r in runs)}")
    print(f"  itemow oblanych przez wszystkich: {len(consensus_hard)}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
