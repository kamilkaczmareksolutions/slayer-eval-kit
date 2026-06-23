# morph-ext: rozszerzenie Polish Morphology Benchmark (metoda)

Drop-in rozszerzenie seeda **lizzy-606** (`polish_morph_tests.json` v0.1, opublikowanego na `#benchmarki` 2026-06-13) o cztery kategorie pod **udokumentowane failure mody**.

## Dlaczego te kategorie

- **NUM_COLL, liczebniki zbiorowe.** sygrydstorrada w ewaluacji (#general, 2026-06-12) zaraportowała: *"Liczebniki zbiorowe (systematyczny fail): model konsekwentnie wykłada się... generuje formy 'pięć dzieci' (zamiast pięcioro) oraz 'trzech kociąt' (zamiast troje)."* To zmierzony, powtarzalny błąd, czyli to, co lab chce mierzyć ("naprawiamy konkretny, zmierzony failure mode").
- **REFLEXIVE, IMPERATIVE, CONS_ALT**: luki wymienione wprost przez autorkę w sekcji "Ograniczenia obecnej wersji" v0.1 (czasowniki zwrotne / pozycja `się`, tryb rozkazujący, alternacje spółgłoskowe).

## Co tu jest (metoda, bez danych)

| Plik | Rola |
|------|------|
| `evaluator_lizzy.py` | vendorowana kopia evaluatora lizzy-606 (logika bez zmian, dodany nagłówek atrybucji) |
| `make_result_card.py` | generator markdownowego result card (dorzut, nie zmienia evaluatora) |
| `numerals/make_card.py` | karta wyników per zapis liczby (słownie / cyfra / cyfra z kropką) |

Schemat każdego przypadku w zestawie held-out jest identyczny z v0.1: `id, category, prompt, expected, acceptable, distractor, note` (+ `is_generative` gdzie trzeba).

## Dane (held-out)

Zestaw zadań (`polish_morph_tests_ext.json`, 44 przypadki) i wyniki próbne są held-out, więc nie trzymam ich publicznie. Żyją w prywatnym repo `slayerlabs/datasets` pod `data/eval/plmt/morph_ext/` (branch `plmt-morph-ext`). To zgodne z zasadą projektu: zbiory ewaluacyjne nie idą do publicznego repo, żeby nie wpłynęły do treningu.

## Jak odpalić (z dostępem do datasets)

```bash
# zestaw zadań pobierz z prywatnego datasets (data/eval/plmt/morph_ext/)
python evaluator_lizzy.py --file polish_morph_tests_ext.json --dry-run
python evaluator_lizzy.py --file polish_morph_tests_ext.json \
    --model ollama/llama3.2:3b --skip-generative \
    --save runs/results_llama32_3b.json
python make_result_card.py --tests polish_morph_tests_ext.json \
    --results runs/results_llama32_3b.json --out runs/CARD.md
```

`--skip-generative` pomija 5 przypadków wymagających pełnego zdania (ocena automatyczna jest tam przybliżona), zgodnie z konwencją evaluatora lizzy.

## Bramki akceptacji (Slayer)

- Held-out, tylko do ewaluacji: przypadki nie wchodzą do treningu.
- Tylko agregaty per kategoria + reprezentatywna próbka błędów.
- Sędzia = matcher regułowy (substring), nie LLM, więc pełna reprodukowalność, temperatura 0.
- Prowienencja jawna: bazuje na seedzie lizzy-606, motywowane pomiarem sygrydstorrada.

## Następny krok (poza zakresem v1)

Autorka zaznaczyła docelowy generator oparty o słownik morfologiczny (Morfeusz2 / PoliMorf), produkujący testy dla dowolnego lematu. To naturalne rozszerzenie po akceptacji tej partii, poza zakresem v1 (zasada „simplicity first": najpierw zmierzyć znany failure mode małym, czystym zbiorem).
