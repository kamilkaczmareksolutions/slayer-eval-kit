"""
mcq: CLI harnessu MCQ.

Przyklad:
    python -m mcq --data mcq/data/test_mcq.jsonl --fewshot mcq/data/fewshot_mcq.jsonl \
        --model ollama/llama3.2:3b --mode both --n-shots 5 \
        --save mcq/results/llama32_3b.json
"""

import argparse
import json
import sys
from pathlib import Path

from .harness import load_mcq, build_messages, score_generative, score_likelihood


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mcq", description="Harness MCQ PL (generative-letter vs likelihood)")
    ap.add_argument("--data", required=True, help="Zbior testowy MCQ (jsonl)")
    ap.add_argument("--fewshot", default=None, help="Pula few-shot (jsonl); brak = 0-shot")
    ap.add_argument("--model", default="ollama/llama3.2:3b")
    ap.add_argument("--mode", choices=["generative", "likelihood", "both"], default="both")
    ap.add_argument("--n-shots", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-shuffle-options", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="Ogranicz liczbe itemow (0 = wszystkie)")
    ap.add_argument("--save", required=True, help="Sciezka wyjsciowa wynikow JSON")
    args = ap.parse_args(argv)

    test = load_mcq(args.data, shuffle_options=not args.no_shuffle_options, seed=args.seed)
    if args.limit:
        test = test[: args.limit]
    fewshot = load_mcq(args.fewshot, shuffle_options=not args.no_shuffle_options, seed=args.seed + 1) \
        if args.fewshot else []
    n_shots = min(args.n_shots, len(fewshot))

    do_gen = args.mode in ("generative", "both")
    do_lik = args.mode in ("likelihood", "both")

    print(f"Model: {args.model} | itemow: {len(test)} | few-shot: {n_shots} | tryby: {args.mode}")

    def _opt(idx):
        return item["options"][idx] if 0 <= idx < len(item["options"]) else None

    per_item = []
    for k, item in enumerate(test, 1):
        messages = build_messages(item, fewshot, n_shots, seed=args.seed)
        rec = {"id": item["id"], "category": item["category"], "answer_idx": item["answer_idx"],
               "question": item["question"], "options": item["options"],
               "answer_text": item["options"][item["answer_idx"]]}
        if do_gen:
            g = score_generative(messages, item, args.model)
            rec["generative"] = {"pred_idx": g.pred_idx, "correct": g.pred_idx == item["answer_idx"],
                                 "pred_text": _opt(g.pred_idx), "parsed": g.parsed, "raw": g.raw}
        if do_lik:
            l = score_likelihood(messages, item, args.model)
            rec["likelihood"] = {"pred_idx": l.pred_idx, "correct": l.pred_idx == item["answer_idx"],
                                 "pred_text": _opt(l.pred_idx), "parsed": l.parsed, "raw": l.raw,
                                 "dist": l.dist, "margin": l.margin}
        per_item.append(rec)
        if k % 10 == 0:
            print(f"  ...{k}/{len(test)}", flush=True)

    result = {
        "model": args.model, "n_shots": n_shots, "seed": args.seed,
        "shuffle_options": not args.no_shuffle_options, "n_items": len(test),
        "modes": [m for m, on in (("generative", do_gen), ("likelihood", do_lik)) if on],
        "per_item": per_item,
    }
    Path(args.save).parent.mkdir(parents=True, exist_ok=True)
    Path(args.save).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # krotkie podsumowanie do konsoli
    for mode in result["modes"]:
        c = sum(1 for r in per_item if r[mode]["correct"])
        p = sum(1 for r in per_item if r[mode]["parsed"])
        print(f"  {mode:<11}: {c}/{len(test)} poprawnych ({100*c/len(test):.1f}%), sparsowano {p}/{len(test)}")
    print(f"\nWyniki: {args.save}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
