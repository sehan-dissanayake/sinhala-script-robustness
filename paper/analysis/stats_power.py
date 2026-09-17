"""What a paired script comparison can and cannot resolve at each item count.

The three datasets differ by two orders of magnitude in size, so a null result
on the smallest one needs a number attached to it rather than an adjective. This
computes the smallest paired accuracy difference McNemar's test would detect,
exactly, at each dataset's own item count and observed discordant rate.

The computation is exact rather than simulated, so it is reproducible with no
seed. Every item independently falls into one of three cells: Sinhala right and
Romanized wrong with probability pb, the reverse with probability pc, or
concordant. Power is the multinomial probability, summed over all (b, c), that
the continuity-corrected test rejects.

Writes out/power.json.

Run from the repository root:  python paper/analysis/stats_power.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from scipy import stats

import common as C

ALPHA = 0.05
TARGET_POWER = 0.80


def rejects(b: int, c: int, alpha: float = ALPHA) -> bool:
    """McNemar with Edwards' continuity correction, as used in stats_extrinsic."""
    n = b + c
    if n == 0:
        return False
    chi2 = (abs(b - c) - 1) ** 2 / n
    return bool(stats.chi2.sf(chi2, 1) < alpha)


def power(n_items: int, p_disc: float, delta: float, alpha: float = ALPHA) -> float:
    """Exact power against a true paired difference of `delta` (proportion).

    delta = pb - pc and p_disc = pb + pc, which fixes both cell probabilities.

    Computed by conditioning on the number of discordant pairs m. That is what
    makes it exact and still cheap: m is Binomial(n, p_disc), b given m is
    Binomial(m, pb / p_disc), and the continuity-corrected test rejects exactly
    when |2b - m| > 1 + sqrt(chi2_crit * m), which is a closed form rather than
    a test call per cell.
    """
    pb = (p_disc + delta) / 2
    pc = (p_disc - delta) / 2
    if pb < 0 or pc < 0 or pb + pc > 1:
        return float("nan")
    if p_disc <= 0:
        return 0.0

    crit = stats.chi2.ppf(1 - alpha, 1)
    q = pb / p_disc

    m = np.arange(0, n_items + 1)
    p_m = stats.binom.pmf(m, n_items, p_disc)
    keep = p_m > 1e-15          # tails that cannot move the answer
    m, p_m = m[keep], p_m[keep]

    t = 1.0 + np.sqrt(crit * m)
    hi = np.floor((m + t) / 2)
    lo = np.ceil((m - t) / 2) - 1
    p_reject = stats.binom.sf(hi, m, q) + stats.binom.cdf(lo, m, q)
    p_reject = np.where(m > 0, p_reject, 0.0)
    return float(np.sum(p_m * p_reject))


def mde(n_items: int, p_disc: float, hi: float = 0.9) -> float:
    """Smallest detectable difference at TARGET_POWER, in proportion units."""
    lo = 0.0
    hi = min(hi, p_disc)
    if power(n_items, p_disc, hi) < TARGET_POWER:
        return float("nan")
    for _ in range(40):
        mid = (lo + hi) / 2
        if power(n_items, p_disc, mid) < TARGET_POWER:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def n_for(delta: float, p_disc: float, cap: int = 40000) -> int:
    """Items needed to reach TARGET_POWER against a given true difference."""
    n = 50
    while n < cap:
        if power(n, p_disc, delta) >= TARGET_POWER:
            lo, hi = n // 2, n
            while lo + 1 < hi:
                mid = (lo + hi) // 2
                if power(mid, p_disc, delta) >= TARGET_POWER:
                    hi = mid
                else:
                    lo = mid
            return hi
        n = int(n * 1.5)
    return -1


def observed():
    """Per-checkpoint discordant rates actually seen, per dataset."""
    ne = json.load(open(os.path.join(C.OUT_DIR, "extrinsic_numbers.json")))
    ex = pd.read_csv(os.path.join(C.OUT_DIR, "extrinsic_main.csv"))
    out = {}
    for ds in ("global_piqa", "sinhala_mmlu"):
        d = ex[ex.dataset == ds]
        n = ne["n_items"][ds]
        disc = (d["n_disc"] / n).dropna()
        out[ds] = {
            "n_items": int(n),
            "n_checkpoints": int(len(disc)),
            "median_discordant_pairs": float(d["n_disc"].median()),
            "p_disc_median": float(disc.median()),
        }
    return out


def main():
    obs = observed()
    piqa = obs["global_piqa"]
    mmlu = obs["sinhala_mmlu"]

    piqa_mde = mde(piqa["n_items"], piqa["p_disc_median"])
    mmlu_mde = mde(mmlu["n_items"], mmlu["p_disc_median"])

    curve = {
        f"{100 * d:.0f}": power(piqa["n_items"], piqa["p_disc_median"], d)
        for d in (0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 0.175, 0.20)
    }

    ne = json.load(open(os.path.join(C.OUT_DIR, "extrinsic_numbers.json")))
    observed_piqa_gap = ne["piqa_pooled_competent"]["gap"] / 100
    largest_mmlu_gap = max(
        abs(v) for v in ne["sinhala_mmlu_summary"]["competent_gaps"].values()
    ) / 100

    out = {
        "alpha": ALPHA,
        "target_power": TARGET_POWER,
        "observed": obs,
        "global_piqa": {
            "mde_points": 100 * piqa_mde,
            "power_curve_by_true_gap_points": curve,
            "power_at_observed_pooled_gap": power(
                piqa["n_items"], piqa["p_disc_median"], observed_piqa_gap),
            "power_at_largest_mmlu_gap": power(
                piqa["n_items"], piqa["p_disc_median"], largest_mmlu_gap),
            "items_needed_for_observed_pooled_gap": n_for(
                observed_piqa_gap, piqa["p_disc_median"]),
        },
        "sinhala_mmlu": {"mde_points": 100 * mmlu_mde},
        "observed_pooled_piqa_gap_points": 100 * observed_piqa_gap,
        "largest_mmlu_gap_points": 100 * largest_mmlu_gap,
    }

    C.ensure_dirs()
    path = os.path.join(C.OUT_DIR, "power.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("wrote", path)

    print(f"\nGlobal PIQA: {piqa['n_items']} items, median discordant rate "
          f"{100 * piqa['p_disc_median']:.0f}%")
    print(f"  smallest detectable gap at {TARGET_POWER:.0%} power: "
          f"{100 * piqa_mde:.1f} points")
    for k, v in curve.items():
        print(f"    true gap {k:>5s} pts -> power {v:.3f}")
    print(f"  power at the largest gap seen anywhere in the paper "
          f"({100 * largest_mmlu_gap:.1f} pts): "
          f"{out['global_piqa']['power_at_largest_mmlu_gap']:.3f}")
    print(f"  items needed for the {100 * observed_piqa_gap:.1f} pt pooled gap: "
          f"{out['global_piqa']['items_needed_for_observed_pooled_gap']:,}")
    print(f"\nSinhalaMMLU: {mmlu['n_items']:,} items, median discordant rate "
          f"{100 * mmlu['p_disc_median']:.0f}%")
    print(f"  smallest detectable gap at {TARGET_POWER:.0%} power: "
          f"{100 * mmlu_mde:.2f} points")


if __name__ == "__main__":
    main()
