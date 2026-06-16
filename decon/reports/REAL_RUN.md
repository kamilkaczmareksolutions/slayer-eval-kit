# Realny przebieg decon: Wikipedia PL vs benchmarki PL

Streszczenie przebiegu na **realnych, publicznych danych** (pełny raport maszynowy: `REAL_RUN_report.md`, lista usunięć: `REAL_RUN_manifest.jsonl`, lineage: `../../data/DATA_CARD.md`).

## Konfiguracja

- Korpus: próbka Polskiej Wikipedii (1500 artykułów, `wikimedia/wikipedia 20231101.pl`, CC BY-SA).
- Zbiory testowe: Belebele pol_Latn (488 passusów), PolEmo2 test (820 recenzji), `_control_wiki` (30, pozytywna kontrola recall).
- Metoda: word 13-gram, `--fold-diacritics`, deterministycznie (blake2b).

## Wynik

| Zbiór testowy | Itemy | Trafione | % | Dok. korpusu skażone |
|---------------|------:|---------:|--:|---------------------:|
| _control_wiki | 30 | 30 | **100.0** | 30 |
| belebele_pol | 488 | 0 | 0.0 | 0 |
| polemo2_test | 820 | 0 | 0.0 | 0 |

**Skażone: 30/1500 (2.0%)**, wyłącznie kontrola pozytywna.

## Interpretacja (uczciwie)

1. **Recall = 100% na realnej prozie Wikipedii.** Każdy z 30 itemów kontrolnych (wycinki artykułów) został trafiony, a flagowany `corpus_id` zgadza się ze źródłowym artykułem (zweryfikowane: 30/30, 0 niedopasowań, 0 fałszywych trafień krzyżowych). To dowód, że detektor wyłapuje kontaminację wywodzącą się z Wikipedii, czyli realny scenariusz dla benchmarków typu DYK/PolQA/PoQuAD.
2. **Belebele i PolEmo2: 0% w tej próbce.** FLORES (Belebele) i recenzje (PolEmo2) nie pochodzą z Wikipedii, więc brak dosłownego pokrycia jest oczekiwany. To również wartościowy wynik: ta próbka korpusu jest czysta względem tych dwóch zbiorów (dla pełnego korpusu trzeba przeskanować całość, narzędzie skaluje się strumieniowo).

## Następny krok dla labu

Wskaż realny korpus treningowy (np. shard SpeakLeash) i pełne zbiory testowe leaderboardu, a `decon` przejdzie po nich strumieniowo i zwróci manifest do usunięcia. Dla benchmarków wywodzących się z Wikipedii spodziewany sygnał jest niezerowy.
