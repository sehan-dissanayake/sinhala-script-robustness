"""Measure what our transliterator costs, by scoring the same 500 sentences three ways.

WHY THIS EXISTS
---------------
The Romanized side of the downstream evaluation is produced by our
transliterator rather than typed by people. That is the main external-validity
limit on the downstream results, and a reviewer will ask how large it is.

The intrinsic parallel corpus lets us answer that directly, because it already
carries two sides for the same 500 sentences: the native script as published,
and a Romanized side that native speakers typed. This script adds a third
condition, our transliterator's output for the same native sentences, and scores
all three with exactly the protocol the main intrinsic evaluation used.

Two things come out of it:

  1. A reproduction check. The `unicode` and `human` columns should land on the
     numbers already recorded in results/intrinsic_evaluation/. The script
     prints the percentage deviation per checkpoint so any drift is visible.

  2. The number we actually need: `ours` minus `human` bits per byte, on
     identical content. Positive means our transliteration is harder for the
     model than authentic typing, so the downstream gaps we report are closer to
     upper bounds. Negative means the opposite.

HOW TO RUN
----------
On a GPU box, from the repository root:

    # everything, all 31 checkpoints, all three conditions (the full picture)
    python paper/analysis/run_synthetic_vs_human.py --all

    # only the new condition, roughly three times faster, if you trust the
    # recorded native and human columns and only want ours-minus-human
    python paper/analysis/run_synthetic_vs_human.py --all --conditions ours

    # a subset, by registry key
    python paper/analysis/run_synthetic_vs_human.py --models llama-3.1-8b phi-4

Notes:
  * Defaults match the original run: float16, device_map="auto". Pass
    --dtype float32 for a CPU run.
  * Gated checkpoints (Llama, Gemma, Mistral) need a token. Put HF_TOKEN in a
    .env file at the repository root, or export it. Checkpoints that fail to
    load are reported and skipped rather than aborting the run.
  * Qwen3.5 needs a recent transformers. If it errors with "does not recognize
    this architecture", upgrade transformers and rerun just those keys.
  * Resumable at sentence granularity. Interrupt at any point and rerun the
    same command. Finished checkpoints are skipped unless --force is passed.

WHAT TO SEND BACK
-----------------
    paper/analysis/out/synthetic_vs_human/*.csv
    paper/analysis/out/synthetic_vs_human.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "src", "transliteration"))

import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

import common as CM
from phonetic import transliterate

LN2 = math.log(2)
OUT = os.path.join(CM.OUT_DIR, "synthetic_vs_human")
PARALLEL = os.path.join(CM.REPO, "data", "raw", "intrinsic_evaluation_datasets",
                        "diverse_sentences.csv")

# registry key -> (display name used everywhere else, Hugging Face identifier)
# The display names match paper/analysis/common.py, so the reproduction check
# can find the recorded run for each checkpoint.
MODELS = {
    "opt-350m":               ("OPT-350M", "facebook/opt-350m"),
    "pythia-410m":            ("Pythia-410M", "EleutherAI/pythia-410m"),
    "bloom-560m":             ("BLOOM-560M", "bigscience/bloom-560m"),
    "bloom-1b1":              ("BLOOM-1B1", "bigscience/bloom-1b1"),
    "tinyllama-1.1b-chat":    ("TinyLlama-1.1B-Chat", "TinyLlama/TinyLlama-1.1B-Chat-v1.0"),
    "llama-3.2-1b":           ("Llama-3.2-1B", "meta-llama/Llama-3.2-1B"),
    "cerebras-gpt-1.3b":      ("Cerebras-GPT-1.3B", "cerebras/Cerebras-GPT-1.3B"),
    "opt-1.3b":               ("OPT-1.3B", "facebook/opt-1.3b"),
    "lamini-gpt-1.5b":        ("LaMini-GPT-1.5B", "MBZUAI/LaMini-GPT-1.5B"),
    "qwen1.5-1.8b":           ("Qwen1.5-1.8B", "Qwen/Qwen1.5-1.8B"),
    "opt-2.7b":               ("OPT-2.7B", "facebook/opt-2.7b"),
    "stablelm-zephyr-3b":     ("StableLM-Zephyr-3B", "stabilityai/stablelm-zephyr-3b"),
    "bloom-3b":               ("BLOOM-3B", "bigscience/bloom-3b"),
    "smollm3-3b":             ("SmolLM3-3B", "HuggingFaceTB/SmolLM3-3B"),
    "llama-3.2-3b":           ("Llama-3.2-3B", "meta-llama/Llama-3.2-3B"),
    "qwen3.5-4b-base":        ("Qwen3.5-4B-Base", "Qwen/Qwen3.5-4B-Base"),
    "qwen3.5-4b":             ("Qwen3.5-4B", "Qwen/Qwen3.5-4B"),
    "mistral-7b-v0.3":        ("Mistral-7B-v0.3", "mistralai/Mistral-7B-v0.3"),
    "zephyr-7b-beta":         ("Zephyr-7B-beta", "HuggingFaceH4/zephyr-7b-beta"),
    "qwen2-7b":               ("Qwen2-7B", "Qwen/Qwen2-7B"),
    "qwen2-7b-instruct":      ("Qwen2-7B-Instruct", "Qwen/Qwen2-7B-Instruct"),
    "llama-3.1-8b":           ("Llama-3.1-8B", "meta-llama/Meta-Llama-3.1-8B"),
    "llama-3.1-8b-instruct":  ("Llama-3.1-8B-Instruct", "meta-llama/Llama-3.1-8B-Instruct"),
    "hormoz-8b":              ("Hormoz-8B", "mann-e/Hormoz-8B"),
    "minitron-8b-base":       ("Minitron-8B-Base", "nvidia/Minitron-8B-Base"),
    "gemma-7b":               ("Gemma-7B", "google/gemma-7b"),
    "qwen3.5-9b-base":        ("Qwen3.5-9B-Base", "Qwen/Qwen3.5-9B-Base"),
    "qwen3.5-9b":             ("Qwen3.5-9B", "Qwen/Qwen3.5-9B"),
    "gemma-2-9b":             ("Gemma-2-9B", "google/gemma-2-9b"),
    "mistral-nemo-base-2407": ("Mistral-Nemo-Base-2407", "mistralai/Mistral-Nemo-Base-2407"),
    "phi-4":                  ("Phi-4-14B", "microsoft/phi-4"),
}

CONDITIONS = ("unicode", "human", "ours")


def hf_token() -> str | None:
    tok = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if tok:
        return tok
    env = os.path.join(CM.REPO, ".env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            if line.strip().startswith("HF_TOKEN"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def lengths(text: str) -> tuple[int, int, int]:
    """Characters, UTF-8 bytes and whitespace words, the three denominators."""
    return len(text), len(text.encode("utf-8")), len(text.split())


def score(model, tok, text: str) -> dict:
    """Total NLL in nats plus the raw counts needed to pool over the corpus.

    Identical to the protocol in the intrinsic notebooks: tokenize the raw
    string with the checkpoint's own tokenizer, take the mean cross-entropy the
    model reports, and multiply back out by the number of predicted positions.
    """
    chars, nbytes, words = lengths(text)
    enc = tok(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model(**enc, labels=enc["input_ids"])
    n_scored = enc["input_ids"].shape[1] - 1
    return {"nll": out.loss.item() * n_scored, "n_scored": n_scored,
            "n_chars": chars, "n_bytes": nbytes, "n_words": words}


def pooled(rows: list[dict]) -> dict:
    """Corpus-pooled metrics. Never average per-sentence ratios."""
    nll = sum(r["nll"] for r in rows)
    return {"ppl": math.exp(nll / sum(r["n_scored"] for r in rows)),
            "bpb": nll / (sum(r["n_bytes"] for r in rows) * LN2),
            "bpc": nll / (sum(r["n_chars"] for r in rows) * LN2),
            "bpw": nll / (sum(r["n_words"] for r in rows) * LN2),
            "nll": nll, "n": len(rows)}


def build_summary(conds_run: tuple[str, ...]) -> dict:
    summary = {}
    for key, (name, hf_id) in MODELS.items():
        p = os.path.join(OUT, f"{key}.csv")
        if not os.path.exists(p):
            continue
        t = pd.read_csv(p)
        have = [c for c in CONDITIONS if f"{c}_nll" in t.columns]
        s = {"hf_id": hf_id, "conditions_scored": have, "n_sentences": int(len(t))}
        for cond in have:
            rows = t[[c for c in t.columns if c.startswith(cond + "_")]].rename(
                columns=lambda c: c[len(cond) + 1:]).to_dict("records")
            s[cond] = pooled(rows)

        # compare the reproducible columns against the recorded GPU run
        try:
            dirkey = next(k for k, v in CM.INTRINSIC_MODELS.items() if v[0] == name)
            div, _ = CM.load_intrinsic_items(dirkey)
            div = div.rename(columns={c: c.lstrip("\ufeff") for c in div.columns})
            ref, dev = {}, {}
            for cond, pre in (("unicode", "unicode"), ("human", "romanized")):
                nll = div[f"{pre}_nll"].sum()
                ref[cond] = {"ppl": math.exp(nll / div[f"{pre}_nscored"].sum()),
                             "bpb": nll / (div[f"{pre}_nbytes"].sum() * LN2),
                             "bpw": nll / (div[f"{pre}_nwords"].sum() * LN2)}
                if cond in s:
                    dev[cond] = {m: abs(s[cond][m] - ref[cond][m]) / ref[cond][m] * 100
                                 for m in ("ppl", "bpb", "bpw")}
            s["recorded_gpu_run"] = ref
            s["reproduction_pct_dev"] = dev
        except Exception as e:                                  # pragma: no cover
            s["recorded_gpu_run"] = f"unavailable: {e}"

        # the quantity of interest, on identical content
        base = s.get("human") or (s.get("recorded_gpu_run") or {}).get("human")
        if "ours" in s and base:
            s["ours_minus_human"] = {m: s["ours"][m] - base[m]
                                     for m in ("bpb", "bpw") if m in base}
            s["ours_over_human_ppl"] = s["ours"]["ppl"] / base["ppl"]
        summary[name] = s

    with open(os.path.join(CM.OUT_DIR, "synthetic_vs_human.json"), "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("HOW TO RUN")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="*", default=[], metavar="KEY",
                    help=f"registry keys, any of: {', '.join(MODELS)}")
    ap.add_argument("--all", action="store_true", help="every checkpoint in the registry")
    ap.add_argument("--conditions", nargs="*", default=list(CONDITIONS),
                    choices=list(CONDITIONS),
                    help="which conditions to score (default: all three)")
    ap.add_argument("--dtype", default="float16", choices=["float16", "bfloat16", "float32"])
    ap.add_argument("--device-map", default="auto")
    ap.add_argument("--force", action="store_true", help="rescore finished checkpoints")
    ap.add_argument("--limit", type=int, default=0, help="debug: first N sentences only")
    ap.add_argument("--list", action="store_true", help="print the registry and exit")
    args = ap.parse_args()

    if args.list:
        for k, (n, h) in MODELS.items():
            print(f"{k:<24} {n:<24} {h}")
        return
    keys = list(MODELS) if args.all else args.models
    if not keys:
        ap.error("pass --all or --models KEY [KEY ...], or --list to see the registry")
    unknown = [k for k in keys if k not in MODELS]
    if unknown:
        ap.error(f"unknown registry keys: {unknown}")

    os.makedirs(OUT, exist_ok=True)
    token = hf_token()
    print(f"HF token: {'found' if token else 'not found, gated checkpoints will be skipped'}")

    d = pd.read_csv(PARALLEL, encoding="utf-8-sig").dropna()
    d.columns = [c.lstrip("\ufeff") for c in d.columns]
    if args.limit:
        d = d.head(args.limit)
    texts = {
        "unicode": [str(s) for s in d.sinhala_unicode],
        "human": [str(s) for s in d.sinhala_romanized],
        "ours": [transliterate(str(s)) for s in d.sinhala_unicode],
    }
    conds = tuple(c for c in CONDITIONS if c in args.conditions)
    print(f"{len(d)} sentences x {len(conds)} conditions {conds} x {len(keys)} checkpoints")

    failures = []
    for key in keys:
        name, hf_id = MODELS[key]
        dest = os.path.join(OUT, f"{key}.csv")
        if os.path.exists(dest) and not args.force:
            print(f"[skip] {name} already scored, pass --force to redo", flush=True)
            continue
        t0 = time.time()
        print(f"[load] {name} ({hf_id})", flush=True)
        try:
            tok = AutoTokenizer.from_pretrained(hf_id, token=token)
            model = AutoModelForCausalLM.from_pretrained(
                hf_id, dtype=getattr(torch, args.dtype), token=token,
                device_map=args.device_map, low_cpu_mem_usage=True)
            model.eval()
        except Exception as e:
            print(f"[fail] {name}: {type(e).__name__}: {e}", flush=True)
            failures.append((name, hf_id, f"{type(e).__name__}: {e}"))
            continue

        part = dest + ".partial.jsonl"
        done = set()
        if os.path.exists(part) and not args.force:
            with open(part) as fh:
                for line in fh:
                    try:
                        done.add(json.loads(line)["item_index"])
                    except Exception:
                        pass
            print(f"    resuming, {len(done)} sentences already scored", flush=True)
        elif args.force and os.path.exists(part):
            os.remove(part)

        with open(part, "a") as fh:
            for i in range(len(d)):
                if i in done:
                    continue
                row = {"item_index": i}
                for cond in conds:
                    for k2, v2 in score(model, tok, texts[cond][i]).items():
                        row[f"{cond}_{k2}"] = v2
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                if (i + 1) % 100 == 0:
                    print(f"    {i + 1}/{len(d)}  {time.time() - t0:.0f}s", flush=True)

        recs = list({json.loads(l)["item_index"]: json.loads(l)
                     for l in open(part)}.values())
        pd.DataFrame(sorted(recs, key=lambda r: r["item_index"])).to_csv(dest, index=False)
        os.remove(part)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(f"[done] {name} in {time.time() - t0:.0f}s -> {dest}", flush=True)

    summary = build_summary(conds)
    print(f"\n{'checkpoint':<24}{'uni':>8}{'human':>8}{'ours':>8}{'ours-human':>12}"
          f"{'repro dev %':>13}")
    for name, s in summary.items():
        if "ours_minus_human" not in s:
            continue
        u = s.get("unicode", {}).get("bpb", float("nan"))
        h = s.get("human", {}).get("bpb",
                                   s.get("recorded_gpu_run", {}).get("human", {}).get("bpb", float("nan")))
        dev = s.get("reproduction_pct_dev", {})
        worst = max([v["bpb"] for v in dev.values()] or [float("nan")])
        print(f"{name:<24}{u:>8.3f}{h:>8.3f}{s['ours']['bpb']:>8.3f}"
              f"{s['ours_minus_human']['bpb']:>+12.3f}{worst:>13.3f}")
    if failures:
        print("\nfailed to load:")
        for n, h, e in failures:
            print(f"  {n} ({h}): {e}")
    print("\nwrote paper/analysis/out/synthetic_vs_human.json")


if __name__ == "__main__":
    main()
