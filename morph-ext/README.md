# morph-ext: rozszerzenie Polish Morphology Benchmark

Drop-in rozszerzenie seeda **lizzy-606** (`polish_morph_tests.json` v0.1, opublikowanego na `#benchmarki` 2026-06-13) o cztery kategorie pod **udokumentowane failure mody**.

## Dlaczego te kategorie

- **NUM_COLL, liczebniki zbiorowe.** sygrydstorrada w ewaluacji (#general, 2026-06-12) zaraportowała: *"Liczebniki zbiorowe (systematyczny fail): model konsekwentnie wykłada się... generuje formy 'pięć dzieci' (zamiast pięcioro) oraz 'trzech kociąt' (zamiast troje)."* To zmierzony, powtarzalny błąd, czyli to, co lab chce mierzyć ("naprawiamy konkretny, zmierzony failure mode").
- **REFLEXIVE, IMPERATIVE, CONS_ALT**: luki wymienione wprost przez autorkę w sekcji "Ograniczenia obecnej wersji" v0.1 (czasowniki zwrotne / pozycja `się`, tryb rozkazujący, alternacje spółgłoskowe).

## Co tu jest

| Plik | Rola |
|------|------|
| `polish_morph_tests_ext.json` | 44 nowe przypadki (NUM_COLL 13, REFLEXIVE 10, IMPERATIVE 11, CONS_ALT 10) w schemacie v0.1 |
| `evaluator_lizzy.py` | vendorowana kopia evaluatora lizzy-606 (logika bez zmian, dodany nagłówek atrybucji) |
| `make_result_card.py` | generator markdownowego result card (dorzut, nie zmienia evaluatora) |
| `results/` | wygenerowane wyniki + result card |

Schemat każdego przypadku jest identyczny z v0.1: `id, category, prompt, expected, acceptable, distractor, note` (+ `is_generative` gdzie trzeba). Dzięki temu **lizzy może wkleić te przypadki wprost** do `polish_morph_tests.json` albo trzymać jako osobny plik.

Dystraktory przeszły walidację: żaden nie zawiera formy akceptowanej jako podłańcuch (inaczej matcher `check_answer` dawałby false-pass). Walidacja jest częścią `c3` (skrypt w opisie poniżej).

## Jak odpalić

```bash
# 1. Podglad bez modelu
python evaluator_lizzy.py --file polish_morph_tests_ext.json --dry-run

# 2. Lokalnie na llama3.2:3b (Ollama)
python evaluator_lizzy.py --file polish_morph_tests_ext.json \
    --model ollama/llama3.2:3b --skip-generative \
    --save results/results_llama32_3b.json

# 3. Model przez API zgodne z OpenAI (np. OpenRouter)
#    set OPENAI_BASE_URL=https://openrouter.ai/api/v1  &&  set OPENAI_API_KEY=...
python evaluator_lizzy.py --file polish_morph_tests_ext.json \
    --model meta-llama/llama-3.2-3b-instruct \
    --save results/results_or_llama32.json

# 4. Result card (porownanie modeli)
python make_result_card.py --tests polish_morph_tests_ext.json \
    --results results/results_llama32_3b.json \
    --out results/CARD.md
```

`--skip-generative` pomija 5 przypadków wymagających pełnego zdania (ocena automatyczna jest tam przybliżona), zgodnie z konwencją evaluatora lizzy.

## Bramki akceptacji (Slayer)

- Held-out, tylko do ewaluacji: przypadki nie wchodzą do treningu.
- Tylko agregaty per kategoria + reprezentatywna próbka błędów.
- Sędzia = matcher regułowy (substring), nie LLM, więc pełna reprodukowalność, temperatura 0.
- Prowienencja jawna: bazuje na seedzie lizzy-606, motywowane pomiarem sygrydstorrada.

## Następny krok (poza zakresem v1)

Autorka zaznaczyła docelowy generator oparty o słownik morfologiczny (Morfeusz2 / PoliMorf), produkujący testy dla dowolnego lematu. To naturalne rozszerzenie po akceptacji tej partii, poza zakresem v1 (zasada „simplicity first": najpierw zmierzyć znany failure mode małym, czystym zbiorem).
