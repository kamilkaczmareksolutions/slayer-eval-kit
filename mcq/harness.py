"""
mcq.harness: rdzeń harnessu MCQ.

Dwa tryby scoringu (porównanie to wkład):
  - generative-letter: model generuje odpowiedź, parsujemy pierwszą literę A-D.
  - likelihood:        czytamy rozkład logprob nad literami A-D na pierwszym tokenie
                       odpowiedzi (top_logprobs z natywnego API Ollama) i bierzemy argmax.

Oba tryby używają TEGO SAMEGO promptu (te same tury chat), więc różnica w wyniku
pochodzi wyłącznie ze sposobu odczytu, i to jest porównywany efekt.

Determinizm: temperatura 0, stały seed (tasowanie opcji + kolejność few-shot).
Tylko agregaty per kategoria. Itemy benchmarku nie trafiają do treningu.
"""

from __future__ import annotations

import json
import random
import re
import urllib.request
from dataclasses import dataclass

LETTERS = ["A", "B", "C", "D", "E", "F"]
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"

SYSTEM = ("Jesteś systemem rozwiązującym pytania wielokrotnego wyboru. "
          "Odpowiadasz wyłącznie jedną wielką literą oznaczającą poprawną opcję "
          "(np. A). Nie dodajesz żadnego innego tekstu, kropek ani wyjaśnień.")


# ─── Wczytywanie i normalizacja MCQ ──────────────────────────────────────────

def _answer_to_idx(answer, n_options: int) -> int:
    if isinstance(answer, bool):
        raise ValueError("answer nie moze byc bool")
    if isinstance(answer, int):
        return answer
    s = str(answer).strip()
    if s.isdigit():
        return int(s)
    s_up = s.upper()
    if s_up in LETTERS[:n_options]:
        return LETTERS.index(s_up)
    raise ValueError(f"Nie rozumiem answer={answer!r}")


def load_mcq(path: str, shuffle_options: bool = True, seed: int = 0) -> list[dict]:
    """Czyta jsonl MCQ. Wymagane pola: question, options (lista), answer (idx|litera).
    Opcjonalne: id, category, context. Deterministycznie tasuje opcje (anty-bias pozycji)."""
    rng = random.Random(seed)
    items = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            opts = list(o["options"])
            ans = _answer_to_idx(o["answer"], len(opts))
            correct_text = opts[ans]
            if shuffle_options:
                rng.shuffle(opts)
                ans = opts.index(correct_text)
            items.append({
                "id": str(o.get("id", f"item_{i}")),
                "category": o.get("category", "default"),
                "question": o["question"],
                "options": opts,
                "answer_idx": ans,
                "context": o.get("context"),
            })
    return items


# ─── Budowa tur chat ─────────────────────────────────────────────────────────

def _user_content(item: dict) -> str:
    lines = []
    if item.get("context"):
        lines.append(f"Kontekst: {item['context']}")
    lines.append(f"Pytanie: {item['question']}")
    for j, opt in enumerate(item["options"]):
        lines.append(f"{LETTERS[j]}) {opt}")
    lines.append("Odpowiedź:")
    return "\n".join(lines)


def build_messages(item: dict, fewshot: list[dict], n_shots: int, seed: int = 0) -> list[dict]:
    rng = random.Random(seed)
    shots = list(fewshot)
    rng.shuffle(shots)
    shots = shots[:n_shots]
    messages = [{"role": "system", "content": SYSTEM}]
    for s in shots:
        messages.append({"role": "user", "content": _user_content(s)})
        messages.append({"role": "assistant", "content": LETTERS[s["answer_idx"]]})
    messages.append({"role": "user", "content": _user_content(item)})
    return messages


# ─── Adapter modelu (Ollama chat) ────────────────────────────────────────────

def _ollama_chat(messages: list[dict], model: str, num_predict: int,
                 top_logprobs: int = 0, timeout: int = 120) -> dict:
    payload = {
        "model": model.replace("ollama/", ""),
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0, "num_predict": num_predict, "seed": 0},
    }
    if top_logprobs:
        payload["logprobs"] = True
        payload["top_logprobs"] = top_logprobs
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_CHAT_URL, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ─── Tryby scoringu ──────────────────────────────────────────────────────────

@dataclass
class Pred:
    pred_idx: int
    raw: str
    parsed: bool
    dist: dict | None = None      # litera -> logprob (tylko tryb likelihood)
    margin: float | None = None   # logprob(top) - logprob(2nd) wsrod liter


def score_generative(messages: list[dict], item: dict, model: str) -> Pred:
    out = _ollama_chat(messages, model, num_predict=6)
    text = (out.get("message", {}).get("content") or "").strip()
    n = len(item["options"])
    m = re.search(r"[A-" + LETTERS[n - 1] + r"]", text.upper())
    if m:
        return Pred(LETTERS.index(m.group(0)), text, True)
    return Pred(-1, text, False)


def score_likelihood(messages: list[dict], item: dict, model: str, top_logprobs: int = 20) -> Pred:
    out = _ollama_chat(messages, model, num_predict=1, top_logprobs=top_logprobs)
    lp = out.get("logprobs") or []
    n = len(item["options"])
    valid = LETTERS[:n]
    raw_tok = (out.get("message", {}).get("content") or "").strip()
    dist: dict[str, float] = {}
    if lp:
        cands = lp[0].get("top_logprobs", []) or [lp[0]]
        for c in cands:
            tok = (c.get("token") or "").strip().upper()
            val = c.get("logprob", float("-inf"))
            if tok in valid and val > dist.get(tok, float("-inf")):
                dist[tok] = val
    if dist:
        ordered = sorted(dist.items(), key=lambda kv: kv[1], reverse=True)
        best_letter, best_lp = ordered[0]
        margin = best_lp - ordered[1][1] if len(ordered) > 1 else None
        return Pred(LETTERS.index(best_letter), f"argmax={best_letter} lp={best_lp:.3f}", True,
                    dist=dist, margin=margin)
    m = re.search(r"[A-" + LETTERS[n - 1] + r"]", raw_tok.upper())
    if m:
        return Pred(LETTERS.index(m.group(0)), raw_tok + " (fallback)", True)
    return Pred(-1, raw_tok, False)
