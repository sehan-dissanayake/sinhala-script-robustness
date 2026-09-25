# Review document — GlobalSouthAI @ NeurIPS 2026 camera-ready

Internal critical read of `paper/globalsouthai/main.tex` (accepted: 8 / 7 / 7, all confidence 4)
ahead of the camera-ready. Reviewer claims have been re-derived from the frozen outputs in
`paper/analysis/out/`; line numbers are `main.tex` as submitted. Tags: **[B]** blocking,
**[F]** fix, **[C]** check/decide, **[D]** decline with a stated reason.

## Overall

No reviewer asks for a new experiment as a condition of acceptance. One new experiment is
worth doing anyway (see Appendices). The two substantive problems are both about how §3
states its result, not about whether it holds.

**[B] The 21× / 24× split does not compose, and two reviewers caught it independently.**
Verified on `out/ppl_decomposition.csv` for the published 24 checkpoints: median total gap
8.29 bits (313×), median normalizer 4.37 bits (20.7×), median per-byte loss 4.555 bits
(23.5×). But 4.37 + 4.555 = 8.925, not 8.29, and 20.7 × 23.5 ≈ 486. Equation 1 is exact
*per checkpoint* (identity error 5e-15); three separately taken medians are not. Reviewer
ghL4's proposed repair works — aggregating in log space with arithmetic means gives
14.76 × 22.75 = 335.8× exactly.

**[B] The split *share* is unit-dependent, which is worse than ghL4's phrasing of it.** ghL4
calls bits per byte "not a unique division" between artifact and real loss. It is sharper than
that. The identity has the form (loss per unit) × (units per token) for *any* unit, so it can
be rewritten over words — exact there too (error 3.6e-15) — and under the word unit the median
normalizer share is **94%** with a mean real-loss factor of **1.04**, against 39–48% and ~23×
under bytes. The "roughly half the headline is the unit of account" framing is therefore itself
an artifact of choosing bytes, and it collides with ghL4 #2, which asks us to promote bits per
word to the principal cross-script estimate. **These two asks cannot be answered
independently.** Recommended line: keep the decomposition as an accounting under UTF-8, state
the normalizer's median *share* instead of a factor pair, and lead the real-degradation claim
with the two unit-clean numbers we already have — 2.14 bits per byte (4.4×) and 1.11 bits per
word (2.2×). The word framing halves the headline real loss, so this is a framing decision, not
a mechanical edit. **[C]**

Minor throughout: `normaliser` (l427, l428, l459) vs `normalizer` (l181, l191, l328, l466);
`favour`/`favours` in an otherwise -ize document.

## Abstract and Introduction

- l68–69, l110–111: the factor pair. Drop "exactly in two" — the identity is exact, the quoted
  split is not. **[B]**
- l71, l112 "first downstream evaluation of Sinhala script variation": ghL4 #3 and fYs9 both
  ask the novelty claim to name the Romanized side as automatic. Cheapest honest fix is
  "…with automatically Romanized inputs", in both places. **[F]**
- Abstract leads with the 0.22 slope (n = 10 heterogeneous checkpoints) rather than 0.451
  (n = 16 cells, item-weighted 0.476). sWb1 #2 and fYs9 both flag this; sWb1 is explicit that
  the conservative number is strong enough. Give both or lead with the cell-level fit. **[F]**
  Cost note: the abstract is 197 words against the 200-word cap the earlier commit enforced,
  so this is a swap, not an insert.

## §2 Setup

- l139, l764 "755,000 human-romanized reference items": 4,397 + 450,587 + 300,000 = 754,984,
  of which the 300,000 are machine-augmented. Human-supplied is ~455,000. ghL4 #4 is correct;
  say "755,000 reference items, 455,000 of them human-supplied". **[F]**
- ghL4 #4 also asks whether our conventions were developed on the Swa-bhasha data later used
  to validate them. They were not, and we can prove it rather than assert it: the mapping
  tables in `src/transliteration/phonetic.py` were committed 2026-07-15/17, the Swa-bhasha
  reference pipeline landed 2026-07-26, and the only subsequent commit to that file is CLI
  plumbing. One sentence. **[F]**
  In the same breath, disclose the one real dependency we do have:
  `src/method_evaluation/derive_nisansa_w.py` builds the `nisansa_w` comparator from a
  v-share statistic measured on the same Swa-bhasha corpus used for scoring. It is candid in
  the code and absent from the paper. It affects a baseline, not our method, but it is exactly
  what ghL4 is asking about and is better volunteered. **[F]**
- l152 "six have a real signal on SOLD" is wrong. The screen yields **five** on SOLD. **[B]**

## §3 Perplexity was measuring the tokenizer

- l191–192 as above. l192 "Almost exactly half" is the 48% median normalizer share on the
  published 24 and is correct; l427's 39% is the same quantity over all 31. Currently they read
  as if one supersedes the other. State both as shares, with their pools. **[F]**
- Keep l194's "2.14 bits per byte, a factor of 4.4" — it is the one statement in §3 that is
  unit-clean and survives everything above.

## §4 Model performance under Romanized input

- **Cohorts are inconsistent, and ghL4 #5 is right.** Three different sets are all called "the
  competent checkpoints": the MMLU screen gives six; the SOLD screen gives five (Hormoz-8B is
  excluded at a 90.2% single-option share against a `> 90%` rule — by two tenths of a point);
  the flattening regression at l236 uses all **ten** parseable checkpoints and therefore does
  not depend on the competence screen at all. Verified: slope is 0.221 on the ten and 0.123 on
  the competent six. Label every cohort at the point of use. **[B]**
- l244 "Five of the six lose significantly" and "median keeps 45%" are computed over the six
  *MMLU*-competent checkpoints, while the pooled SOLD gap (n = 12,500) and the appendix
  attestation terciles use the five *SOLD*-competent ones. Same sentence region, two
  populations. **[B]**
- sWb1's two questions on the slope have answers we can give now: item weighting is undefined
  at checkpoint level, because all ten checkpoints score the same 6,879 items, so the weights
  are equal; and dropping the extreme low and high Sinhala-script checkpoints gives 0.168 —
  it moves *away* from 0.45, not toward it. Report both. Volunteering the second is more
  persuasive than leaving it to be found. **[F]**
- **Competence-screen sensitivity (sWb1 #4) is cheap and should be done.** CPU-only from
  frozen per-item CSVs, but the thresholds are hard-coded literals at
  `paper/analysis/stats_extrinsic.py:130` and `:132`; lift them into `argparse` first.
  Precomputed from the stored screen statistics: the MMLU six are **identical** at α = 0.001,
  0.01 and at both an 80% and a 90% degeneracy rule; α = 0.05 adds Zephyr-7B-beta
  (p = 0.045); a 95% rule adds SmolLM3-3B (93.3%). SOLD is the sensitive one, on Hormoz-8B's
  0.2-point margin. A short sweep kills the "the screen was tuned" reading outright on MMLU
  and is honest about SOLD. **[F]**
- l230: "Qwen3.5-9B falling from 44.1% to 28.7% (95% CI 14.0 to 16.9)" — the interval is on
  the 15.5-point difference, not on either level. Reword. **[F]**

## §5 Implications

Well received; sWb1 explicitly asks that this section and the licensing decisions survive into
the camera-ready. No change beyond keeping the cross-references valid.

## §6 Limitations

Content is right and all three reviewers said so. The problem is placement: synthetic
romanization is the caveat two reviewers want *prominent*, and it currently sits mid-paragraph
in a four-sentence run-on. Give it its own lead sentence. **[F]**

## Appendices

- **Table 16 never says why only six checkpoints.** The ACL version does (`paper/main.tex:1468`:
  scored on CPU so the control did not compete with the main runs for GPU time). Porting that
  one sentence turns an apparent cherry-pick into a stated budget decision. All three reviewers
  raised the coverage of this table. **[F]**
- **The one new experiment worth running.** Extend the ours-vs-human bits-per-byte control to
  one or two *competent* checkpoints. `run_synthetic_vs_human.py` already takes `--models` and
  `--conditions ours`, and the unicode/human columns for those checkpoints are already
  recorded, so the marginal cost is 500 sentences in one condition per checkpoint.
  Llama-3.1-8B-Instruct or Qwen3.5-4B would close the objection — raised by sWb1 #3, ghL4 #3
  and fYs9 — that the control covers none of the checkpoints carrying the downstream result.
  Nothing else in the review set is this cheap relative to what it buys. **[C] do if the
  timeline allows**
- **sWb1 Q4 has found a real wording error.** `mcc_w` (`stats_extrinsic.py:76–86`) is documented
  as folding invalid answers in as the wrong class. Mechanically an invalid answer is counted as
  a prediction of `NOT`, so on a gold-`NOT` item it lands in TN and *helps* MCC; the SOLD
  accuracy column maps invalid to a sentinel and always counts it wrong. Invalid rates never
  exceed 0.03% in the competent cohort so no reported number moves, but both the docstring and
  the appendix sentence are wrong as written, and the reviewer asked this exact question. Fix
  the wording; a one-line "MCC with invalid dropped" robustness note would settle it. **[F]**
- ghL4 #2's bits-per-word promotion needs no compute — BPW is already stored for all 31
  checkpoints in all three conditions in `out/intrinsic_pooled.csv`. Decide the framing first
  (see Overall). **[C]**
- Attestation is not naturalness, and ghL4 makes the point well: our deterministic output
  scores *more* lexicon-attested (88.6%) than the humans who typed the same sentences (84.2%).
  Stop offering that pair as evidence of naturalness and let it do the narrower job it can do.
  **[F]**

## Declines, each with a reason worth stating

- **[D] Human-typed Romanized subset at scale** (all three reviewers). Out of scope for a
  camera-ready; partially met by the single-checkpoint control above. Keep sWb1's framing —
  it converts our largest limitation into a measurement — as explicit future work.
- **[D] Transliterate-back-to-Sinhala baseline** (fYs9). On our own synthetic Romanized side
  this is close to circular: it inverts our own grapheme map, so it would largely recover the
  Sinhala-script score and would measure our transliterator's injectivity rather than anything
  about the models. It is only informative on human-typed input. Say that in one sentence
  rather than pleading time.
- **[D] Full-set prompt-template sweep, tokenizer-fertility-controlled refits, within-family
  scaling, a Romanized-adapted model** (fYs9). All need new GPU runs. The Appendix B argument —
  that a paired comparison needs a template that does not favour a script, not an optimal one,
  evidenced by ≤0.03% invalid rates in both conditions — already carries the template point.

## Build and repo blockers for the mechanics

- `paper/globalsouthai/make_assets.py` and `check_paper.py` are documented in the top-level
  README but **are not in the repo**. They are what regenerates this paper's tables and figures
  at NeurIPS geometry and guards the page budget. Every fix above changes a rendered number, so
  restore them before touching a table. `paper/globalsouthai/README.md` is also referenced and
  missing. **[B]**
- `\sinword` and the `\ifsinhalafigs` switch (l27–34) are dead code; the two Sinhala examples use
  `\includegraphics` directly. Remove. **[F]**
- Two bootstrap CIs exist for the same slope — `stats_extrinsic` gives [0.113, 0.567],
  `stats_robustness` [0.113, 0.538], and the paper quotes 0.11–0.54. Make one script
  authoritative. **[F]**
- Re-run `verify_claims.py` after every edit. Both 39% and 48% are live numbers, so whichever
  wording we adopt has to be registered there.
- **Confirm the camera-ready page allowance before planning.** The abstract is at 197 of 200
  words and the body is at the four-page mark, so every addition above has to be paid for out
  of existing text.

## Triage

**Must fix (correctness):** the factor pair in abstract/intro/§3; the byte-vs-word framing
decision; "six have a real signal on SOLD"; the three unlabelled cohorts in §4; the MCC invalid
wording; the missing `make_assets.py` / `check_paper.py`.

**Should fix (pre-empts the obvious objection):** both slopes in the abstract; the competence
sweep; the "automatically Romanized" qualifier; the 755k composition and the transliterator
independence sentence; the Table 16 CPU rationale; synthetic romanization promoted in §6.

**Optional:** the ours-vs-human control on one competent checkpoint; MCC with invalid dropped;
figure and table legibility (sWb1's Figure 1(c) annotation and the Table 5 reordering callout).
