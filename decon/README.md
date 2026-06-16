# decon: dekontaminacja danych treningowych (PL)

Flagowy moduł zestawu. Odpowiada na `/zadania` #06 ("Skrypt dekontaminacji") i na zasadę #1 labu: **held-out albo nic**. Lab już raz się o to potknął ("Okazało się że trenowałem na train secie benchmarku"). To narzędzie zamyka problem u źródła.

Wejście: korpus treningowy (jsonl/txt/katalog) + zbiory testowe. Wyjście: **raport kontaminacji** (tylko agregaty) + **manifest wierszy do usunięcia**.

## Zero zależności w rdzeniu

Detekcja n-gramowa działa na czystym `stdlib` (Python 3.10+). Tryby near-dup są opcjonalne:

| Tier | Co łapie | Zależność | Flaga |
|------|----------|-----------|-------|
| n-gram (13) | **dosłowne** wystąpienie itemu testowego w korpusie | brak (stdlib) | domyślnie |
| n-gram + fold | duplikaty różniące się **tylko diakrytykami** | brak | `--fold-diacritics` |
| MinHash/Jaccard | **near-dupy** całych dokumentów (drobne edycje) | `datasketch` | `--minhash` |
| Embedding (CPU) | **parafrazy / semantyczne** dupy | `sentence-transformers` | `--embed` |

Architektura jest pamięciooszczędna: indeks n-gramów **zbiorów testowych** (małych) trzymany w RAM; **korpus** (potencjalnie ogromny) czytany strumieniowo, dokument po dokumencie.

## Użycie

```bash
# Baseline (doslowna kontaminacja), bez instalacji
python -m decon \
  --corpus decon/fixtures/corpus_sample.jsonl \
  --tests  decon/fixtures/tests_sample.jsonl \
  --report decon/reports/sample_report.md \
  --manifest decon/reports/sample_manifest.jsonl

# Warstwowo: + diakrytyki + near-dup MinHash (dla krotkich itemow benchmarkowych
# mniejszy shingle i nizszy prog dzialaja lepiej niz domyslne 5/0.8 dla dlugich dokumentow)
python -m decon --corpus C.jsonl --tests T/ \
  --fold-diacritics --minhash --shingle 3 --minhash-threshold 0.6 \
  --report out.md --manifest manifest.jsonl

# Parafrazy (opcjonalnie, wymaga dzialajacego sentence-transformers):
python -m decon --corpus C.jsonl --tests T/ --embed --embed-threshold 0.85 --report out.md
```

Najważniejsze opcje: `--n` (rozmiar n-gramu, domyślnie 13), `--corpus-field`/`--tests-field` (pole tekstu w jsonl), `--min-containment` (próg pokrycia itemu), `--min-hits`.

## Format danych

- **jsonl**: pole `text` (konfigurowalne); jeśli jest pole `id`, trafia do raportu/manifestu.
- **txt/md**: jeden dokument na linię.
- **katalog**: dla `--tests` każdy plik to osobny zbiór testowy (nazwa pliku = nazwa zbioru w raporcie).

## Wynik

- **raport `.md`** podaje tylko agregaty: % skażonych dokumentów, kontaminacja per zbiór testowy (ile itemów trafionych), próbka dopasowań do diagnozy (skrócone fragmenty).
- **manifest `.jsonl`** ma jeden wiersz na skażony `corpus_id` z listą przyczyn (`test_set`, `test_item`, `method`, `score`). To jest lista do usunięcia z treningu.

## Demonstracja na fixtures

`decon/fixtures/` zawiera mini-korpus (17 dokumentów) z **zaplanowaną** kontaminacją wobec 10 itemów testowych w stylu Open PL LLM Leaderboard (PolEmo2/DYK/Belebele/PolQA/PoQuAD/KLEJ-NER/PolEval):

| Dokument | Typ kontaminacji | Łapie tier |
|----------|------------------|------------|
| `contam_verbatim_001..004` | dosłowne wklejenie itemu | n-gram |
| `contam_diacritic_001` | item bez polskich znaków | n-gram + `--fold-diacritics` |
| `contam_neardup_001` | item z 1 podmianą słowa (łamie każdy 13-gram) | `--minhash` |
| `contam_paraphrase_001` | parafraza (synonimy, inny szyk) | **tylko `--embed`** |

Pokazuje to, **gdzie kończy się dekontaminacja leksykalna, a zaczyna semantyczna**: `contam_paraphrase_001` przechodzi przez n-gram i MinHash, a wyłapuje go dopiero tier embeddingowy. Wynik:

- baseline n-gram: **4/17** (dosłowne), plik `reports/sample_report.md`
- + fold + MinHash: **6/17** (dosłowne + diakrytyki + near-dup), plik `reports/sample_report_layered.md`

## Realne dane

`scripts/fetch_pl_testsets.py` pobiera publiczne zbiory testowe i próbkę korpusu SpeakLeash do `data/downloaded/` (przez bibliotekę `datasets`). Patrz `data/DATA_CARD.md` (lineage + licencje). Realny przebieg i raport: `reports/REAL_RUN.md`.

## Bramki akceptacji (Slayer)

- Tylko agregaty w raporcie; pełne itemy testowe nie są wysypywane.
- Manifest dotyczy korpusu treningowego (co usunąć), nie testów.
- Deterministyczne (hash blake2b), jeden `python -m decon ...` odtwarza wynik.
- Lineage: raport zapisuje ścieżki, metodę, progi i wersję parametrów.
