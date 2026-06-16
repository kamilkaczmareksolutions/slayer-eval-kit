# DATA CARD: realne dane do dekontaminacji

Pobrane przez `scripts/fetch_pl_testsets.py` do `data/downloaded/` (gitignore/cursorignore).
Wyłącznie do **ewaluacji** (dekontaminacja przed treningiem). Nie wprowadzać do treningu.

| Rola | Plik | N | Źródło / licencja |
|------|------|--:|-------------------|
| corpus | `downloaded/corpus_wikipedia_pl.jsonl` | 1500 | wikimedia/wikipedia 20231101.pl / CC BY-SA 4.0 (próbka strumieniowa, ≤4000 zn./art.) |
| belebele_pol | `downloaded/tests/belebele_pol.jsonl` | 488 | Belebele pol_Latn (FLORES) / CC BY-SA 4.0, unikalne passusy |
| polemo2_test | `downloaded/tests/polemo2_test.jsonl` | 820 | clarin-pl/polemo2-official (split test) / CC BY-NC-SA 4.0, recenzje |
| _control_wiki | `downloaded/tests/_control_wiki.jsonl` | 30 | pozytywna kontrola recall: wycinki artykułów korpusu (symulacja benchmarku z Wikipedii) |

## Schemat (przy okazji `/zadania` #02)

Wszystkie pliki to JSONL z polem `text` (+ `id`). Korpus i zbiory testowe mają ten sam,
minimalny schemat, więc `decon` czyta je bez konwersji:

```json
{"id": "wiki_12345", "text": "..."}
```

`_control_wiki.jsonl` dodatkowo niesie `source_corpus_id` (z którego artykułu pochodzi wycinek)
i służy do weryfikacji recall (flagowany `corpus_id` musi się zgadzać ze źródłem).

## Dlaczego Wikipedia jako korpus

Polska Wikipedia jest składnikiem większości korpusów pretreningowych PL (w tym SpeakLeash),
więc jest realistycznym stand-inem. Benchmarki wywodzące się z Wikipedii (np. DYK „Czy wiesz",
PolQA, PoQuAD) są szczególnie narażone na kontaminację takim korpusem, i to ten scenariusz
mierzymy. Belebele/FLORES i PolEmo2 (recenzje) pochodzą spoza Wikipedii, więc oczekiwana
kontaminacja względem tej próbki jest niska, co również jest wartościowym, uczciwym wynikiem
(pokazuje, że próbka korpusu jest czysta względem tych konkretnych zbiorów).

## Odtworzenie

```bash
python scripts/fetch_pl_testsets.py --corpus-size 1500 --control 30
```
