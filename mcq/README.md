# mcq: harness MCQ (PL), generative-letter vs likelihood

Mały runner pytań wielokrotnego wyboru, który adresuje punkt metodologiczny z dyskusji (#benchmarki): *generative-letter* i *likelihood (logprob)* to dwa różne protokoły pomiaru i potrafią dać inny sygnał. Ten moduł liczy oba na **tym samym promptcie**, pokazuje gdzie się rozjeżdżają i co likelihood widzi, a generative wyrzuca.

Wejście: zbiór MCQ (jsonl) + pula few-shot (jsonl). Wyjście: wynik per item (JSON) + **karta wyniku** (md, tylko agregaty).

## Dwa tryby, jeden prompt

| Tryb | Jak czyta odpowiedź | Co daje |
|------|---------------------|---------|
| `generative` | model generuje tekst, parsujemy pierwszą literę A-D | werdykt (jak człowiek czytający odpowiedź) |
| `likelihood` | czytamy rozkład `logprob` nad literami A-D na pierwszym tokenie (argmax) | werdykt + margines pewności |

Oba tryby dostają **identyczne tury chat** (system + few-shot jako pary user/assistant + pytanie), więc każda różnica w wyniku pochodzi ze sposobu odczytu odpowiedzi. To jest mierzony efekt.

## Użycie

```bash
# Lokalnie przez Ollama (jak Piotr Styla, llama3.2:3b)
python -m mcq \
  --data    mcq/data/test_mcq.jsonl \
  --fewshot mcq/data/fewshot_mcq.jsonl \
  --model   ollama/llama3.2:3b \
  --mode    both --n-shots 5 --seed 0 \
  --save    mcq/results/llama32_3b.json

# Karta wyniku z jednego lub wielu przebiegow (porownanie modeli)
python -m mcq.make_result_card \
  mcq/results/llama32_3b.json mcq/results/qwen25_3b.json \
  --out mcq/results/RESULT_CARD.md
```

Opcje: `--mode {generative,likelihood,both}`, `--n-shots`, `--seed`, `--no-shuffle-options` (domyślnie opcje są **tasowane** deterministycznie dla anty-biasu pozycji), `--limit` (smoke test).

Modele API (Bielik/Qwen/…) podłącza się przez analogiczny adapter; koszt trzeba wtedy dopisać do karty (bramka „koszt = część wyniku").

## Format danych

`jsonl`, jeden item na linię:

```json
{"id": "wo_01", "category": "wiedza_ogolna",
 "question": "Który pierwiastek ma symbol 'O'?",
 "options": ["Złoto", "Tlen", "Wodór", "Węgiel"], "answer": 1}
```

`answer` to indeks (0-based) albo litera (`"B"`). Pole `context` jest opcjonalne. Pula few-shot ma ten sam format i **musi być rozłączna ze zbiorem testowym** (patrz dogfooding niżej).

## Co pokazuje wynik

Karta (`results/RESULT_CARD.md`) zawiera:

1. **Accuracy zbiorcze** per model × tryb (+ Δ likelihood−generative).
2. **Per kategoria**: agregaty, bez pojedynczych itemów jako eksport.
3. **Zgodność gen/lik**: ile predykcji się pokrywa, rozkład „tylko gen / tylko lik".
4. **Margines pewności**: `logprob(1.) − logprob(2.)` na itemach poprawnych vs błędnych. To sygnał kalibracji, którego tryb generative **nie ma**.
5. **Taksonomia błędów**: itemy oblane przez wszystkie modele/tryby (konsensusowo trudne), z rozkładem po kategoriach.

### Wynik referencyjny (32 itemy, 5-shot, seed 0)

- `llama3.2:3b`: 21/32 (65.6%), `qwen2.5:3b`: 22/32 (68.8%), **identycznie w gen i lik**.
- Zgodność predykcji gen/lik: **100%** na tej próbce (silny system-prompt + temp 0, więc argmax się pokrywa).
- Margines pewności rozdziela poprawne od błędnych: llama 4.47 vs 2.11 (Δ2.36), qwen 15.70 vs 9.46 (Δ6.24 nats). **Błędy padają przy niższej pewności**, co widać tylko w likelihood.
- 7 itemów oblanych przez oba modele (matematyka ×3, geografia ×3, wiedza ×1).

Wniosek dla debaty: na czystym MCQ z instrukcją „jedna litera" oba protokoły dają ten sam werdykt, więc *do rankingu accuracy* są wymienne, a likelihood dokłada sygnał kalibracji. Rozjazd werdyktów spodziewam się przy słabszych/bazowych modelach i trudniejszych zbiorach; harness to wykryje (kolumny „tylko gen/lik").

## Dogfooding (stack działa razem)

Przed runem pula few-shot jest sprawdzana modułem `decon` względem zbioru testowego:

```bash
python -m decon --corpus mcq/data/fewshot_mcq.jsonl --tests mcq/data/test_mcq.jsonl \
  --corpus-field question --tests-field question --n 5 \
  --report mcq/results/dogfood_decon_report.md
# wynik: SKAZONE 0/5, few-shot rozlaczny z testem
```

## Bramki akceptacji (Slayer)

- **Held-out**: test rozłączny z few-shot, potwierdzone `decon`.
- **Tylko agregaty**: karta podaje wyniki per kategoria; itemy widoczne wyłącznie diagnostycznie.
- **Otwarty sędzia**: parsowanie litery + odczyt logprob, deterministyczne, bez modelu-sędziego (żadnego Opusa jako sędzia).
- **Koszt**: $0 lokalnie; dla API dopisywany do karty.
- **Reprodukcja**: temp 0, seed 0, jeden `python -m mcq …`. Backend bywa pseudodeterministyczny, możliwy rzadki dryf ±1 itemu.
