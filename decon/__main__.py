"""
decon: CLI dekontaminacji.

Przyklad:
    python -m decon \
        --corpus decon/fixtures/corpus_sample.jsonl \
        --tests  decon/fixtures/tests_sample.jsonl \
        --report decon/reports/sample_report.md \
        --manifest decon/reports/sample_manifest.jsonl

    # z near-dup MinHash (wymaga datasketch):
    python -m decon --corpus C.jsonl --tests T/ --minhash --report out.md
"""

import argparse
import sys

from .core import TestIndex, scan_corpus, list_test_sets
from .report import aggregate, build_report_md, write_manifest


def main(argv=None):
    ap = argparse.ArgumentParser(prog="decon", description="Dekontaminacja korpusu treningowego vs zbiory testowe (PL)")
    ap.add_argument("--corpus", required=True, help="Plik (.jsonl/.txt/.md) lub katalog z korpusem treningowym")
    ap.add_argument("--tests", required=True, help="Plik lub katalog ze zbiorami testowymi (kazdy plik = osobny zbior)")
    ap.add_argument("--report", required=True, help="Sciezka wyjsciowa raportu .md")
    ap.add_argument("--manifest", default=None, help="Sciezka wyjsciowa manifestu usuniec .jsonl")

    ap.add_argument("--n", type=int, default=13, help="Rozmiar n-gramu slownego (domyslnie 13)")
    ap.add_argument("--corpus-field", default="text", help="Pole tekstu w korpusie jsonl (domyslnie 'text')")
    ap.add_argument("--tests-field", default="text", help="Pole tekstu w testach jsonl (domyslnie 'text')")
    ap.add_argument("--fold-diacritics", action="store_true", help="Sprowadz polskie znaki do ASCII przy porownaniu")
    ap.add_argument("--min-ngram-tokens", type=int, default=5, help="Itemy krotsze = oznaczane jako krotkie (mniej pewne)")
    ap.add_argument("--min-hits", type=int, default=1, help="Min. wspolnych n-gramow, by zglosic kontaminacje")
    ap.add_argument("--min-containment", type=float, default=0.0, help="Min. pokrycie itemu testowego (0..1)")

    ap.add_argument("--minhash", action="store_true", help="Dodatkowo near-dup MinHash (datasketch)")
    ap.add_argument("--minhash-threshold", type=float, default=0.8)
    ap.add_argument("--num-perm", type=int, default=128)
    ap.add_argument("--shingle", type=int, default=5)

    ap.add_argument("--embed", action="store_true", help="Dodatkowo near-dup embeddingowy (sentence-transformers, CPU)")
    ap.add_argument("--embed-threshold", type=float, default=0.85)
    ap.add_argument("--embed-model", default="paraphrase-multilingual-MiniLM-L12-v2")

    ap.add_argument("--max-samples", type=int, default=20, help="Ile dopasowan pokazac w raporcie")
    ap.add_argument("--progress-every", type=int, default=0, help="Log co N dokumentow korpusu (0 = cisza)")
    args = ap.parse_args(argv)

    test_paths = list_test_sets(args.tests)
    if not test_paths:
        print(f"Brak zbiorow testowych w: {args.tests}", file=sys.stderr)
        return 2

    print(f"Buduje indeks n-gramow ({args.n}-gram) z {len(test_paths)} zbioru/ow testowych...")
    index = TestIndex.build(
        test_paths, field_name=args.tests_field, n=args.n,
        fold_diacritics=args.fold_diacritics, min_ngram_tokens=args.min_ngram_tokens,
    )
    print(f"  itemow testowych: {len(index.items)} | unikalnych n-gramow: {len(index.gram_to_items)} "
          f"| krotkich itemow: {index.short_items}")

    print(f"Skanuje korpus: {args.corpus}")
    matches, n_docs = scan_corpus(
        args.corpus, index, corpus_field=args.corpus_field,
        min_hits=args.min_hits, min_containment=args.min_containment,
        progress_every=args.progress_every,
    )
    print(f"  n-gram: {len(matches)} trafien w {n_docs} dokumentach")

    if args.minhash:
        from .near_dup import scan_minhash
        mh, _ = scan_minhash(args.corpus, index, args.corpus_field,
                             threshold=args.minhash_threshold, num_perm=args.num_perm,
                             shingle=args.shingle)
        print(f"  minhash: +{len(mh)} trafien")
        matches += mh

    if args.embed:
        from .near_dup import scan_embed
        em, _ = scan_embed(args.corpus, index, args.corpus_field,
                           threshold=args.embed_threshold, model_name=args.embed_model)
        print(f"  embed: +{len(em)} trafien")
        matches += em

    agg = aggregate(matches, index, n_docs)

    config = {
        "corpus": args.corpus, "tests": args.tests, "n": args.n,
        "min_hits": args.min_hits, "min_containment": args.min_containment,
        "minhash": args.minhash, "minhash_threshold": args.minhash_threshold, "num_perm": args.num_perm,
        "embed": args.embed, "embed_threshold": args.embed_threshold, "embed_model": args.embed_model,
    }
    report = build_report_md(agg, index, matches, config, max_samples=args.max_samples)

    from pathlib import Path
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(report, encoding="utf-8")
    print(f"\nRaport: {args.report}")

    if args.manifest:
        n_manifest = write_manifest(args.manifest, matches)
        print(f"Manifest usuniec: {args.manifest} ({n_manifest} dokumentow do usuniecia)")

    print(f"\nSKAZONE: {agg['n_flagged_docs']}/{agg['n_corpus_docs']} ({agg['flagged_pct']}%) dokumentow korpusu")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
