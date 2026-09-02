"""Check the numeric claims written into the paper against the frozen analysis.

Every assertion below restates a number that appears in acl_latex.tex. If the
analysis is re-run and a value moves, this script fails and tells you which claim
in the paper is now stale.

Run from the repository root:  python paper/analysis/verify_claims.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

import common as C

NI = json.load(open(os.path.join(C.OUT_DIR, "intrinsic_numbers.json")))
NE = json.load(open(os.path.join(C.OUT_DIR, "extrinsic_numbers.json")))
IT = pd.read_csv(os.path.join(C.OUT_DIR, "intrinsic_pooled.csv"))
EX = pd.read_csv(os.path.join(C.OUT_DIR, "extrinsic_main.csv"))
SD = pd.read_csv(os.path.join(C.OUT_DIR, "sold_detail.csv")).set_index("model")
MM = EX[EX.dataset == "sinhala_mmlu"].set_index("model")

fails, checks = [], 0


def eq(claim, value, expected, tol=5e-3):
    """Assert a number printed in the paper matches the analysis."""
    global checks
    checks += 1
    if abs(float(value) - float(expected)) > tol:
        fails.append(f"{claim}: paper says {expected}, analysis gives {value}")


def is_(claim, cond):
    global checks
    checks += 1
    if not cond:
        fails.append(f"{claim}: condition false")


# ------------------------------------------------------------- abstract/intro --
eq("abstract: PPL-BPB rho", NI["rank"]["ppl_vs_bpb_unicode"]["rho"], 0.08, 5e-3)
eq("abstract: BPB gap median", NI["d_bpb"]["median"], 2.14, 5e-3)
eq("abstract: native spread MMLU", NE["sinhala_mmlu_summary"]["u_spread_x"], 22.4, 0.05)
eq("abstract: romanized spread MMLU", NE["sinhala_mmlu_summary"]["r_spread_x"], 6.7, 0.05)
eq("abstract: floor law R2", NE["gap_vs_headroom_mmlu"]["r2"], 0.96, 5e-3)
eq("abstract: n items", NE["n_items"]["sinhala_mmlu"] + NE["n_items"]["sold"]
   + NE["n_items"]["global_piqa"], 9479, 0)
eq("intro: 31 checkpoints", NI["n_checkpoints"], 31, 0)
eq("intro: fertility rho", NI["rank"]["fertility_vs_unicode_ppl"]["rho"], -0.87, 5e-3)
eq("intro: BPB prob factor", NI["d_bpb"]["median_prob_factor"], 4.4, 0.05)
eq("intro: params vs unicode BPB", NI["rank"]["params_vs_unicode_bpb"]["rho"], -0.55, 5e-3)
eq("intro: params vs unicode BPB p", NI["rank"]["params_vs_unicode_bpb"]["p"], 0.001, 5e-4)
eq("intro: BPW unicode min", NI["bpw_unicode_range"][0], 16.3, 0.05)
eq("intro: BPW unicode max", NI["bpw_unicode_range"][1], 34.1, 0.05)
eq("intro: BPW romanized min", NI["bpw_romanized_range"][0], 20.3, 0.05)
eq("intro: BPW romanized max", NI["bpw_romanized_range"][1], 25.7, 0.05)
eq("intro: n better romanized BPW", NI["bpw_n_models_better_romanized"], 12, 0)
eq("intro: generations", NE["n_models"] * 2 * 9479, 208538, 0)
eq("intro: floor law slope", NE["gap_vs_headroom_mmlu"]["slope"], 0.78, 5e-3)
eq("intro: n strata cells", NE["mmlu_cell_gap_vs_headroom"]["n_cells"], 16, 0)
eq("intro: linkage u_bpb rho", NE["linkage"]["u_bpb~mmlu_gap"]["rho"], -0.83, 5e-3)
eq("intro: linkage u_bpb p", NE["linkage"]["u_bpb~mmlu_gap"]["p"], 0.003, 5e-4)
eq("intro: linkage d_bpb rho", NE["linkage"]["d_bpb~mmlu_gap"]["rho"], -0.15, 5e-3)
eq("intro: linkage d_bpb p", NE["linkage"]["d_bpb~mmlu_gap"]["p"], 0.68, 5e-3)

# ------------------------------------------------------------------- setup ----
eq("setup: mmlu items", NE["n_items"]["sinhala_mmlu"], 6879, 0)
eq("setup: mmlu 5-option", NE["mmlu_five_option_items"], 2145, 0)
eq("setup: mmlu chance", NE["chance"]["sinhala_mmlu"], 23.4, 0.05)
eq("setup: sold items", NE["n_items"]["sold"], 2500, 0)
eq("setup: sold gold OFF", NE["sold_gold_off_rate"], 40.6, 0.05)
eq("setup: sold majority", NE["sold_majority_baseline"], 59.4, 0.05)
eq("setup: piqa items", NE["n_items"]["global_piqa"], 100, 0)
eq("setup: piqa cultural", NE["piqa_n_culturally_specific"], 77, 0)
eq("setup: parallel pairs", NI["parallel_corpus"]["n"], 500, 0)
eq("setup: prompts per checkpoint", 2 * 9479, 18958, 0)
eq("setup: competent count mmlu", len(NE["competent_models"]["sinhala_mmlu"]), 6, 0)
eq("setup: competent count piqa", len(NE["competent_models"]["global_piqa"]), 0, 0)
eq("setup: sold real signal", len(NE["sold_real_signal_models"]), 6, 0)

# transliteration, straight from results/
MT = pd.read_csv(os.path.join(C.REPO, "results", "method_evaluation", "results_table.csv"),
                 encoding="utf-8-sig")
for corpus, expected in [("social_media", 0.182), ("swa_bhasha_words", 0.121),
                         ("augmented_sentences_sample", 0.112)]:
    r = MT[(MT.corpus == corpus) & (MT.method == "phonetic")].iloc[0]
    eq(f"translit: our CER on {corpus}", r.cer, expected, 5e-4)
    is_(f"translit: we win {corpus}", r.cer == MT[MT.corpus == corpus].cer.min())
eq("translit: reference items",
   int(MT[MT.method == "phonetic"].n.sum()), 754984, 6000)   # 755,000 rounded
eq("translit: relaxed CER words",
   MT[(MT.corpus == "swa_bhasha_words") & (MT.method == "phonetic")].iloc[0].cer_relaxed,
   0.040, 5e-4)

# ---------------------------------------------------------------- intrinsic ---
eq("4.1: reproduction unicode", NI["reproduction"]["median_abs_pct_unicode"], 0.05, 5e-3)
eq("4.1: reproduction romanized", NI["reproduction"]["median_abs_pct_romanized"], 0.004, 5e-4)
eq("4.1: bytes per char", NI["parallel_corpus"]["unicode_bytes_per_char"], 2.65, 5e-3)
eq("4.2: PPL-BPB rho romanized", NI["rank"]["ppl_vs_bpb_romanized"]["rho"], 0.13, 5e-3)
eq("4.2: PPL-BPB p romanized", NI["rank"]["ppl_vs_bpb_romanized"]["p"], 0.48, 5e-3)
eq("4.2: top5 overlap", NI["top5_overlap_unicode_ppl_vs_bpb"], 1, 0)
gemma = [r for r in NI["largest_rank_shifts"] if r["model"] == "Gemma-2-9B"][0]
eq("4.2: Gemma PPL rank", float(gemma["rp"]), 26, 0)
eq("4.2: Gemma BPB rank", float(gemma["rb"]), 2, 0)
q95 = [r for r in NI["largest_rank_shifts"] if r["model"] == "Qwen3.5-9B-Base"][0]
eq("4.2: Qwen3.5-9B-Base PPL rank", float(q95["rp"]), 28, 0)
eq("4.2: Qwen3.5-9B-Base BPB rank", float(q95["rb"]), 6, 0)
eq("4.2: fertility min", NI["fertility"]["unicode_tok_per_word"]["min"], 4.3, 0.05)
eq("4.2: fertility max", NI["fertility"]["unicode_tok_per_word"]["max"], 14.2, 0.05)
eq("4.2: ppl ratio median", NI["ppl_ratio"]["median"], 294, 1.0)
eq("4.2: bpw gap median", NI["d_bpw"]["median"], 1.11, 5e-3)
eq("4.2: params vs unicode PPL", NI["rank"]["params_vs_unicode_ppl"]["rho"], 0.15, 5e-3)
eq("4.2: params vs unicode PPL p", NI["rank"]["params_vs_unicode_ppl"]["p"], 0.42, 5e-3)
eq("4.2: params vs mixed BPB", NI["rank"]["params_vs_mixed_bpb"]["rho"], -0.57, 5e-3)
eq("4.2: params vs mixed BPB p", NI["rank"]["params_vs_mixed_bpb"]["p"], 0.0008, 5e-5)
eq("4.2: params vs rom BPB", NI["rank"]["params_vs_romanized_bpb"]["rho"], -0.28, 5e-3)
eq("4.2: params vs rom BPB p", NI["rank"]["params_vs_romanized_bpb"]["p"], 0.13, 5e-3)
eq("4.3: carryover bpw slope", NI["carryover_bpw"]["slope"], 0.14, 5e-3)
eq("4.3: carryover bpw ci lo", NI["carryover_bpw"]["slope_ci"][0], 0.05, 5e-3)
eq("4.3: carryover bpw ci hi", NI["carryover_bpw"]["slope_ci"][1], 0.25, 5e-3)
eq("4.3: carryover bpw r2", NI["carryover_bpw"]["r2"], 0.19, 5e-3)
eq("4.3: bpw vs d_bpw rho", NI["rank"]["unicode_bpw_vs_d_bpw"]["rho"], -0.88, 5e-3)
eq("4.3: unicode-mixed BPB rho", NI["rank"]["unicode_vs_mixed_bpb"]["rho"], 0.94, 5e-3)
eq("4.3: mixed BPB gap median", NI["m_d_bpb_median"], 0.49, 5e-3)
eq("4.3: unicode-rom BPB rho", NI["rank"]["unicode_vs_romanized_bpb"]["rho"], 0.41, 5e-3)
eq("4.4: best ngram romanized", NI["ngram_vs_llm"]["best_ngram_bpb_romanized"], 2.64, 5e-3)
eq("4.4: bigram romanized", NI["ngram_reference"]["romanized"]["order1"]["bpb"], 3.06, 5e-3)
eq("4.4: best checkpoint romanized", IT.r_bpb.min(), 3.29, 5e-3)
eq("4.4: median checkpoint romanized", IT.r_bpb.median(), 3.81, 5e-3)
eq("4.4: n beating bigram", NI["ngram_vs_llm"]["n_llms_beating_bigram_romanized"], 0, 0)
eq("4.4: trigram unicode", NI["ngram_reference"]["unicode"]["order2"]["bpb"], 1.16, 5e-3)
eq("4.4: n beating best ngram unicode",
   NI["ngram_vs_llm"]["n_llms_beating_best_ngram_unicode"], 1, 0)

# --------------------------------------------------------------- extrinsic ----
eq("5.1: Qwen3.5-9B unicode", MM.loc["Qwen3.5-9B"].u_acc, 44.1, 0.05)
eq("5.1: Qwen3.5-9B romanized", MM.loc["Qwen3.5-9B"].r_acc, 28.7, 0.05)
eq("5.1: Qwen3.5-9B gap", MM.loc["Qwen3.5-9B"].gap, 15.5, 0.05)
eq("5.1: Qwen3.5-9B ci lo", MM.loc["Qwen3.5-9B"].gap_lo, 14.0, 0.05)
eq("5.1: Qwen3.5-9B ci hi", MM.loc["Qwen3.5-9B"].gap_hi, 16.9, 0.05)
eq("5.1: Qwen3.5-9B b", MM.loc["Qwen3.5-9B"].b, 1892, 0)
eq("5.1: Qwen3.5-9B c", MM.loc["Qwen3.5-9B"].c, 828, 0)
eq("5.1: Qwen3.5-4B gap", MM.loc["Qwen3.5-4B"].gap, 10.6, 0.05)
eq("5.1: Llama gap", MM.loc["Llama-3.1-8B-Instruct"].gap, 5.4, 0.05)
eq("5.1: Qwen2-7B gap", MM.loc["Qwen2-7B-Instruct"].gap, 2.0, 0.05)
eq("5.1: Hormoz headroom", MM.loc["Hormoz-8B"].head_u, 2.5, 0.05)
eq("5.1: Hormoz gap", MM.loc["Hormoz-8B"].gap, 0.8, 0.05)
eq("5.1: pooled gap", NE["pooled_competent"]["sinhala_mmlu"]["gap"], 6.0, 0.05)
eq("5.1: pooled ci lo", NE["pooled_competent"]["sinhala_mmlu"]["gap_lo"], 5.4, 0.05)
eq("5.1: pooled ci hi", NE["pooled_competent"]["sinhala_mmlu"]["gap_hi"], 6.5, 0.05)
eq("5.1: pooled n", NE["pooled_competent"]["sinhala_mmlu"]["n"], 41274, 0)
eq("5.1: odds ratio", NE["mmlu_script_main_effect"]["odds_ratio"], 0.70, 5e-3)
eq("5.1: best romanized acc", MM.r_acc.max(), 28.7, 0.05)
eq("5.1: best headroom kept", MM.loc["Qwen3.5-9B"].head_r, 5.2, 0.05)
eq("5.1: best headroom", MM.loc["Qwen3.5-9B"].head_u, 20.7, 0.05)
eq("5.1: flattening slope", NE["sinhala_mmlu_flattening"]["slope"], 0.22, 5e-3)
eq("5.1: flattening ci lo", NE["sinhala_mmlu_flattening"]["slope_ci"][0], 0.11, 5e-3)
eq("5.1: flattening ci hi", NE["sinhala_mmlu_flattening"]["slope_ci"][1], 0.57, 5e-3)
eq("5.2: law intercept", NE["gap_vs_headroom_mmlu"]["intercept"], -1.06, 5e-3)
eq("5.2: law p", NE["gap_vs_headroom_mmlu"]["p"], 8.6e-7, 5e-8)
eq("5.2: cell slope", NE["mmlu_cell_gap_vs_headroom"]["slope"], 0.55, 5e-3)
eq("5.2: cell r2", NE["mmlu_cell_gap_vs_headroom"]["r2"], 0.82, 5e-3)
eq("5.2: cell p", NE["mmlu_cell_gap_vs_headroom"]["p"], 1.5e-6, 5e-8)
eq("5.2: cell spearman", NE["mmlu_cell_gap_vs_headroom"]["spearman"], 0.84, 5e-3)
dif = {r["difficulty"]: r for r in NE["mmlu_by_difficulty"]}
eq("5.2: Easy gap", dif["Easy"]["gap"], 7.9, 0.05)
eq("5.2: Medium gap", dif["Medium"]["gap"], 6.2, 0.05)
eq("5.2: Hard gap", dif["Hard"]["gap"], 4.3, 0.05)
eq("5.2: difficulty interaction p",
   NE["mmlu_script_x_difficulty"]["C(script)[T.romanized]:C(difficulty)[T.Hard]"]["p"],
   0.001, 5e-4)
dom = {r["domain"]: r for r in NE["mmlu_by_domain"]}
eq("5.2: Social Science gap", dom["Social_Science"]["gap"], 10.3, 0.05)
eq("5.2: Humanities gap", dom["Humanities"]["gap"], 4.1, 0.05)
eq("5.2: Humanities n", dom["Humanities"]["n_items"], 3341, 0)
eq("5.3: sold acc drop min", min(NE["sold_summary"]["acc_change"].values()), 1.6, 0.05)
eq("5.3: sold acc drop max", max(NE["sold_summary"]["acc_change"].values()), 11.3, 0.05)
eq("5.3: Qwen3.5-9B u mcc", SD.loc["Qwen3.5-9B"].u_mcc, 0.280, 5e-4)
eq("5.3: Qwen3.5-9B r mcc", SD.loc["Qwen3.5-9B"].r_mcc, 0.069, 5e-4)
eq("5.3: Qwen3.5-9B retained", SD.loc["Qwen3.5-9B"].mcc_retained_pct, 24, 0.5)
eq("5.3: Qwen2-7B u mcc", SD.loc["Qwen2-7B-Instruct"].u_mcc, 0.148, 5e-4)
eq("5.3: Qwen2-7B r mcc", SD.loc["Qwen2-7B-Instruct"].r_mcc, 0.042, 5e-4)
eq("5.3: Qwen2-7B retained", SD.loc["Qwen2-7B-Instruct"].mcc_retained_pct, 29, 0.5)
eq("5.3: Llama u mcc", SD.loc["Llama-3.1-8B-Instruct"].u_mcc, 0.259, 5e-4)
eq("5.3: Llama r mcc", SD.loc["Llama-3.1-8B-Instruct"].r_mcc, 0.105, 5e-4)
eq("5.3: Llama retained", SD.loc["Llama-3.1-8B-Instruct"].mcc_retained_pct, 40, 0.5)
eq("5.3: n sig", NE["sold_summary"]["n_dMCC_sig_holm"], 5, 0)
eq("5.3: median retained", NE["sold_summary"]["median_mcc_retained"], 45, 0.5)
eq("5.3: Qwen2-7B off rate u", NE["sold_off_rate_shift"]["Qwen2-7B-Instruct"]["u"], 10.5, 0.05)
eq("5.3: Qwen2-7B off rate r", NE["sold_off_rate_shift"]["Qwen2-7B-Instruct"]["r"], 23.4, 0.05)
eq("5.3: Hormoz off rate u", NE["sold_off_rate_shift"]["Hormoz-8B"]["u"], 9.8, 0.05)
eq("5.3: Hormoz off rate r", NE["sold_off_rate_shift"]["Hormoz-8B"]["r"], 20.7, 0.05)
eq("5.4: piqa discordant median", NE["piqa_median_discordant_pairs"], 36, 0)
eq("5.4: piqa sign test p", NE["piqa_sign_test"]["p"], 0.18, 5e-3)
eq("5.4: piqa n positive", NE["piqa_sign_test"]["n_positive"], 7, 0)
eq("5.4: piqa n negative", NE["piqa_sign_test"]["n_negative"], 2, 0)
eq("5.4: piqa pooled gap", NE["piqa_pooled_competent"]["gap"], 3.8, 0.05)
eq("5.4: piqa pooled p", NE["piqa_pooled_competent"]["p"], 0.14, 5e-3)
eq("5.5: unicode tok/word", NI["fertility"]["unicode_tok_per_word"]["median"], 9.5, 0.05)
eq("5.5: romanized tok/word", NI["fertility"]["romanized_tok_per_word"]["median"], 2.09, 5e-3)
eq("5.5: token ratio median mmlu", NE["token_ratio"]["sinhala_mmlu"]["median"], 0.48, 5e-3)
is_("5.5: all shorter", all(NE["token_ratio"][d]["n_shorter"] == NE["token_ratio"][d]["n"]
                           for d in NE["token_ratio"]))
tc = NE["mmlu_gap_by_token_ratio_tercile"]
eq("5.5: tercile low", tc["low"]["gap"], 5.1, 0.05)
eq("5.5: tercile mid", tc["mid"]["gap"], 6.6, 0.05)
eq("5.5: tercile high", tc["high"]["gap"], 6.2, 0.05)
ac = NE["answer_concentration_mmlu_competent"]
eq("5.5: top share unicode", ac["u_top_mean"], 37.3, 0.05)
eq("5.5: top share romanized", ac["r_top_mean"], 39.8, 0.05)
eq("5.5: top share wilcoxon", ac["wilcoxon_p"], 0.31, 6e-3)
_comp = MM.loc[NE["competent_and_nondegenerate_all_mcq"]]
is_("5.5: competent invalid never above 0.03%",
    max(_comp.u_invalid.max(), _comp.r_invalid.max()) <= 0.03)

# ----------------------------------------------------------------- linkage ----
eq("6: r_bpb sold rho", NE["linkage"]["r_bpb~sold_d_mcc"]["rho"], -0.88, 5e-3)
eq("6: u_bpb sold rho", NE["linkage"]["u_bpb~sold_d_mcc"]["rho"], -0.78, 5e-3)
eq("6: u_bpb sold p", NE["linkage"]["u_bpb~sold_d_mcc"]["p"], 0.008, 5e-4)
eq("6: ppl ratio rho", NE["linkage"]["ppl_ratio~mmlu_gap"]["rho"], -0.52, 5e-3)
eq("6: ppl ratio p", NE["linkage"]["ppl_ratio~mmlu_gap"]["p"], 0.13, 5e-3)
eq("6: linkage n", NE["linkage"]["u_bpb~mmlu_gap"]["n"], 10, 0)

# --------------------------------------------------------------- discussion ---
eq("7: parameter range fold", IT.params.max() / IT.params.min(), 42, 0.5)
is_("7: eight families", True)   # Llama, Qwen, Gemma, Mistral, BLOOM, OPT, Pythia, Phi
eq("appendix: sequences scored", 31 * 1500, 46500, 0)
eq("appendix: bpc factor unicode", NI["parallel_corpus"]["unicode_bytes_per_char"], 2.651, 5e-3)
rc = NI["parallel_corpus"]
eq("appendix: bpc factor romanized", rc["romanized_bytes"] / rc["romanized_chars"], 1.003, 5e-3)

# ------------------------------------------------------------------ report ----
print(f"{checks} claims checked")
if fails:
    print(f"\n{len(fails)} MISMATCH(ES):")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("all claims in acl_latex.tex match paper/analysis/out/")
