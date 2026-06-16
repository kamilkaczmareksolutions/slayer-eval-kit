"""
make_result_card.py: buduje markdownowy result card z wyników evaluator_lizzy.py.

Dorzut do benchmarku lizzy-606 (nie zmienia jej evaluatora). Czyta jeden lub
wiele plikow wynikowych JSON i sklada agregaty per kategoria + probke bledow.

Uzycie:
    python make_result_card.py --tests polish_morph_tests_ext.json \
        --results results_ollama_llama3.2_3b.json [results_gpt-4o-mini.json ...] \
        --out results/CARD.md
"""

import json
import argparse
import collections
from datetime import datetime, timezone


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def per_category(results):
    cats = collections.OrderedDict()
    for r in results:
        c = r["category"]
        s = cats.setdefault(c, {"passed": 0, "total": 0, "distractor": 0})
        s["total"] += 1
        if r["passed"]:
            s["passed"] += 1
        if r.get("hit_distractor") and not r["passed"]:
            s["distractor"] += 1
    return cats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", required=True)
    ap.add_argument("--results", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--errors-per-cat", type=int, default=3,
                    help="Ile przykladowych bledow na kategorie w taksonomii")
    args = ap.parse_args()

    tests = load(args.tests)
    test_by_id = {t["id"]: t for t in tests["tests"]}
    n_total = len(tests["tests"])
    cat_meta = {c["id"]: c["name"] for c in tests.get("categories", [])}

    runs = [load(p) for p in args.results]

    lines = []
    lines.append("# Result card: Polish Morphology Benchmark (rozszerzenie ext1)")
    lines.append("")
    lines.append(f"- Zbior testowy: `{args.tests}` ({tests.get('version','?')}, {n_total} przypadkow, held-out)")
    lines.append(f"- Bazuje na: {tests.get('extends','polish_morph_tests.json (lizzy-606)')}")
    lines.append(f"- Wygenerowano: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("- Protokol: temperatura 0 (deterministycznie), matcher substring jak w evaluator.py, tylko agregaty")
    lines.append("")

    # Tabela ogolna
    lines.append("## Wynik ogolny")
    lines.append("")
    lines.append("| Model | Pass | % | Bledy z dystraktorem |")
    lines.append("|-------|-----:|--:|---------------------:|")
    for run in runs:
        res = run["results"]
        p = sum(1 for r in res if r["passed"])
        t = len(res)
        d = sum(1 for r in res if r.get("hit_distractor") and not r["passed"])
        pct = f"{100*p/t:.1f}" if t else "0.0"
        lines.append(f"| `{run['model']}` | {p}/{t} | {pct} | {d} |")
    lines.append("")

    # Per kategoria (per model)
    lines.append("## Per kategoria")
    lines.append("")
    for run in runs:
        lines.append(f"### `{run['model']}`")
        lines.append("")
        lines.append("| Kategoria | Pass | % | Dystraktor |")
        lines.append("|-----------|-----:|--:|-----------:|")
        cats = per_category(run["results"])
        for c, s in cats.items():
            name = cat_meta.get(c, c)
            pct = f"{100*s['passed']/s['total']:.0f}" if s["total"] else "0"
            lines.append(f"| {c} ({name}) | {s['passed']}/{s['total']} | {pct} | {s['distractor']} |")
        lines.append("")

    # Taksonomia bledow (probka)
    lines.append("## Taksonomia bledow (probka)")
    lines.append("")
    lines.append("Agregaty + reprezentatywne pomylki (item -> co model wyprodukowal). "
                 "Itemy sluza wylacznie diagnozie, nie wchodza do treningu.")
    lines.append("")
    for run in runs:
        fails = [r for r in run["results"] if not r["passed"]]
        if not fails:
            continue
        lines.append(f"### `{run['model']}`: {len(fails)} bledow")
        lines.append("")
        by_cat = collections.defaultdict(list)
        for r in fails:
            by_cat[r["category"]].append(r)
        for c, items in by_cat.items():
            lines.append(f"- **{c}** ({len(items)}):")
            for r in items[: args.errors_per_cat]:
                t = test_by_id.get(r["id"], {})
                exp = t.get("expected", "?")
                got = (r.get("response", "") or "").strip().replace("\n", " ")
                if len(got) > 80:
                    got = got[:77] + "..."
                flag = " [dystraktor]" if r.get("hit_distractor") else ""
                lines.append(f"  - `{r['id']}` oczekiwane: *{exp}* | model: \"{got}\"{flag}")
        lines.append("")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Zapisano result card: {args.out}")


if __name__ == "__main__":
    main()
