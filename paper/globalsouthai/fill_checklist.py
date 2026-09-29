"""Fill the NeurIPS checklist answers in checklist.tex, in document order.

The checklist questions and guidelines are kept verbatim, as the template
requires. Only the Answer and Justification lines are replaced, and only with
the macros the template provides. Run from anywhere:

    python paper/globalsouthai/fill_checklist.py
"""
from __future__ import annotations

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "checklist.tex")

# (macro, justification) in the order the items appear in the template.
ANSWERS = [
    # 1 Claims
    (r"\answerYes{}",
     r"The abstract and Section~\ref{sec:intro} state the three claims the paper "
     r"supports, namely that almost all of the published degradation ratio is the token-count normalizer (Section~\ref{sec:metric}), that romanization compresses rather "
     r"than uniformly lowers downstream ability (Section~\ref{sec:flatten}), and "
     r"that the metric a benchmark reports decides which of these is visible "
     r"(Section~\ref{sec:lessons}). Scope is one language and eleven open "
     r"instruction-tuned checkpoints, stated in Section~\ref{sec:setup} and bounded "
     r"in Section~\ref{sec:limitations}."),
    # 2 Limitations
    (r"\answerYes{}",
     r"Section~\ref{sec:limitations} lists the binding limitations, and "
     r"Appendix~\ref{sec:limitfull} gives the full set, including the single "
     r"language, the synthetic Romanized side of the downstream items and what we "
     r"measured that substitution to cost, the confounding of scale with family and "
     r"tokenizer, unauditable pretraining corpora, and the exploratory status of the "
     r"intrinsic-to-downstream link."),
    # 3 Theory assumptions and proofs
    (r"\answerNA{}",
     r"The paper proves no theorems. The one analytic step, the exact split in "
     r"Equation~\ref{eq:decomp}, is an algebraic rearrangement of the definition of "
     r"perplexity, it is derived in full in Section~\ref{sec:metric}, and we verify "
     r"it numerically on our own measurements to $5 \times 10^{-15}$ bits."),
    # 4 Experimental result reproducibility
    (r"\answerYes{}",
     r"Section~\ref{sec:setup} and Appendix~\ref{sec:setupfull} give the checkpoint list with Hugging Face identifiers, the corpora and splits, the "
     r"prompt templates, the decoding settings, the answer-extraction rule, the "
     r"competence screen, and every statistical procedure. "
     r"Appendix~\ref{sec:reproduction} additionally reproduces the published "
     r"perplexities we build on, to a median of 0.05\%."),
    # 5 Open access to data and code
    (r"\answerYes{}",
     r"All analysis code, the transliterator, the frozen result files and the scripts "
     r"that regenerate every number, table and figure in this paper are in the "
     r"repository at \repo. One dataset cannot be redistributed. SinhalaMMLU is licensed CC BY-NC-ND 4.0 and its authors asked that the full "
     r"set stay private, so we release the transformation code and the item "
     r"identifiers instead of the items (Appendix~\ref{sec:licences})."),
    # 6 Experimental setting/details
    (r"\answerYes{}",
     r"There is no training in this work, so the relevant details are evaluation details, namely zero-shot prompting, greedy decoding with a 40-token limit, one "
     r"template chosen on a documented pilot, no item sampling, and fp16 inference. "
     r"All of these are in Section~\ref{sec:setup} and "
     r"Appendix~\ref{sec:setupfull}."),
    # 7 Experiment statistical significance
    (r"\answerYes{}",
     r"Every paired comparison is tested with McNemar's test under Holm correction "
     r"within a task and reported with its discordant pair counts, and every "
     r"interval is a 95\% confidence interval from 10{,}000 paired bootstrap "
     r"resamples, with the resampling unit stated in each case "
     r"(Section~\ref{sec:setup}). Regression slopes carry bootstrap intervals, "
     r"leave-one-out ranges and permutation tests, and "
     r"Appendix~\ref{sec:flattenfull} reports one fit we discard as an algebraic "
     r"artifact after its own permutation null reproduced it."),
    # 8 Experiments compute resources
    (r"\answerYes{}",
     r"Section~\ref{sec:setup} reports 80 GPU hours of wall clock in total, about 10 "
     r"for the intrinsic sweep over 31 checkpoints and about 70 for the 208{,}538 "
     r"downstream generations, of which roughly 25 are one 14.7B checkpoint. "
     r"Appendix~\ref{sec:setupfull} names the hardware, two T4 GPUs in fp16 with a "
     r"single 16\,GB RTX 4070 Ti SUPER for the largest checkpoint, and the CPU cost "
     r"of the transliteration control."),
    # 9 Code of ethics
    (r"\answerYes{}",
     r"We reviewed the NeurIPS Code of Ethics. The work is evaluation only, adds no "
     r"new human annotation or data collection, quotes no offensive text from the "
     r"corpus it measures, and respects the redistribution terms of every asset it "
     r"uses (Appendix~\ref{sec:ethics})."),
    # 10 Broader impacts
    (r"\answerYes{}",
     r"Section~\ref{sec:lessons} and Appendix~\ref{sec:ethics} discuss both directions. The positive impact is that a safety system validated on the "
     r"formal script and serving Romanized users can now be shown to be far worse in "
     r"the field than in evaluation, and the negative one is that our transliterator "
     r"deliberately collapses consonant distinctions, so it suits building evaluation "
     r"data and not rendering names."),
    # 11 Safeguards
    (r"\answerNA{}",
     r"We release no model weights, no scraped data and no generative artifact. The "
     r"released code is a deterministic rule-based transliterator and the analysis "
     r"pipeline, and the offensive-language corpus we measure on is an existing pseudonymized research release that we do not redistribute."),
    # 12 Licenses for existing assets
    (r"\answerYes{}",
     r"Appendix~\ref{sec:licences} names every dataset, model family and tool we use with its license and states exactly what we do and do not redistribute, "
     r"including the CC BY-NC-ND 4.0 terms of SinhalaMMLU, the CC BY-SA 4.0 terms of "
     r"Global PIQA and its prohibition on training, and the AGPL-3.0 license of Aksharamukha. The acknowledgement that the uroman license requires is given "
     r"in Appendix~\ref{sec:licences}."),
    # 13 New assets
    (r"\answerYes{}",
     r"The new assets are the Sinhala-to-Latin transliterator, the Romanized "
     r"evaluation conditions and the analysis pipeline, all documented in "
     r"Appendix~\ref{sec:translit} and in the README of the anonymous repository at "
     r"\repo, which states the license, the intended use and the known "
     r"limitations of each."),
    # 14 Crowdsourcing and research with human subjects
    (r"\answerNA{}",
     r"We ran no crowdsourcing and no study with human subjects. The human-typed "
     r"Romanized text we validate against comes from existing public research "
     r"releases collected by their own authors."),
    # 15 IRB
    (r"\answerNA{}",
     r"No human subjects research was conducted, so no institutional review was "
     r"required. All data is existing public research releases used for evaluation "
     r"only (Appendix~\ref{sec:ethics})."),
    # 16 Declaration of LLM usage
    (r"\answerNA{}",
     r"Language models are the object of study here rather than a component of the "
     r"method. The method itself is a deterministic transliterator, a "
     r"tokenizer-independent metric and a paired statistical design, none of which "
     r"involves an LLM."),
]

ANS_RE = re.compile(r"\\answerTODO\{\}[^\n]*")
JUS_RE = re.compile(r"\\justificationTODO\{\}")


def main() -> None:
    with open(PATH, encoding="utf-8") as f:
        text = f.read()

    if text.count("answerTODO") != len(ANSWERS):
        raise SystemExit(f"expected {len(ANSWERS)} answers, found "
                         f"{text.count('answerTODO')} placeholders")

    ans = iter(a for a, _ in ANSWERS)
    jus = iter(j for _, j in ANSWERS)
    text = ANS_RE.sub(lambda m: next(ans), text)
    text = JUS_RE.sub(lambda m: next(jus), text)
    text = text.replace("Conferences/2025/LLM", "Conferences/2026/LLM")

    with open(PATH, "w", encoding="utf-8") as f:
        f.write(text)
    print("filled", len(ANSWERS), "checklist answers")


if __name__ == "__main__":
    main()
