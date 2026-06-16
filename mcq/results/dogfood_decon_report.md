# Raport dekontaminacji

- Wygenerowano: 2026-06-16 14:58 UTC
- Korpus: `mcq/data/fewshot_mcq.jsonl` (5 dokumentow)
- Zbiory testowe: `mcq/data/test_mcq.jsonl` (1 zbiorow, 32 itemow; krotkich <5 tok.: 3)
- Metoda: word 5-gram, fold_diacritics=False, min_hits=1, min_containment=0.0

## Podsumowanie

- **Skazone dokumenty korpusu: 0 / 5 (0.0%)**
- Trafienia wg metody: brak

## Kontaminacja per zbior testowy

| Zbior testowy | Itemy | Itemy trafione | % itemow | Dok. korpusu skazone |
|---------------|------:|---------------:|---------:|---------------------:|
| test_mcq | 32 | 0 | 0.0 | 0 |

## Co dalej

1. Usun z korpusu treningowego wiersze z `corpus_id` wymienione w manifeście.
2. Powtorz skan -> oczekiwany wynik: 0 skazonych dokumentow.
3. Twierdzenia benchmarkowe formuluj dopiero na wyczyszczonym korpusie (held-out = held-out).
