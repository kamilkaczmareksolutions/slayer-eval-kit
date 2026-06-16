# Raport dekontaminacji

- Wygenerowano: 2026-06-16 13:56 UTC
- Korpus: `data/downloaded/corpus_wikipedia_pl.jsonl` (1500 dokumentow)
- Zbiory testowe: `data/downloaded/tests` (3 zbiorow, 1338 itemow; krotkich <5 tok.: 1)
- Metoda: word 13-gram, fold_diacritics=True, min_hits=1, min_containment=0.0

## Podsumowanie

- **Skazone dokumenty korpusu: 30 / 1500 (2.0%)**
- Trafienia wg metody: {'ngram': 30}

## Kontaminacja per zbior testowy

| Zbior testowy | Itemy | Itemy trafione | % itemow | Dok. korpusu skazone |
|---------------|------:|---------------:|---------:|---------------------:|
| _control_wiki | 30 | 30 | 100.0 | 30 |
| belebele_pol | 488 | 0 | 0.0 | 0 |
| polemo2_test | 820 | 0 | 0.0 | 0 |

## Probka dopasowan (diagnostycznie)

| corpus_id | zbior | item | score | metoda | fragment itemu testowego |
|-----------|-------|------|------:|--------|--------------------------|
| `wiki_2` | _control_wiki | control_wiki_2 | 1.0 | ngram | język programowania, którego główną funkcją jest wyszukiwani... |
| `wiki_4` | _control_wiki | control_wiki_4 | 1.0 | ngram | medycyny zajmująca się rozpoznawaniem i leczeniem schorzeń a... |
| `wiki_6` | _control_wiki | control_wiki_6 | 1.0 | ngram | skrót od ang. American Standard Code for Information Interch... |
| `wiki_7` | _control_wiki | control_wiki_7 | 1.0 | ngram | składnik materii. Składa się z małego dodatnio naładowanego ... |
| `wiki_8` | _control_wiki | control_wiki_8 | 1.0 | ngram | (gr. axíōma, godność, pewność, oczywistość) – jedno z podsta... |
| `wiki_10` | _control_wiki | control_wiki_10 | 1.0 | ngram | gr. ἀριθμητική arithmētikē, z ἀριθμός – liczba) – dział mate... |
| `wiki_12` | _control_wiki | control_wiki_12 | 1.0 | ngram | związki chemiczne z grupy węglowodorów nienasyconych, w któr... |
| `wiki_13` | _control_wiki | control_wiki_13 | 1.0 | ngram | biblioteka komponentów i kontrolek stworzona przez Microsoft... |
| `wiki_14` | _control_wiki | control_wiki_14 | 1.0 | ngram | interfejs programistyczny aplikacji, interfejs programu apli... |
| `wiki_15` | _control_wiki | control_wiki_15 | 1.0 | ngram | operacyjny opracowany przez firmę Commodore International dl... |
| `wiki_16` | _control_wiki | control_wiki_16 | 1.0 | ngram | Machinery (ACM) to największa na świecie społeczność ludzi n... |
| `wiki_18` | _control_wiki | control_wiki_18 | 1.0 | ngram | alternatywa zwykła, alternatywa nierozłączna, alternatywa łą... |
| `wiki_19` | _control_wiki | control_wiki_19 | 1.0 | ngram | aksjomat, a właściwie nieskończony przeliczalny zbiór aksjom... |
| `wiki_21` | _control_wiki | control_wiki_21 | 1.0 | ngram | związki chemiczne, węglowodory nienasycone, w których jeden ... |
| `wiki_22` | _control_wiki | control_wiki_22 | 1.0 | ngram | – grupa organicznych związków chemicznych będących węglowodo... |
| `wiki_23` | _control_wiki | control_wiki_23 | 1.0 | ngram | = mało powinowaty) – łańcuchowe węglowodory nasycone, organi... |
| `wiki_24` | _control_wiki | control_wiki_24 | 1.0 | ngram | organiczne zawierające jedną lub więcej grup hydroksylowych ... |
| `wiki_25` | _control_wiki | control_wiki_25 | 1.0 | ngram | polityczna i ruch społeczny, które cechują się niechęcią wob... |
| `wiki_26` | _control_wiki | control_wiki_26 | 1.0 | ngram | "bez władcy") – forma struktury społeczno-politycznej, w któ... |
| `wiki_28` | _control_wiki | control_wiki_28 | 1.0 | ngram | Abstract Syntax Notation One – abstrakcyjna notacja składnio... |
| `wiki_29` | _control_wiki | control_wiki_29 | 1.0 | ngram | ciąg jasno zdefiniowanych czynności koniecznych do wykonania... |
| `wiki_30` | _control_wiki | control_wiki_30 | 1.0 | ngram | Agulhas (port. Cabo das Agulhas, wym. []) – przylądek stanow... |
| `wiki_31` | _control_wiki | control_wiki_31 | 1.0 | ngram | „alkohol odwodorniony”) – klasa organicznych związków chemic... |
| `wiki_32` | _control_wiki | control_wiki_32 | 1.0 | ngram | Mallowan, DBE, właśc. Agatha Mary Clarissa Miller Christie (... |
| `wiki_33` | _control_wiki | control_wiki_33 | 1.0 | ngram | z wersji genu. Allel najczęściej występuje w określonym locu... |

## Co dalej

1. Usun z korpusu treningowego wiersze z `corpus_id` wymienione w manifeście.
2. Powtorz skan -> oczekiwany wynik: 0 skazonych dokumentow.
3. Twierdzenia benchmarkowe formuluj dopiero na wyczyszczonym korpusie (held-out = held-out).
