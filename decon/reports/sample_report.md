# Raport dekontaminacji

- Wygenerowano: 2026-06-16 13:46 UTC
- Korpus: `decon/fixtures/corpus_sample.jsonl` (17 dokumentow)
- Zbiory testowe: `decon/fixtures/tests_sample.jsonl` (1 zbiorow, 10 itemow; krotkich <5 tok.: 0)
- Metoda: word 13-gram, fold_diacritics=False, min_hits=1, min_containment=0.0

## Podsumowanie

- **Skazone dokumenty korpusu: 4 / 17 (23.5294%)**
- Trafienia wg metody: {'ngram': 4}

## Kontaminacja per zbior testowy

| Zbior testowy | Itemy | Itemy trafione | % itemow | Dok. korpusu skazone |
|---------------|------:|---------------:|---------:|---------------------:|
| tests_sample | 10 | 4 | 40.0 | 4 |

## Probka dopasowan (diagnostycznie)

| corpus_id | zbior | item | score | metoda | fragment itemu testowego |
|-----------|-------|------|------:|--------|--------------------------|
| `contam_verbatim_001` | tests_sample | polemo2_001 | 1.0 | ngram | Obsługa w tej restauracji była wyjątkowo miła i profesjonaln... |
| `contam_verbatim_002` | tests_sample | dyk_001 | 1.0 | ngram | Czy wiesz, że najdłuższą rzeką w Polsce jest Wisła, która li... |
| `contam_verbatim_003` | tests_sample | belebele_001 | 1.0 | ngram | Zgodnie z fragmentem tekstu autor podkreśla, że zmiany klima... |
| `contam_verbatim_004` | tests_sample | poquad_001 | 1.0 | ngram | Fotosynteza to proces, w którym rośliny przekształcają dwutl... |

## Co dalej

1. Usun z korpusu treningowego wiersze z `corpus_id` wymienione w manifeście.
2. Powtorz skan -> oczekiwany wynik: 0 skazonych dokumentow.
3. Twierdzenia benchmarkowe formuluj dopiero na wyczyszczonym korpusie (held-out = held-out).
