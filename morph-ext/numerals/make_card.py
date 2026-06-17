"""
Karta wynikow dla pod-tracku liczebnikow.

Czyta surowe odpowiedzi zapisane przez evaluator_lizzy.py (results/*.json)
i przelicza je ponownie z dopasowaniem na granicy slowa (jak evaluator v2
kwiscion), zamiast czystego substringu. Grupuje wynik per zapis (slownie /
cyfra / cyfra z kropka), bo o to chodzi w tym zestawie: czy ten sam item
punktuje inaczej zaleznie od tego, jak zapisano liczbe.

Uzycie:
    python make_card.py
    python make_card.py --tests polish_numerals_tests.json --results results --out results/CARD.md
"""

import argparse
import glob
import json
import os
import re
from collections import defaultdict


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().rstrip(".").lower())


def word_match(form: str, text: str) -> bool:
    """Dopasowanie z granica slowa (nie substring): 'piąte' nie wpadnie w 'piątego'."""
    return re.search(r"(?<!\w)" + re.escape(norm(form)) + r"(?!\w)", text) is not None


def score(response: str, test: dict) -> dict:
    r = norm(response)
    matched = next((a for a in test["acceptable"] if word_match(a, r)), None)
    dist = [d for d in test.get("distractor", []) if word_match(d, r) and norm(d) != norm(matched or "")]
    return {"passed": matched is not None, "matched": matched, "hit_distractor": bool(dist), "distractors": dist}


def load_tests(path: str) -> dict:
    data = json.load(open(path, encoding="utf-8"))
    return {t["id"]: t for t in data["tests"]}


def pct(p: int, t: int) -> str:
    return f"{p}/{t} ({(100 * p // t) if t else 0}%)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", default="polish_numerals_tests.json")
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", default="results/CARD.md")
    args = ap.parse_args()

    tests = load_tests(args.tests)
    runs = []
    for fp in sorted(glob.glob(os.path.join(args.results, "*.json"))):
        data = json.load(open(fp, encoding="utf-8"))
        if "results" in data and "model" in data:
            runs.append(data)

    if not runs:
        print("Brak plikow wynikowych w", args.results)
        return

    lines = []
    lines.append("# Karta wynikow: liczebniki (pod-track PL-MT)")
    lines.append("")
    lines.append(f"- Zbior: `{os.path.basename(args.tests)}` ({len(tests)} itemow, held-out)")
    lines.append("- Scoring: dopasowanie z granica slowa (jak evaluator v2), temperatura 0, tylko agregaty")
    lines.append("- Pointa: ten sam item w roznych zapisach liczby (slownie / cyfra / cyfra z kropka)")
    lines.append("")

    for run in runs:
        model = run["model"]
        by_id = {row["id"]: row.get("response", "") for row in run["results"]}

        overall_p = overall_t = 0
        cat = defaultdict(lambda: [0, 0])
        notation = defaultdict(lambda: [0, 0])
        errors = []
        for tid, t in tests.items():
            if tid not in by_id:
                continue
            res = score(by_id[tid], t)
            overall_t += 1
            cat[t["category"]][1] += 1
            notation[t["notation"]][1] += 1
            if res["passed"]:
                overall_p += 1
                cat[t["category"]][0] += 1
                notation[t["notation"]][0] += 1
            else:
                errors.append((tid, t, by_id[tid]))

        lines.append(f"## {model}")
        lines.append("")
        lines.append("```")
        lines.append(f"razem        {pct(overall_p, overall_t)}")
        lines.append("")
        lines.append("per kategoria:")
        for c in sorted(cat):
            lines.append(f"  {c:<10} {pct(cat[c][0], cat[c][1])}")
        lines.append("")
        lines.append("per zapis liczby:")
        for n in ["slownie", "cyfra", "cyfra_kropka"]:
            if n in notation:
                lines.append(f"  {n:<13} {pct(notation[n][0], notation[n][1])}")
        lines.append("```")
        lines.append("")

        if errors:
            lines.append("Reprezentatywne bledy (item -> co model napisal):")
            for tid, t, resp in errors[:6]:
                short = re.sub(r"\s+", " ", resp).strip()
                if len(short) > 90:
                    short = short[:90] + "..."
                lines.append(f"- `{tid}` ({t['notation']}) oczekiwane: *{t['expected']}* | model: \"{short}\"")
            lines.append("")

    out = "\n".join(lines).rstrip() + "\n"
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    open(args.out, "w", encoding="utf-8").write(out)
    print("Zapisano", args.out)


if __name__ == "__main__":
    main()
