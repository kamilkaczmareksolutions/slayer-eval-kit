# slayer-eval-kit

**Eval Integrity Stack** dla polskich LLM-ów: trzy małe, reproduktywne narzędzia, które pilnują, żeby pomiar był uczciwy, zanim ktokolwiek wytrenuje model.

> Czyste dane, czysty pomiar, celowana diagnoza.

Kontrybucja do [Slayer](https://slayer.fabryka.ai), applied research labu dla polskich modeli językowych. Każdy moduł jest samodzielny, odpalany jednym poleceniem, działa na CPU/laptopie (4 GB VRAM) i kończy się artefaktem, który da się otworzyć, odpalić i ocenić.

## Moduły

| Moduł | Co robi | Mapuje na |
|-------|---------|-----------|
| [`decon/`](decon/) | Dekontaminacja: n-gram + MinHash overlap korpusu treningowego vs zbiory testowe | `/zadania` #06, zasada "Held-out albo nic" |
| [`mcq/`](mcq/) | Harness MCQ z dwoma trybami scoringu (generative-letter vs likelihood) | `/zadania` #01/#04, debata LLMzSzŁ |
| [`morph-ext/`](morph-ext/) | Rozszerzenie Polish Morphology Benchmark o zmierzone failure mody | seed lizzy-606, pomiar sygrydstorrada |

## Dlaczego ten zestaw

Slayer ma jedną twardą zasadę: **publiczne twierdzenia tylko z held-out, mierzone tym samym protokołem co baseline**. Cała reszta (datasety, recepty, leaderboard) zależy od tego, czy ten warunek jest spełniony. Lab już raz się o to potknął ("Okazało się że trenowałem na train secie benchmarku"). Ten zestaw daje każdemu w labie powtarzalne narzędzie i zamyka problem u źródła.

## Bramki akceptacji (każdy artefakt je spełnia)

- **Held-out albo nic**: wyniki tylko z danych, których model nie widział.
- **Tylko agregaty**: per kategoria/domena; itemy benchmarku nie trafiają do treningu.
- **Lineage + disclosure**: skąd dane, jaka licencja, jaka wersja.
- **Otwarty sędzia**: gdy ocenia LLM, podaj otwarte wagi, prompt i wersję.
- **Koszt jest wynikiem**: model, tryb, n, seed i czas są częścią result card.
- **Reproducibility**: stały seed, jedno polecenie odtwarza wynik.

## Szybki start

```bash
# decon dziala bez zadnych instalacji (czysty stdlib)
python -m decon --corpus decon/fixtures/corpus_sample.jsonl \
                --tests  decon/fixtures/tests_sample.jsonl \
                --report decon/reports/sample_report.md

# mcq wymaga uruchomionego modelu (Ollama lokalnie lub API)
python -m mcq --data mcq/data/test_mcq.jsonl --fewshot mcq/data/fewshot_mcq.jsonl \
              --model ollama/llama3.2:3b --mode both --n-shots 5 \
              --save mcq/results/llama32_3b.json

# morph-ext rozszerza benchmark lizzy-606
python morph-ext/evaluator_lizzy.py --file morph-ext/polish_morph_tests_ext.json --dry-run
```

## Środowisko docelowe

Budowane i testowane na: Windows 11, Python 3.10, i7-9750H, 32 GB RAM, NVIDIA Quadro T1000 4 GB VRAM.
Modele lokalne przez Ollama (`llama3.2:3b`); większe (Bielik-11B, Qwen3.5-27B) przez API (OpenRouter / OpenAI-compatible).

## Licencja

MIT, plik [LICENSE](LICENSE). Dane testowe i wyniki służą wyłącznie do **ewaluacji** (dekontaminacja przed treningiem), nie do treningu.
