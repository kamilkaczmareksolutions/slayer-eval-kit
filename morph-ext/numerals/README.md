# Liczebniki: pod-track do Polish Morphology Benchmark

Osobny zestaw na liczebniki, testujący te same zjawiska w różnych zapisach liczby.
Pomysł Lizzy-606 (#benchmarki, 2026-06-17): liczebniki to osobny temat, bo to
pojęcie matematyczne zakodowane w morfologii, a nie zwykły leksem. Warto je
sprawdzić w trzech zapisach, bo to dla modelu trzy różne zadania:

- `slownie` liczba podana słowem ("pięć dzieci")
- `cyfra` liczba podana cyfrą ("5 dzieci")
- `cyfra_kropka` liczebnik porządkowy cyfrą z kropką ("5. miejsce"), gdzie kropka
  to marker fleksyjny, nie koniec zdania

Punkt wyjścia: liczebniki zbiorowe jako systematyczny fail zgłosiła sygrydstorrada
(#general, 2026-06-12).

## Co jest w środku

- `polish_numerals_tests.json` 26 itemów, schemat zgodny z `polish_morph_tests_v02.json`
  (pole `level`), więc wchodzi prosto w evaluator. Dwie kategorie:
  - `NUM_COLL` (level 5) liczebniki zbiorowe, pary `slownie` i `cyfra` na tych samych zdaniach
  - `NUM_ORD` (level `null`, kandydat na osobny poziom) porządkowe, pary `cyfra_kropka` i `slownie`
  Pole `pair` łączy ten sam item w obu zapisach, żeby dało się je zestawić wprost.
- `make_card.py` przelicza surowe odpowiedzi z dopasowaniem na granicy słowa
  (jak evaluator v2), nie czystym substringiem, i rozbija wynik per zapis liczby.
- `results/` surowe odpowiedzi i karta.

## Jak odpalić

```bash
python ../evaluator_lizzy.py --file polish_numerals_tests.json --model ollama/llama3.2:3b --save results/llama32_3b.json
python ../evaluator_lizzy.py --file polish_numerals_tests.json --model ollama/qwen2.5:3b --save results/qwen25_3b.json
python make_card.py
```

## Wynik próbny (2 małe modele, n=26)

Pełna karta: `results/CARD.md`. Skrót:

- liczebniki zbiorowe lecą po dnie u obu modeli, co zgadza się z tym, co zgłaszała Nola
- zapis cyfrowy wypada gorzej niż słowny: `cyfra` 0/8 u obu modeli, `slownie` wyżej
- porządkowe z kropką (`cyfra_kropka`) wychodzą trudniej niż te same formy podane słownie

To małe modele i automatyczne sprawdzanie, więc traktować jako sygnał, nie wyrok.
Kanoniczne liczby najlepiej policzyć evaluatorem v2 na pełnym zestawie modeli.

## Uwagi

- Zbiór wyłącznie do ewaluacji (held-out). Nie wprowadzać do treningu.
- Dystraktory dobrane tak, żeby nie zawierały form akceptowanych przy granicy słowa.
- Kredyt za schemat i evaluator: lizzy-606. Tu dokładam tylko zestaw liczebników.
