# Review document — GlobalSouthAI camera-ready

Internal read of `paper/globalsouthai/main.tex` before the camera-ready. Accepted 8 / 7 / 7,
all confidence 4. Line numbers are `main.tex` as submitted. Every number below was re-derived
from `results/intrinsic_evaluation/*.csv` and `paper/analysis/out/`.

## Overall

No reviewer makes a new experiment a condition of acceptance. The downstream results, the
scale reversal, the flattening, the SOLD metric result and the reproduction of the published
perplexities all hold unchanged. The problem is confined to §3, where the decomposition is
stated three different ways that are each defective, and two of three reviewers caught the
first of the three.

Both reviewers are right that the medians do not compose. On the published 24: total 8.29 bits
(312x), normaliser 4.37 (20.7x), per-byte loss 4.555 (23.5x). But 4.37 + 4.555 = 8.925, not
8.29, and 20.7 x 23.5 = 486, not 312. Equation 1 is exact per checkpoint (residual 5e-15);
three separately taken medians are not. Worth knowing why the guard rail missed it:
`verify_claims.py:307-312` checks all three medians individually, so each is true and the
composition implied by the prose is never tested. The comment at
`stats_robustness.py:193`, "the reported ratio factorises into these two", is the same error
inside the code.

Two further problems that nobody flagged and that matter more.

Dimensions: the loss term is (bytes per token) x (change in bits per byte), so its units are
bits per *token*. The "factor of 24" is therefore a per-token quantity, which is why it sits so
comfortably beside the per-token 312x. The actual per-byte figure is 2.16 bits per byte, a
factor of 4.5. So "a factor of 24 is a real rise in per-byte loss" (l69, l110) attaches a
per-token magnitude to a per-byte quantity.

Units: bits per byte does not remove the normaliser, it replaces a token-count normaliser with
a byte-count one. Exactly, and verified to 8.9e-16 across all 31 checkpoints,
bpb_r / bpb_u = (NLL_r / NLL_u) x (Bytes_u / Bytes_r), and that second factor has a median of
2.30 purely because Sinhala UTF-8 spends 2.65 bytes per character against 1.00 for Latin.
Byte counts are not matched across a pair. Word counts are, exactly, in all 31 pairs. So the
one encoding-free and tokenizer-free statement available is the total NLL ratio, and on the
published 24 that is 1.023 — the median checkpoint assigns 2.3% more loss to the identical
content, and 12 of the 24 assign *less*. Reviewer ghL4's point 2 is this, understated.

The consequence is that l192's "Almost exactly half of the headline is the unit of account" is
too modest rather than too strong. On the pool the claim is about, essentially all of it is.
This is a better paper, not a worse one: the strongest single illustration available is that
SmolLM3-3B carries the largest reported degradation in the pool at 769x while assigning 4%
*less* total loss to the Romanized text, whereas Gemma-2-9B, the only checkpoint genuinely
much worse on Romanized input at +46%, reports a middling 357x. Recommend rebuilding §3 around
the unit-free ratio, keeping Equation 1 as an accounting under UTF-8, and quoting the
normaliser's median *share* instead of a factor pair. Nothing downstream changes.

Various British and American spellings mixed throughout: normaliser (l427, l428, l459) against
normalizer (l181, l191, l328, l466); favour and favours in an otherwise -ize document.

## Abstract and Introduction

l68-69, l110-111: the factor pair, as above. Drop "exactly in two" — the identity is exact, the
split as quoted is not.
l71, l112: "first downstream evaluation of Sinhala script variation" should say the Romanized
side is automatically produced. Both ghL4 and fYs9 ask for this and it costs four words.
Abstract leads with the 0.22 slope over 10 heterogeneous checkpoints rather than 0.451 over 16
cells (item-weighted 0.476). sWb1 and fYs9 both flag it and sWb1 says outright that the
conservative number is strong enough. Give both. Note the abstract is at 197 of its 200-word
cap, so this is a swap, not an insert.

## Setup

l139, l764: "755,000 human-romanized reference items". The three corpora are 4,397 + 450,587 +
300,000 = 754,984, and the 300,000 are machine-augmented, so human-supplied is about 455,000.
ghL4 is right that the label overstates it.
l139: ghL4 asks whether our digraph conventions were developed on the Swa-bhasha data later
used to validate them. They were not, and the repository proves it rather than asserting it —
the mapping tables in `src/transliteration/phonetic.py` were committed 2026-07-15 and 07-17,
the Swa-bhasha pipeline landed 07-26, and the only later commit to that file is CLI plumbing.
One sentence. In the same place, volunteer the one real dependency we do have:
`src/method_evaluation/derive_nisansa_w.py` builds the `nisansa_w` comparator from a v-share
statistic measured on the same corpus used for scoring. It affects a baseline, not our method,
it is candid in the code and absent from the paper, and it is better disclosed than found.
l152: "six have a real signal on SOLD" is wrong. The screen returns five. Hormoz-8B is excluded
at a 90.2% single-option share against a >90% rule, that is, by two tenths of a point.

## Perplexity was measuring the tokenizer

Rebuild per Overall. l194's "2.14 bits per byte, a factor of 4.4" is the one statement in the
section that survives, but state it as 4.4x less probability per byte so it is not read beside
the per-token 312x.
l192 and l427 are the same quantity on two pools, 48% on the published 24 and 39% over all 31,
and currently read as though one supersedes the other. Give both with their pools.

## Model performance under Romanized input

Three different sets are all called "the competent checkpoints". The MMLU screen returns six,
the SOLD screen returns five, and the flattening regression at l236 uses all ten parseable
checkpoints and so does not depend on the competence screen at all. The slope is 0.221 on the
ten and 0.123 on the competent six. Label each cohort where it is used; this is ghL4's point 5
and it is correct.
l244: "Five of the six lose significantly" and "median keeps 45%" are computed over the six
*MMLU*-competent checkpoints, while the pooled SOLD gap (n = 12,500) and the appendix
attestation terciles use the five *SOLD*-competent ones. Same paragraph, two populations.
sWb1's two questions on the slope both have answers now. Item weighting is undefined at
checkpoint level because all ten score the same 6,879 items, so the weights are equal; and
dropping the extreme high and low Sinhala-script checkpoints gives 0.168, which moves away from
the cell-level 0.45 rather than toward it. Report both — the second is more persuasive
volunteered than found.
Competence sweep: cheap, CPU-only from the frozen CSVs, and it should be done, but the
thresholds are literals at `stats_extrinsic.py:130` and `:132` and want lifting into argparse
first. The stored screen statistics already give the answer: the MMLU six are identical at
alpha 0.001 and 0.01 and at both an 80% and a 90% degeneracy rule; alpha 0.05 adds
Zephyr-7B-beta at p = 0.045; a 95% rule adds SmolLM3-3B at 93.3%. SOLD is the sensitive one,
on Hormoz-8B's 0.2-point margin. Reporting this kills the "screen was tuned" reading on MMLU
outright and is honest about SOLD.
l230: "falling from 44.1% to 28.7% (95% CI 14.0 to 16.9)" — the interval is on the 15.5-point
difference, not on either level.

## Implications for evaluation

Well received, and sWb1 asks specifically that this section and the licensing decisions survive
into the camera-ready. No change beyond keeping the cross-references valid.

## Limitations

Content is right and all three reviewers said so. Placement is the problem: synthetic
romanization is the caveat two reviewers want prominent and it currently sits mid-paragraph in
a four-sentence run-on. Give it its own lead sentence.

## Appendices

table 16: the short version never says why only six checkpoints. The long version does
(`paper/main.tex:1468`, scored on CPU so the control did not compete with the main runs for GPU
time). Porting that sentence turns an apparent cherry-pick into a stated budget decision, and
all three reviewers raised this table's coverage.
The one new experiment worth running is extending that control to one or two checkpoints that
pass the competence screen. `run_synthetic_vs_human.py` already takes `--models` and
`--conditions ours`, and the unicode and human columns are already recorded, so the marginal
cost is 500 sentences in one condition. Llama-3.1-8B-Instruct or Qwen3.5-4B would close the
objection all three reviewers raise, that the control covers none of the checkpoints carrying
the downstream result. Nothing else in the review set is this cheap for what it buys.
sWb1's question on SOLD invalid handling has found a real error. `mcc_w`
(`stats_extrinsic.py:76-86`) is documented as folding invalid answers in as the wrong class,
but mechanically an invalid answer counts as a prediction of NOT, so on a gold-NOT item it
lands in TN and helps MCC, while the accuracy column maps invalid to a sentinel and always
counts it wrong. Invalid never exceeds 0.03% in the competent cohort so no reported number
moves, but the docstring and the appendix sentence are both wrong and the reviewer asked this
exact question.
Bits per word needs no new compute — it is already stored for all 31 checkpoints in all three
conditions in `out/intrinsic_pooled.csv`.
Attestation is not naturalness, and ghL4 makes the point well: our output scores more
lexicon-attested (88.6%) than the humans who typed the same sentences (84.2%). Let that pair do
the narrower job it can do.

## Requests to decline, with reasons

A human-typed Romanized subset at scale is out of scope for a camera-ready and is partly met by
the single-checkpoint control above; keep sWb1's framing of it as explicit future work.
The transliterate-back-to-Sinhala baseline fYs9 asks for is close to circular on our own
synthetic Romanized side, since it inverts our own grapheme map and would mostly recover the
Sinhala-script score while measuring our transliterator's injectivity rather than anything about
the models. It is informative only on human-typed input, and saying that is better than pleading
time. The full-set template sweep, fertility-controlled refits, within-family scaling and a
Romanized-adapted model all need new GPU runs; the Appendix B argument, that a paired comparison
needs a template which does not favour a script rather than an optimal one, already carries the
template point.

## Mechanics

`make_assets.py`, `check_paper.py` and `fill_checklist.py` are now in place, so the corrected
tables and figures can be regenerated rather than hand-edited. `paper/globalsouthai/README.md`
is still referenced by the top-level README and missing.
`check_paper.py` gates every number in `main.tex` against `acl_latex.tex`, so the long version
has to be corrected first or the new §3 values will need ALLOW entries. `verify_claims.py:307-312`
needs rewriting alongside, since the three medians it checks are exactly the ones being
withdrawn.
l27-34: `\sinword` and the `\ifsinhalafigs` switch are dead code; the two Sinhala examples use
`\includegraphics` directly.
Two bootstrap intervals exist for the same slope, [0.113, 0.567] from `stats_extrinsic` and
[0.113, 0.538] from `stats_robustness`, against 0.11 to 0.54 in the paper. Make one
authoritative.
Confirm the camera-ready page allowance before planning. The body is at the four-page mark and
the abstract is three words under its cap, so every addition above has to be paid for.
