"""Check the numeric claims written into the paper against the frozen analysis.

Every assertion below restates a number that appears in main.tex. If the
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
RB = json.load(open(os.path.join(C.OUT_DIR, "robustness_numbers.json")))
AT = json.load(open(os.path.join(C.OUT_DIR, "attestation_numbers.json")))
SV = json.load(open(os.path.join(C.OUT_DIR, "synthetic_vs_human.json")))
SL = json.load(open(os.path.join(C.OUT_DIR, "sinllama.json")))
PW = json.load(open(os.path.join(C.OUT_DIR, "power.json")))
PQ = json.load(open(os.path.join(C.OUT_DIR, "piqa_rerun.json")))
TF = json.load(open(os.path.join(C.OUT_DIR, "tokenizer_fertility.json")))
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
eq("5.1: flattening slope", RB["flattening_models"]["levels"]["slope"], 0.22, 5e-3)
eq("5.2: levels ci lo",
   RB["flattening_models"]["levels"]["slope_boot_ci"]["lo"], 0.11, 5e-3)
eq("5.2: levels ci hi",
   RB["flattening_models"]["levels"]["slope_boot_ci"]["hi"], 0.54, 5e-3)
eq("5.2: law intercept", NE["gap_vs_headroom_mmlu"]["intercept"], -1.06, 5e-3)
eq("5.2: law p", NE["gap_vs_headroom_mmlu"]["p"], 8.6e-7, 5e-8)
eq("5.2: cell levels slope", RB["flattening_cells"]["levels"]["slope"], 0.45, 5e-3)
eq("5.2: cell levels ci lo",
   RB["flattening_cells"]["levels"]["slope_boot_ci"]["lo"], 0.36, 5e-3)
eq("5.2: cell levels ci hi",
   RB["flattening_cells"]["levels"]["slope_boot_ci"]["hi"], 0.63, 5e-3)
eq("5.2: cell levels loco lo",
   RB["flattening_cells"]["levels"]["loco"]["slope_min"], 0.43, 5e-3)
eq("5.2: cell levels loco hi",
   RB["flattening_cells"]["levels"]["loco"]["slope_max"], 0.50, 5e-3)
eq("5.2: cell levels r2", RB["flattening_cells"]["levels"]["r2"], 0.75, 5e-3)
eq("5.2: cell levels p vs 1",
   RB["flattening_cells"]["levels"]["p_slope_eq_1"], 1.5e-6, 5e-8)
eq("5.2: cell weighted slope",
   RB["flattening_cells"]["levels_weighted_slope"], 0.48, 5e-3)
eq("5.2: n cells", RB["flattening_cells"]["n_cells"], 16, 0)
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
# Global PIQA is the re-run with the item-type-aware instruction; the earlier
# prompt's numbers stay in extrinsic_numbers.json for the comparison only.
eq("5.4: piqa items", PQ["n_items"], 100, 0)
eq("5.4: piqa question items", PQ["item_forms"]["question_answer"], 40, 0)
eq("5.4: piqa completion items", PQ["item_forms"]["paragraph_completion"], 60, 0)
eq("5.4: piqa discordant median", PQ["median_discordant_pairs"], 36, 0)
eq("5.4: piqa best native acc", max(r["u_acc"] for r in PQ["per_model"]), 58.0, 0.05)
eq("5.4: piqa best native p", min(r["u_p_above"] for r in PQ["per_model"]), 0.055, 5e-3)
eq("5.4: piqa parseable", PQ["n_parseable"], 10, 0)
eq("5.4: piqa n drop", PQ["parseable_summary"]["n_drop"], 4, 0)
eq("5.4: piqa n rise", PQ["parseable_summary"]["n_rise"], 4, 0)
eq("5.4: piqa n tie", PQ["parseable_summary"]["n_tie"], 2, 0)
eq("5.4: piqa sign test n moved", PQ["sign_test"]["n_moved"], 8, 0)
eq("5.4: piqa sign test p", PQ["sign_test"]["p"], 1.00, 5e-3)
eq("5.4: piqa pooled gap", PQ["pooled_parseable"]["gap"], -0.1, 0.05)
eq("5.4: piqa pooled CI lo", PQ["pooled_parseable"]["gap_lo"], -3.6, 0.05)
eq("5.4: piqa pooled CI hi", PQ["pooled_parseable"]["gap_hi"], 3.3, 0.05)
eq("5.4: piqa competent", PQ["n_competent"], 0, 0)
eq("app H: piqa sig after holm", PQ["n_sig_holm"], 1, 0)
eq("app H: piqa lamini gap", min(r["gap"] for r in PQ["per_model"]), -42.0, 0.05)
eq("app H: piqa question-form gap", PQ["by_item_form"][0]["gap"], 1.0, 0.05)
eq("app H: piqa completion-form gap", PQ["by_item_form"][1]["gap"], -0.83, 0.05)
eq("app H: piqa cultural gap", PQ["by_cultural"][0]["gap"], 1.17, 0.05)
eq("app H: piqa non-cultural gap", PQ["by_cultural"][1]["gap"], -4.35, 0.05)
eq("app H: piqa max invalid excl lamini",
   max(r["r_invalid"] for r in PQ["per_model"] if r["model"] != "LaMini-GPT-1.5B"), 9.0, 0.05)
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
L = RB["linkage_ci"]
eq("6: u_bpb mmlu ci lo", L["u_bpb~mmlu_gap"]["ci_lo"], -1.00, 5e-3)
eq("6: u_bpb mmlu ci hi", L["u_bpb~mmlu_gap"]["ci_hi"], -0.30, 5e-3)
eq("6: u_bpb mmlu loo lo", L["u_bpb~mmlu_gap"]["loo_min"], -0.90, 5e-3)
eq("6: u_bpb mmlu loo hi", L["u_bpb~mmlu_gap"]["loo_max"], -0.77, 5e-3)
eq("6: u_bpb sold ci lo", L["u_bpb~sold_d_mcc"]["ci_lo"], -1.00, 5e-3)
eq("6: u_bpb sold ci hi", L["u_bpb~sold_d_mcc"]["ci_hi"], -0.36, 5e-3)
eq("6: u_bpb sold loo lo", L["u_bpb~sold_d_mcc"]["loo_min"], -0.87, 5e-3)
eq("6: u_bpb sold loo hi", L["u_bpb~sold_d_mcc"]["loo_max"], -0.73, 5e-3)
eq("6: d_bpb ci lo", L["d_bpb~mmlu_gap"]["ci_lo"], -0.89, 5e-3)
eq("6: d_bpb ci hi", L["d_bpb~mmlu_gap"]["ci_hi"], 0.63, 5e-3)
is_("6: d_bpb loo straddles zero", not L["d_bpb~mmlu_gap"]["loo_sign_stable"])

# --------------------------------------------------------------- discussion ---
eq("7: parameter range fold", IT.params.max() / IT.params.min(), 42, 0.5)
is_("7: eight families", True)   # Llama, Qwen, Gemma, Mistral, BLOOM, OPT, Pythia, Phi
eq("appendix: sequences scored", 31 * 1500, 46500, 0)
eq("appendix: bpc factor unicode", NI["parallel_corpus"]["unicode_bytes_per_char"], 2.651, 5e-3)
rc = NI["parallel_corpus"]
eq("appendix: bpc factor romanized", rc["romanized_bytes"] / rc["romanized_chars"], 1.003, 5e-3)

# ============================ claims added in the revision ==================

S24 = RB["shared24"]
eq("4.1: shared pool size", S24["n_shared"], 24, 0)
eq("4.1: new checkpoints", S24["n_new"], 7, 0)
eq("4.1: shared24 median ratio", S24["ppl_ratio"]["median"], 312.3, 0.05)
eq("4.1: mixed dev excl outliers",
   S24["published_ppl_deviation_pct"]["mixed_median_excl_outliers"], 0.39, 5e-3)
is_("4.1: two mixed outliers",
    len(S24["published_ppl_deviation_pct"]["mixed_outliers_gt5pct"]) == 2)
eq("4.2: shared24 ppl-bpb rho", S24["ppl_vs_bpb_unicode"]["rho"], 0.46, 5e-3)
eq("4.2: shared24 ppl-bpb p", S24["ppl_vs_bpb_unicode"]["p"], 0.02, 5e-3)
eq("4.3: shared24 params-bpb rho", S24["params_vs_unicode_bpb"]["rho"], -0.42, 5e-3)
eq("4.3: shared24 params-bpb p", S24["params_vs_unicode_bpb"]["p"], 0.04, 5e-3)

D = RB["decomposition"]
is_("4.3: decomposition is an identity", D["identity_max_abs_resid_bits"] < 1e-12)
eq("4.3: shared24 total bits", D["shared24"]["median_total_bits"], 8.29, 5e-3)
eq("4.3: shared24 normaliser bits", D["shared24"]["median_tok_term_bits"], 4.37, 5e-3)
eq("4.3: shared24 loss bits", D["shared24"]["median_loss_term_bits"], 4.56, 5e-3)
eq("4.3: shared24 normaliser factor", D["shared24"]["median_tok_factor"], 21, 0.5)
eq("4.3: shared24 loss factor", D["shared24"]["median_loss_factor"], 24, 0.5)
eq("4.3: shared24 total factor", D["shared24"]["median_total_factor"], 312, 1.0)
eq("4.3: all31 normaliser share", D["median_tok_share_pct"], 39, 0.5)
eq("4.3: bpb gap median", NI["d_bpb"]["median"], 2.14, 5e-3)
eq("4.3: bpb gap factor", NI["d_bpb"]["median_prob_factor"], 4.4, 0.05)
DC = pd.read_csv(os.path.join(C.OUT_DIR, "ppl_decomposition.csv")).set_index("model")
is_("4.3: Qwen3.5 and Gemma normaliser terms are negative",
    all(DC.loc[m].tok_term < 0 for m in
        ["Qwen3.5-4B", "Qwen3.5-4B-Base", "Qwen3.5-9B", "Qwen3.5-9B-Base",
         "Gemma-7B", "Gemma-2-9B"]))
_all = IT.set_index("model")
_all = (_all.r_ppl / _all.u_ppl).sort_values()
_qwen35 = ["Qwen3.5-9B", "Qwen3.5-9B-Base", "Qwen3.5-4B-Base", "Qwen3.5-4B"]
eq("4.3: Qwen3.5 ratio min", _all[_qwen35].min(), 58, 0.5)
eq("4.3: Qwen3.5 ratio max", _all[_qwen35].max(), 64, 0.5)
is_("4.3: Qwen3.5 hold the four smallest ratios",
    set(_all.index[:4]) == set(_qwen35))
is_("4.3: Gemma-7B is fifth smallest", _all.index[4] == "Gemma-7B")
eq("4.3: pool median ratio", _all.median(), 294, 0.5)

FM = RB["flattening_models"]
eq("5.2: headroom slope", FM["headroom"]["slope"], 0.78, 5e-3)
eq("5.2: headroom r2", FM["headroom"]["r2"], 0.96, 5e-3)
eq("5.2: levels loco lo", FM["levels"]["loco"]["slope_min"], 0.17, 5e-3)
eq("5.2: levels loco hi", FM["levels"]["loco"]["slope_max"], 0.26, 5e-3)
eq("5.2: levels r2", FM["levels"]["r2"], 0.65, 5e-3)
eq("5.2: levels p vs 1", FM["levels"]["p_slope_eq_1"], 8.6e-7, 5e-8)
PN = FM["permutation_null"]
eq("5.2: null headroom slope", PN["headroom_slope_mean"], 1.00, 5e-3)
eq("5.2: null headroom r2", PN["headroom_r2_mean"], 0.94, 5e-3)
eq("5.2: null headroom p", PN["headroom_p_r2_ge_obs"], 0.089, 5e-3)
eq("5.2: null levels slope", PN["levels_slope_mean"], 0.00, 5e-3)
eq("5.2: null levels r2", PN["levels_r2_mean"], 0.11, 5e-3)
eq("5.2: null levels p", PN["levels_p_r2_ge_obs"], 0.005, 1e-3)
eq("5.3: Phi-4 u mcc", SD.loc["Phi-4-14B"].u_mcc, 0.152, 5e-4)
eq("5.3: Phi-4 r mcc", SD.loc["Phi-4-14B"].r_mcc, 0.076, 5e-4)

# ------------------------------------------------- transliterator fidelity ----
A = AT["aligned"]
eq("app G: sentences aligned", A["n_sentences_word_aligned"], 485, 0)
eq("app G: word pairs", A["n_word_pairs"], 2933, 0)
eq("app G: exact match", A["word_exact_match_pct"], 44.6, 0.05)
eq("app G: vowel-normalised match", A["word_exact_match_vowel_collapsed_pct"], 72.2, 0.05)
MP = A["mismatch_profile"]
eq("app G: vowel-only share", MP["vowel_convention_only_pct"], 27.6, 0.05)
eq("app G: residual share", MP["residual_pct"], 27.8, 0.05)
AA = AT["attestation"]
eq("app G: lexicon words", AA["lexicon_words"], 449598, 0)
eq("app G: mean spellings per word", AA["lexicon_mean_spellings_per_word"], 15.7, 0.05)
eq("app G: ours attested norm", AA["parallel_ours"]["attested_vowel_collapsed_pct"], 88.6, 0.05)
eq("app G: human attested norm", AA["parallel_human"]["attested_vowel_collapsed_pct"], 84.2, 0.05)
eq("app G: sold attested norm", AA["sold"]["attested_vowel_collapsed_pct"], 87.0, 0.05)
eq("app G: piqa attested norm", AA["global_piqa"]["attested_vowel_collapsed_pct"], 86.9, 0.05)
DN = AT["downstream"]
eq("app G: attestation items", DN["n_items_scored"], 2447, 0)
eq("app G: attestation spearman", DN["item_spearman_attest_vs_loss"]["rho"], 0.02, 5e-3)
eq("app G: attestation spearman p", DN["item_spearman_attest_vs_loss"]["p"], 0.31, 5e-3)
eq("app G: tercile gap low", DN["low"]["gap"], 5.0, 0.05)
eq("app G: tercile gap mid", DN["mid"]["gap"], 7.2, 0.05)
eq("app G: tercile gap high", DN["high"]["gap"], 7.3, 0.05)

# --------------------------------------------- our text against human typing --
_d = [v["ours_minus_human"]["bpb"] for v in SV.values()]
_r = [v["ours_over_human_ppl"] for v in SV.values()]
_dev = [x["bpb"] for v in SV.values() for x in v["reproduction_pct_dev"].values()]
eq("app G: control checkpoints", len(SV), 6, 0)
is_("app G: ours is harder for every checkpoint", all(x > 0 for x in _d))
eq("app G: ours-human min", min(_d), 0.17, 5e-3)
eq("app G: ours-human max", max(_d), 0.24, 5e-3)
is_("app G: perplexity says the opposite", all(x < 1 for x in _r))
eq("app G: control ppl ratio median", float(pd.Series(_r).median()), 0.74, 5e-3)
eq("app G: control reproduction max", max(_dev), 0.11, 5e-3)
is_("app G: two control checkpoints are downstream ones",
    len(set(SV) & set(C.EXTRINSIC_MODELS)) == 2)

# ------------------------------------------------------------- prompt pilot ---
P = RB["pilot"]
eq("app A: pilot generations", P["n_generations"], 3240, 0)
eq("app A: pilot items per dataset", P["n_items_per_dataset"], 20, 0)
is_("app A: template used is T1", P["template_used"] == "T1_direct")
is_("app A: T1 wins mmlu", P["winners"]["sinhala_mmlu"]["best_template"] == "T1_direct")
is_("app A: T1 has no invalid output on mmlu",
    P["winners"]["sinhala_mmlu"]["t1_invalid_rate"] == 0.0)
eq("app A: T3 lead on sold",
   100 * (P["winners"]["sold"]["best_overall_acc"] - P["winners"]["sold"]["t1_overall_acc"]),
   1.4, 0.05)
eq("app A: pilot overlap pct", P["mmlu_pilot_overlap_pct"], 0.3, 0.05)
eq("app A: pilot overlap items", P["mmlu_pilot_items_in_eval_set"], 20, 0)

eq("app I: control sequences scored", 6 * 3 * 500, 9000, 0)


# --------------------------------------------- the Sinhala-adapted checkpoint --
# Section 4.5 and Appendix G.
P_, A_ = SL["parent"], SL["adapted"]
eq("4.5: parent unicode bpb", P_["u_bpb"], 1.157, 5e-4)
eq("4.5: adapted unicode bpb", A_["u_bpb"], 0.628, 5e-4)
eq("4.5: parent unicode ppl", P_["u_ppl"], 3.25, 5e-3)
eq("4.5: adapted unicode ppl", A_["u_ppl"], 74.56, 5e-3)
eq("4.5: parent unicode fertility", P_["u_tok_per_word"], 9.68, 5e-3)
eq("4.5: adapted unicode fertility", A_["u_tok_per_word"], 1.44, 5e-3)
eq("4.5: parent ppl ratio", SL["ppl_ratio"]["parent"], 310.7, 0.05)
eq("4.5: adapted ppl ratio", SL["ppl_ratio"]["adapted"], 8.7, 0.05)
eq("4.5: parent d_bpb", SL["d_bpb"]["parent"], 2.447, 5e-4)
eq("4.5: adapted d_bpb", SL["d_bpb"]["adapted"], 2.743, 5e-4)
eq("4.5: unicode bpb gain", -SL["gains"]["unicode"]["bpb_delta"], 0.528, 5e-4)
eq("4.5: romanized bpb gain", -SL["gains"]["romanized"]["bpb_delta"], 0.233, 5e-4)
eq("4.5: gain asymmetry", SL["adaptation_asymmetry"], 2.3, 0.05)
eq("abstract: adapted ppl factor", SL["gains"]["unicode"]["ppl_factor"], 23.0, 0.05)
is_("4.5: adapted is best of 32 by unicode bpb",
    SL["ranks_among_32"]["u_bpb"] == 1)
is_("4.5: adapted is worst of 32 by unicode ppl",
    SL["ranks_among_32"]["u_ppl"] == 32)
is_("4.5: adapted has the smallest reported ratio of 32",
    SL["ranks_among_32"]["ppl_ratio"] == 1)
is_("4.5: only one of the 31 has a wider per-byte gap",
    SL["ranks_among_32"]["d_bpb"] == 31)
eq("app G: added Sinhala pieces", SL["vocab"]["SinLlama-8B"] - SL["vocab"]["Llama-3-8B"],
   11080, 0)
eq("app G: adapted vocab", SL["vocab"]["SinLlama-8B"], 139336, 0)
eq("app G: bytes per token unicode",
   SL["decomposition_adapted"]["bytes_per_token_unicode"], 9.90, 5e-3)
eq("app G: bytes per token romanized",
   SL["decomposition_adapted"]["bytes_per_token_romanized"], 2.77, 5e-3)
eq("app G: decomposition normalizer term",
   SL["decomposition_adapted"]["normalizer_bits"], -14.26, 5e-3)
eq("app G: decomposition per-byte term",
   SL["decomposition_adapted"]["per_byte_bits"], 17.38, 5e-3)
eq("app G: decomposition total", SL["decomposition_adapted"]["total_bits"], 3.11, 5e-3)
is_("app G: decomposition is exact",
    abs(SL["decomposition_adapted"]["residual"]) < 1e-9)
eq("app G: two Llama versions within 0.008 bpb",
   abs(P_["u_bpb"] - float(IT[IT.model == "Llama-3.1-8B"].u_bpb.iloc[0])), 0.008, 5e-4)
R_ = SL["conclusion_robustness"]
eq("3.3 reply: rho(ppl,bpb) with adapted",
   R_["ppl_vs_bpb_unicode"]["with_sinllama"]["rho"], -0.02, 5e-3)
eq("3.3 reply: rho(fertility,ppl) with adapted",
   R_["fertility_vs_unicode_ppl"]["with_sinllama"]["rho"], -0.88, 5e-3)
eq("3.3 reply: rho(params,bpb) with adapted",
   R_["params_vs_unicode_bpb"]["with_sinllama"]["rho"], -0.56, 5e-3)

# ------------------------------------------------------- power, section 5.4 ----
eq("5.4: piqa MDE", PW["global_piqa"]["mde_points"], 17.3, 0.05)
eq("5.4: mmlu MDE", PW["sinhala_mmlu"]["mde_points"], 1.74, 5e-3)
eq("app H: power at the reference gap", PW["global_piqa"]["power_at_reference_gap"],
   0.126, 5e-3)
eq("app H: items needed for the reference gap",
   PW["global_piqa"]["items_needed_for_reference_gap"], 825, 0)
eq("5.4: reference gap points", PW["reference_gap_points"], 6.0, 0.05)
eq("5.4: largest mmlu gap", PW["largest_mmlu_gap_points"], 15.5, 0.05)
eq("5.4: piqa median discordant pairs",
   PW["observed"]["global_piqa"]["median_discordant_pairs"], 36, 0)

# --------------------------------------------- tokenizer fertility, app H -----
T_ = TF["tokenizers"]
eq("2.5: HelaBERT unicode fertility", T_["HelaBERT"]["unicode"], 1.31, 5e-3)
eq("2.5: SinLlama unicode fertility",
   T_["SinLlama (Extended-Sinhala-LLaMA)"]["unicode"], 1.44, 5e-3)
eq("2.5: SinBERT romanized fertility", T_["SinBERT-large"]["romanized"], 6.15, 5e-3)
is_("2.5: SinBERT is the worst on romanized text",
    T_["SinBERT-large"]["romanized"] > TF["pool_of_31"]["romanized_max"])
eq("app H: HelaBERT vocab", T_["HelaBERT"]["vocab"], 32000, 0)

# ------------------------------------------------------------------ report ----
print(f"{checks} claims checked")
if fails:
    print(f"\n{len(fails)} MISMATCH(ES):")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("all claims in paper/main.tex match paper/analysis/out/")
