# MCQ: karta wyniku (generative-letter vs likelihood)

Harness: `python -m mcq`. Sędzia: dopasowanie litery (otwarty, deterministyczny). Dekodowanie: temp 0, seed 0. Koszt: $0 (lokalnie, Ollama/CPU+iGPU).

## Konfiguracja

| pole | wartość |
|---|---|
| itemów (held-out) | 32 |
| few-shot | 5-shot (pula rozłączna z testem, zdekontaminowana) |
| tasowanie opcji | tak (anty-bias pozycji, seed 0) |
| kategorie | geografia, jezyk_polski, matematyka, wiedza_ogolna |
| modele | llama3.2:3b, qwen2.5:3b |

## Wynik zbiorczy (accuracy)

| model | generative | likelihood | Δ (lik−gen) |
|---|---|---|---|
| llama3.2:3b | 21/32 (65.6%) | 21/32 (65.6%) | +0 |
| qwen2.5:3b | 22/32 (68.8%) | 22/32 (68.8%) | +0 |

## Per kategoria

| model | tryb | geografia | jezyk_polski | matematyka | wiedza_ogolna |
|---|---|---|---|---|---|
| llama3.2:3b | generative | 5/8 | 7/8 | 4/8 | 5/8 |
| llama3.2:3b | likelihood | 5/8 | 7/8 | 4/8 | 5/8 |
| qwen2.5:3b | generative | 5/8 | 7/8 | 4/8 | 6/8 |
| qwen2.5:3b | likelihood | 5/8 | 7/8 | 4/8 | 6/8 |

## Generative vs likelihood: zgodność predykcji

Ten sam prompt, różny odczyt. „Zgodność" = oba tryby wskazały tę samą opcję. Tabela rozkłada przypadki, w których tryby się różnią. To sygnał z dyskusji (#benchmarki): wybór protokołu potrafi zmienić werdykt na itemie.

| model | zgodność predykcji | oba dobrze | oba źle | tylko gen | tylko lik |
|---|---|---|---|---|---|
| llama3.2:3b | 32/32 (100.0%) | 21 | 11 | 0 | 0 |
| qwen2.5:3b | 32/32 (100.0%) | 22 | 10 | 0 | 0 |

_Brak rozbieżności gen/lik w tej próbce: przy tych modelach oba protokoły dały tę samą predykcję na każdym itemie (różnica może ujawnić się przy słabszych modelach lub trudniejszym zbiorze)._

## Margines pewności likelihood (czego generative nie widzi)

Argmax obu trybów bywa zgodny, ale likelihood podaje dodatkowo **margines** = logprob(1. litera) − logprob(2. litera). To sygnał kalibracji, który tryb generative bezpowrotnie traci. Jeśli margines na itemach poprawnych jest większy niż na błędnych, model „wie, czego nie wie", i to widać tylko w likelihood.

| model | margines (poprawne) | margines (błędne) | rozdzielczość |
|---|---|---|---|
| llama3.2:3b | 4.47 | 2.11 | 2.36 |
| qwen2.5:3b | 15.70 | 9.46 | 6.24 |

_Margines w nats (logprob naturalny). Większa „rozdzielczość" = lepsza kalibracja: błędy padają przy niższej pewności._

## Taksonomia błędów (itemy oblane przez wszystkie modele i tryby)

Itemów oblanych przez wszystkie modele/tryby: **7**. Rozkład po kategoriach:

- `matematyka`: 3
- `geografia`: 3
- `wiedza_ogolna`: 1

| id | kat. | pytanie | poprawna |
|---|---|---|---|
| ge_04 | geografia | Najwyższy szczyt Polski to: | Rysy |
| ge_05 | geografia | Który kontynent jest najmniejszy pod względem powierzchni? | Australia |
| ge_07 | geografia | Które z państw sąsiaduje z Polską od południa? | Czechy |
| ma_06 | matematyka | Ile wynosi 2 do potęgi 5? | 32 |
| ma_07 | matematyka | Ile wynosi suma 125 + 375? | 500 |
| ma_08 | matematyka | Ile minut ma 2,5 godziny? | 150 |
| wo_07 | wiedza_ogolna | Ile planet liczy Układ Słoneczny według definicji z 2006 roku? | Osiem |

## Zgodność z bramkami Slayera

- **Held-out**: zbiór testowy rozłączny z pulą few-shot; rozłączność potwierdzona `decon` (dogfooding, patrz `dogfood_decon_report.md`).
- **Tylko agregaty**: raport podaje wyniki per kategoria; pojedyncze itemy widoczne wyłącznie diagnostycznie, nie jako eksport datasetu.
- **Otwarty sędzia**: parsowanie litery + odczyt logprob; deterministyczne, bez modelu-sędziego.
- **Koszt = część wyniku**: $0 (lokalnie). Dla modeli API koszt należy dopisać do karty.
- **Reprodukcja**: `python -m mcq --data … --fewshot … --model … --mode both --n-shots 5` (temp 0, seed 0). Uwaga: backend potrafi dać rzadki dryf ±1 itemu między uruchomieniami.
