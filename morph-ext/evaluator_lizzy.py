"""
Polish Morphology Evaluator
===========================

ATTRIBUTION / PROWENIENCJA
--------------------------
Ten plik jest VENDOROWANĄ (niezmienioną logicznie) kopią evaluatora autorstwa
**lizzy-606**, opublikowanego na Discordzie Slayer (#benchmarki, 2026-06-13)
razem z `polish_morph_tests.json` (v0.1) jako seed "Polish Morphology Benchmark".

Wklejony tutaj wyłącznie po to, by rozszerzenie `polish_morph_tests_ext.json`
dało się odpalić bez zewnętrznych zależności. Cały kredyt za projekt evaluatora
i schemat testów należy do lizzy-606. Propozycja: scalić nowe przypadki z
`polish_morph_tests_ext.json` do oryginalnego zbioru w repo Slayera.

Jedyna zmiana względem oryginału: ten nagłówek. Logika bez zmian.

Użycie:
    python evaluator_lizzy.py --file polish_morph_tests_ext.json --dry-run
    python evaluator_lizzy.py --file polish_morph_tests_ext.json --model ollama/llama3.2:3b --save out.json
    python evaluator_lizzy.py --file polish_morph_tests_ext.json --model gpt-4o-mini --tests NUM_COLL

API zgodne z OpenAI (np. OpenRouter): ustaw OPENAI_BASE_URL i OPENAI_API_KEY.

Wymagania:
    pip install openai requests rich
"""

import json
import argparse
import re
import sys
from pathlib import Path
from datetime import datetime


# ─── Ładowanie testów ────────────────────────────────────────────────────────

def load_tests(path: str = "polish_morph_tests.json", category_filter: str = None):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    tests = data["tests"]
    if category_filter:
        tests = [t for t in tests if t["category"] == category_filter]
    return tests


# ─── Sprawdzanie odpowiedzi ──────────────────────────────────────────────────

def normalize(text: str) -> str:
    """Małe litery, bez zbędnych spacji, bez kropki na końcu."""
    return re.sub(r"\s+", " ", text.strip().rstrip(".").lower())


def check_answer(response: str, test: dict) -> dict:
    """
    Zwraca dict z:
      - passed (bool)
      - matched_form (str lub None)
      - hit_distractor (bool)
    """
    r = normalize(response)

    # Sprawdź oczekiwane formy
    for form in test["acceptable"]:
        if normalize(form) in r:
            # Czy przy okazji trafił w dystraktory?
            distractors_hit = [
                d for d in test.get("distractor", [])
                if normalize(d) in r and normalize(d) != normalize(form)
            ]
            return {
                "passed": True,
                "matched_form": form,
                "hit_distractor": len(distractors_hit) > 0,
                "distractors_hit": distractors_hit
            }

    # Sprawdź czy trafił w dystraktory (częsty błąd)
    distractors_hit = [
        d for d in test.get("distractor", [])
        if normalize(d) in r
    ]

    return {
        "passed": False,
        "matched_form": None,
        "hit_distractor": len(distractors_hit) > 0,
        "distractors_hit": distractors_hit
    }


# ─── Adaptery modelów ────────────────────────────────────────────────────────

def query_openai(prompt: str, model: str = "gpt-4o") -> str:
    """Odpytuje OpenAI API (lub kompatybilne, np. OpenRouter przez OPENAI_BASE_URL)."""
    try:
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Jesteś ekspertem od gramatyki polskiej. "
                        "Odpowiadaj krótko i precyzyjnie — tylko forma lub formy, bez wyjaśnień, "
                        "chyba że pytanie wprost prosi o uzasadnienie."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        return response.choices[0].message.content
    except ImportError:
        print("Błąd: brak pakietu openai. Zainstaluj: pip install openai")
        sys.exit(1)


def query_ollama(prompt: str, model: str = "bielik") -> str:
    """Odpytuje lokalny Ollama."""
    import requests
    model_name = model.replace("ollama/", "")
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model_name,
            "prompt": (
                "Jesteś ekspertem od gramatyki polskiej. "
                "Odpowiadaj krótko i precyzyjnie.\n\n" + prompt
            ),
            "stream": False,
            "options": {"temperature": 0}
        },
        timeout=60
    )
    resp.raise_for_status()
    return resp.json()["response"]


def query_model(prompt: str, model: str) -> str:
    if model.startswith("ollama/"):
        return query_ollama(prompt, model)
    else:
        return query_openai(prompt, model)


# ─── Wyświetlanie wyników ────────────────────────────────────────────────────

def print_result(test: dict, response: str, result: dict, verbose: bool = False):
    status = "✓" if result["passed"] else "✗"
    distractor_warn = " [DYSTRAKTOR!]" if result["hit_distractor"] and not result["passed"] else ""

    print(f"\n{status} [{test['id']}] {test['category']}")
    print(f"  Pytanie:   {test['prompt']}")
    print(f"  Oczekiwane: {test['expected']}")

    if verbose or not result["passed"]:
        print(f"  Odpowiedź: {response.strip()}")

    if result["passed"]:
        print(f"  Forma: '{result['matched_form']}' ✓")
    else:
        print(f"  Brak oczekiwanej formy{distractor_warn}")
        if result["distractors_hit"]:
            print(f"  Trafione dystraktory: {result['distractors_hit']}")

    if verbose and test.get("note"):
        print(f"  Uwaga: {test['note']}")


def print_summary(results: list, model: str):
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    distractor_hits = sum(1 for r in results if r["hit_distractor"] and not r["passed"])

    print("\n" + "═" * 60)
    print(f"  Model: {model}")
    print(f"  Wynik: {passed}/{total} ({100*passed//total}%)")
    print(f"  Błędy z dystraktorami: {distractor_hits}")

    # Wyniki per kategoria
    categories = {}
    for i, r in enumerate(results):
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"passed": 0, "total": 0}
        categories[cat]["total"] += 1
        if r["passed"]:
            categories[cat]["passed"] += 1

    print("\n  Per kategoria:")
    for cat, stats in sorted(categories.items()):
        p = stats["passed"]
        t = stats["total"]
        bar = "█" * p + "░" * (t - p)
        print(f"    {cat:<20} {bar} {p}/{t}")

    print("═" * 60)
    return passed, total


def save_results(results: list, model: str, output_path: str = None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = re.sub(r"[^\w]", "_", model)
    if output_path is None:
        output_path = f"results_{safe_model}_{timestamp}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "model": model,
            "timestamp": timestamp,
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n  Wyniki zapisane: {output_path}")
    return output_path


# ─── Tryb dry-run ────────────────────────────────────────────────────────────

def dry_run(tests: list):
    print(f"\nZaładowano {len(tests)} testów:\n")
    for t in tests:
        print(f"  [{t['id']}] {t['category']}")
        print(f"    Pytanie:    {t['prompt']}")
        print(f"    Oczekiwane: {t['expected']}")
        print(f"    Dystraktory: {', '.join(t.get('distractor', []))}")
        if t.get("note"):
            print(f"    Uwaga: {t['note']}")
        print()


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Polish Morphology Evaluator — testuje modele na polskiej fleksji"
    )
    parser.add_argument(
        "--model", default="gpt-4o",
        help="Model do testowania: gpt-4o, gpt-4o-mini, ollama/bielik, ollama/llama3.2:3b itd."
    )
    parser.add_argument(
        "--tests", default=None,
        help="Filtruj po kategorii: NUM_COLL, REFLEXIVE, IMPERATIVE, CONS_ALT (lub kategorie v0.1)"
    )
    parser.add_argument(
        "--file", default="polish_morph_tests.json",
        help="Ścieżka do pliku z testami (domyślnie: polish_morph_tests.json)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Wyświetl testy bez odpytywania modelu"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Wyświetl pełne odpowiedzi modelu"
    )
    parser.add_argument(
        "--save", default=None,
        help="Ścieżka do zapisu wyników JSON"
    )
    parser.add_argument(
        "--skip-generative", action="store_true",
        help="Pomiń testy generatywne (is_generative=true) — trudniejsze do automatycznej oceny"
    )
    args = parser.parse_args()

    tests = load_tests(args.file, args.tests)

    if args.skip_generative:
        tests = [t for t in tests if not t.get("is_generative")]

    if args.dry_run:
        dry_run(tests)
        return

    print(f"\nPolish Morphology Evaluator — model: {args.model}")
    print(f"Testów do uruchomienia: {len(tests)}\n")

    all_results = []

    for test in tests:
        try:
            response = query_model(test["prompt"], args.model)
        except Exception as e:
            print(f"  Błąd zapytania [{test['id']}]: {e}")
            response = ""

        result = check_answer(response, test)
        result["category"] = test["category"]
        result["id"] = test["id"]
        result["response"] = response

        all_results.append(result)
        print_result(test, response, result, verbose=args.verbose)

    passed, total = print_summary(all_results, args.model)

    if args.save or len(all_results) > 0:
        save_results(all_results, args.model, args.save)


if __name__ == "__main__":
    main()
