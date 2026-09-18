"""Global PIQA, re-run with an item-type-aware prompt.

Review pointed out two faults in the Global PIQA instruction used for the main
run: the domain slot was left empty where "Sri Lankan Culture" belonged, and the
wording asked the model to complete a text, which describes only part of the set.
The eleven checkpoints were therefore re-run with a prompt that names the domain
and matches the item's form. Everything else is the protocol of the main run:
zero-shot, greedy, 40 new tokens, each checkpoint's own chat template, answers
extracted by the same matcher with unparseable output scored wrong.

Item form is our own annotation, since the released data has no such field: it is
carried per item as `isQnA` in the result files. It is not a judgement call
either, being exactly whether the Sinhala stem ends in a question mark. This
script re-derives the split from the frozen evaluation set and checks it against
the annotation in every per-item file, so neither can drift from the other.

The statistics match stats_extrinsic.py, whose helpers are imported rather than
reimplemented: McNemar with a continuity correction, exact below 25 discordant
pairs, Holm across checkpoints, 10,000-sample paired bootstrap intervals, and a
one-sided Poisson-binomial screen for beating chance.

Writes out/piqa_rerun.json and ../tables/tab_piqa.tex.

Run from the repository root:  python paper/analysis/stats_piqa_rerun.py
"""
from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from scipy import stats

import common as C
from stats_extrinsic import above_chance, holm, paired_acc

RERUN_DIR = os.path.join(C.EXTR_DIR, "global_piqa_evaluation")
TAB = os.path.join(C.REPO, "paper", "tables")
ALPHA = 0.01          # competence screen, as in stats_extrinsic
TOP_SHARE_MAX = 90.0  # a checkpoint putting more than this on one option is degenerate

# directory under global_piqa_evaluation -> display name used everywhere else
DIRS = {
    "TinyLlama-1.1B-Chat-v1.0": "TinyLlama-1.1B-Chat",
    "LaMini-GPT-1.5B": "LaMini-GPT-1.5B",
    "stablelm-zephyr-3b": "StableLM-Zephyr-3B",
    "SmolLM3-3B": "SmolLM3-3B",
    "Qwen-3.5-4B": "Qwen3.5-4B",
    "zephyr-7b-beta": "Zephyr-7B-beta",
    "Qwen2-7B-Instruct": "Qwen2-7B-Instruct",
    "Llama-3.1-8B-Instruct": "Llama-3.1-8B-Instruct",
    "Hormoz-8B": "Hormoz-8B",
    "Qwen-3.5-9B": "Qwen3.5-9B",
    "Phi-4": "Phi-4-14B",
}


def eval_set() -> pd.DataFrame:
    """The frozen items, with the item form re-derived from the stem."""
    rows = []
    path = os.path.join(C.REPO, "data", "eval", "global_piqa.jsonl")
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        rows.append({
            "id": d["id"],
            "label": d["label"],
            "is_qna": d["unicode"]["text"].strip().endswith("?"),
            "culturally_specific": bool(d["strata"]["culturally_specific"]),
        })
    return pd.DataFrame(rows)


def load_one(directory: str) -> pd.DataFrame:
    hits = glob.glob(os.path.join(RERUN_DIR, directory, "*_global_piqa.csv"))
    hits = [h for h in hits if "summary" not in os.path.basename(h)]
    if len(hits) != 1:
        raise FileNotFoundError(f"{directory}: {hits}")
    d = pd.read_csv(hits[0], encoding="utf-8-sig")
    d.columns = [c.lstrip("\ufeff") for c in d.columns]
    return d[d["id"].notna()].reset_index(drop=True)


def load_all(items: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Per-checkpoint records, merged onto the frozen items and integrity-checked."""
    out = {}
    for directory, name in DIRS.items():
        d = load_one(directory)
        if len(d) != len(items):
            raise ValueError(f"{name}: {len(d)} rows, expected {len(items)}")
        d = d.merge(items, on="id", how="left", validate="one_to_one")
        if d.label.isna().any():
            raise ValueError(f"{name}: ids not in the frozen evaluation set")
        recorded = d["is_qna_x"].astype(str).str.lower() == "true"
        if not (recorded == d["is_qna_y"]).all():
            raise ValueError(f"{name}: recorded isQnA disagrees with the stem rule")
        d["is_qna"] = d["is_qna_y"]
        if not (d.gold_label == d.label).all():
            raise ValueError(f"{name}: gold labels disagree with the frozen set")
        out[name] = d
    return out


def invalid(d: pd.DataFrame, script: str) -> np.ndarray:
    v = d[f"{script}_pred_label"].astype(str)
    return v.isin(["INVALID", "nan", "None", ""]).to_numpy()


def top_share(d: pd.DataFrame, script: str) -> float:
    v = d[f"{script}_pred_label"].astype(str)
    v = v[~v.isin(["INVALID", "nan", "None", ""])]
    return float(v.value_counts(normalize=True).max() * 100) if len(v) else float("nan")


def format_block(frames: dict, items: pd.DataFrame, mask, label: str) -> dict:
    """Pooled paired comparison over one subset of items, across all checkpoints."""
    u = np.concatenate([f.loc[mask.values, "unicode_correct"].to_numpy() for f in frames.values()])
    r = np.concatenate([f.loc[mask.values, "romanized_correct"].to_numpy() for f in frames.values()])
    res = paired_acc(u, r)
    res["label"] = label
    res["n_items"] = int(mask.sum())
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()}


def main():
    C.ensure_dirs()
    items = eval_set()
    frames = load_all(items)

    n_qna = int(items.is_qna.sum())
    out = {
        "n_items": int(len(items)),
        "n_checkpoints": len(frames),
        "chance": 50.0,
        "item_forms": {"question_answer": n_qna, "paragraph_completion": int(len(items) - n_qna)},
        "item_form_rule": "the Sinhala stem ends in a question mark",
        "prompt": {
            "question_answer": ("This is a multiple-choice question related to the Sri Lankan "
                                "Culture. Choose the correct or most appropriate answer from "
                                "answers 1/2. ..."),
            "paragraph_completion": ("This is related to the Sri Lankan Culture. Out of the given "
                                     "2 answers, which one is the best option to complete the "
                                     "given text? ..."),
        },
        "n_culturally_specific": int(items.culturally_specific.sum()),
    }

    # ------------------------------------------------------------ per model --
    rows = []
    chance_vec = np.full(len(items), 0.5)
    for name, d in frames.items():
        r = paired_acc(d.unicode_correct, d.romanized_correct)
        r["model"] = name
        r["params"] = C.EXTRINSIC_MODELS[name][2]
        for tag, script in (("u", "unicode"), ("r", "romanized")):
            r[f"{tag}_invalid"] = float(invalid(d, script).mean() * 100)
            r[f"{tag}_top_share"] = top_share(d, script)
            ac = above_chance(d[f"{script}_correct"].to_numpy(), chance_vec)
            r[f"{tag}_z"], r[f"{tag}_p_above"] = ac["z"], ac["p"]
            r[f"{tag}_tok"] = int(d[f"{script}_n_input_tokens"].sum())
        r["tok_ratio"] = r["r_tok"] / r["u_tok"]
        # a checkpoint that cannot produce a parseable answer in the Sinhala
        # script has no usable native score to compare against
        r["parseable"] = r["u_invalid"] < 50.0
        r["competent"] = bool(r["u_p_above"] < ALPHA)
        r["degenerate_u"] = bool(r["u_top_share"] > TOP_SHARE_MAX)
        rows.append(r)

    T = pd.DataFrame(rows).sort_values("params").reset_index(drop=True)
    T["p_holm"] = holm(T.p.tolist())

    out["per_model"] = T.drop(columns=["params"]).round(4).to_dict("records")
    out["n_competent"] = int((T.competent & ~T.degenerate_u).sum())
    out["competent_models"] = T[T.competent & ~T.degenerate_u].model.tolist()
    out["n_sig_holm"] = int((T.p_holm < 0.05).sum())
    out["max_abs_gap"] = float(T.gap.abs().max())
    out["median_discordant_pairs"] = float(T.n_disc.median())
    out["median_discordant_rate"] = float(T.n_disc.median() / len(items))

    par = T[T.parseable]
    out["n_parseable"] = int(len(par))
    out["parseable_summary"] = {
        "u_range": [float(par.u_acc.min()), float(par.u_acc.max())],
        "r_range": [float(par.r_acc.min()), float(par.r_acc.max())],
        "n_drop": int((par.gap > 0).sum()),
        "n_rise": int((par.gap < 0).sum()),
        "n_tie": int((par.gap == 0).sum()),
        "gap_range": [float(par.gap.min()), float(par.gap.max())],
    }
    # Sign test over checkpoints that moved at all, as in the main run.
    moved = par[par.gap != 0]
    n_pos = int((moved.gap > 0).sum())
    out["sign_test"] = {
        "n_moved": int(len(moved)), "n_drop": n_pos,
        "p": float(stats.binomtest(n_pos, len(moved), 0.5).pvalue) if len(moved) else float("nan"),
    }

    # --------------------------------------------------------------- pooled --
    allmask = pd.Series(True, index=items.index)
    out["pooled_parseable"] = format_block(
        {k: v for k, v in frames.items() if k in set(par.model)}, items, allmask, "all items")
    par_frames = {k: v for k, v in frames.items() if k in set(par.model)}
    out["by_item_form"] = [
        format_block(par_frames, items, items.is_qna, "question-answer"),
        format_block(par_frames, items, ~items.is_qna, "paragraph completion"),
    ]
    out["by_cultural"] = [
        format_block(par_frames, items, items.culturally_specific, "culturally specific"),
        format_block(par_frames, items, ~items.culturally_specific, "not culturally specific"),
    ]

    # ------------------------------------------- against the earlier prompt --
    old = pd.read_csv(os.path.join(C.OUT_DIR, "extrinsic_main.csv"))
    old = old[old.dataset == "global_piqa"].set_index("model")
    comp = []
    for r in T.itertuples():
        if r.model in old.index:
            o = old.loc[r.model]
            comp.append({"model": r.model,
                         "old_u": float(o.u_acc), "new_u": float(r.u_acc),
                         "old_r": float(o.r_acc), "new_r": float(r.r_acc),
                         "old_gap": float(o.gap), "new_gap": float(r.gap)})
    out["vs_earlier_prompt"] = comp
    out["vs_earlier_prompt_summary"] = {
        "mean_abs_u_change": float(np.mean([abs(c["new_u"] - c["old_u"]) for c in comp])),
        "n_u_improved": int(sum(c["new_u"] > c["old_u"] for c in comp)),
        "old_n_drop": int(sum(c["old_gap"] > 0 for c in comp if c["model"] in set(par.model))),
        "new_n_drop": int(sum(c["new_gap"] > 0 for c in comp if c["model"] in set(par.model))),
    }

    path = os.path.join(C.OUT_DIR, "piqa_rerun.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print("wrote", path)

    write_table(T)
    report(out, T)


def fp(p):
    return r"$<$\,.0001" if p < 1e-4 else f"{p:.4f}".lstrip("0")


def write_table(T: pd.DataFrame):
    nb = lambda s: s.replace("-", "\\nobreakdash-")  # noqa: E731
    lines = []
    for r in T.itertuples():
        lines.append(f"{nb(r.model)} & {r.u_acc:.0f} & {r.r_acc:.0f} & {r.gap:+.0f} "
                     f"& {r.b}/{r.c} & {fp(r.p_holm)} \\\\")
    body = "\n".join(lines)
    p = os.path.join(TAB, "tab_piqa.tex")
    with open(p, "w", encoding="utf-8") as f:
        f.write("% Generated by paper/analysis/stats_piqa_rerun.py. Do not edit by hand.\n")
        f.write(body + "\n")
    print("wrote", p)


def report(out, T):
    print(f"\nGlobal PIQA re-run: {out['n_items']} items "
          f"({out['item_forms']['question_answer']} question-answer, "
          f"{out['item_forms']['paragraph_completion']} completion), "
          f"{out['n_checkpoints']} checkpoints")
    print(T[["model", "u_acc", "r_acc", "gap", "b", "c", "n_disc", "p_holm",
             "u_invalid", "r_invalid", "u_p_above", "parseable"]]
          .round(3).to_string(index=False))
    s = out["parseable_summary"]
    print(f"\nparseable: {out['n_parseable']}  drop {s['n_drop']}  rise {s['n_rise']}  "
          f"tie {s['n_tie']}  gap range {s['gap_range']}")
    print(f"sign test over the {out['sign_test']['n_moved']} that moved: "
          f"{out['sign_test']['n_drop']} drop, p = {out['sign_test']['p']:.3f}")
    print(f"competent (above chance at p<{ALPHA}): {out['n_competent']} "
          f"{out['competent_models']}")
    print(f"significant after Holm: {out['n_sig_holm']}")
    print(f"median discordant pairs: {out['median_discordant_pairs']:.0f}")
    pp = out["pooled_parseable"]
    print(f"\npooled over parseable: u {pp['u_acc']:.2f} r {pp['r_acc']:.2f} "
          f"gap {pp['gap']:+.2f} [{pp['gap_lo']:.2f}, {pp['gap_hi']:.2f}] p = {pp['p']:.3f}")
    for blk in out["by_item_form"] + out["by_cultural"]:
        print(f"  {blk['label']:26s} n={blk['n_items']:3d} u {blk['u_acc']:6.2f} "
              f"r {blk['r_acc']:6.2f} gap {blk['gap']:+6.2f} p = {blk['p']:.3f}")
    v = out["vs_earlier_prompt_summary"]
    print(f"\nvs the earlier prompt: mean |change| in Sinhala-script accuracy "
          f"{v['mean_abs_u_change']:.1f} points, improved for {v['n_u_improved']} of "
          f"{len(out['vs_earlier_prompt'])}; checkpoints dropping under romanization "
          f"{v['old_n_drop']} -> {v['new_n_drop']}")


if __name__ == "__main__":
    main()
