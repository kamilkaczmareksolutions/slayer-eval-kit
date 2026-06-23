# Liczebniki: pod-track do Polish Morphology Benchmark (metoda)

Osobny zestaw na liczebniki, testujący te same zjawiska w różnych zapisach liczby.
Pomysł Lizzy-606 (#benchmarki, 2026-06-17): liczebniki to osobny temat, bo to pojęcie
matematyczne zakodowane w morfologii. Warto je sprawdzić w trzech zapisach, bo to dla
modelu trzy różne zadania:

- `slownie` liczba słowem ("pięć dzieci")
- `cyfra` liczba cyfrą ("5 dzieci")
- `cyfra_kropka` liczebnik porządkowy cyfrą z kropką ("5. miejsce"), gdzie kropka to marker fleksyjny

Punkt wyjścia: liczebniki zbiorowe jako systematyczny fail zgłosiła sygrydstorrada (#general, 2026-06-12).

## Co tu jest

Tu zostaje sama metoda, bez danych:

- `make_card.py` przelicza odpowiedzi z dopasowaniem na granicy słowa (jak evaluator v2)
  i rozbija wynik per zapis liczby (słownie, cyfrą, cyfrą z kropką).

## Dane (held-out)

Zestaw zadań (`polish_numerals_tests.json`) i wyniki są held-out, więc nie trzymam ich
publicznie. Żyją w prywatnym repo `slayerlabs/datasets` pod `data/eval/plmt/numerals/`
(PR: slayerlabs/datasets#4). To zgodne z zasadą projektu: zbiory ewaluacyjne nie idą do
publicznego repo, żeby nie wpłynęły do treningu.

## Jak odpalić (z dostępem do datasets)

```bash
# zestaw zadań pobierz z prywatnego datasets (data/eval/plmt/numerals/)
python ../evaluator_lizzy.py --file polish_numerals_tests.json --model ollama/llama3.2:3b --save runs/results_llama32_3b.json
python ../evaluator_lizzy.py --file polish_numerals_tests.json --model ollama/qwen2.5:3b --save runs/results_qwen25_3b.json
python make_card.py
```

## Wynik próbny (2 małe modele, n=26)

Liczebniki zbiorowe lecą po dnie u obu modeli. Zapis cyfrowy wypada gorzej niż słowny
(`cyfra` 0/8), a porządkowe z kropką trudniejsze niż podane słownie. To sygnał, nie wyrok;
kanoniczne liczby najlepiej policzyć evaluatorem v2 na pełnym zestawie modeli.

## Kredyty

- **@lizzy-606**: schemat PL-MT, pomysl na liczebniki jako osobny temat, trzy warianty zapisu
  (slownie / cyfra / cyfra z kropka), analizy morfologii vs instrukcji.
- **@kwiscion**: evaluator v2 (set-equality, tryby `match`: cases/forms), merge PL-MT v0.2
  (slayer PR #34, datasets PR #3).
- **sygrydstorrada**: zgloszenie failure modu liczebnikow zbiorowych.
- **Kamil Kaczmarek**: pod-track liczebnikow, 26 probek, PR datasets #4.
