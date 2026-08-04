# Transliteration Method Evaluation

**Question addressed:** we have four different methods that convert Sinhala
script into "Singlish" (Sinhala written using English letters). Which one
produces output closest to how real people actually write Singlish?

---

## 1. The four methods being compared

| Method | What it is |
|---|---|
| **Phonetic (in-house)** | A rule-based converter built for this project: each Sinhala letter/sound maps to a fixed English spelling |
| **Aksharamukha** | A general-purpose transliteration library, not built specifically for Sinhala |
| **uroman** | Another general-purpose "universal romanizer" tool |
| **Nisansa Sir's method** | Nisansa Sir's web application |

Example of the four methods on the same word (ආයුබෝවන් — a common greeting):

```
Sinhala:      ආයුබෝවන්
Phonetic:     aayuboowan
Aksharamukha: aayuboowan
uroman:       aayuboovan       <- uses "v" instead of "w"
Nisansa:      aayuboowan       <- after the v→w fix described in section 3
```

They mostly produce very similar results but differ consistently in small
spelling choices like this. The whole evaluation is really about figuring out
which of these small choices matches real human habit.

## 2. Getting a "ground truth" to compare against

There is no official standard for Singlish spelling, so to judge the methods
we needed real examples of Sinhala paired with Singlish that a human actually
typed. These came from the **Swa-bhasha Resource Hub** (a public research
dataset), via Kaggle and Hugging Face. Three datasets were used:

### Dataset A — Social media sentences (4,397 items)
Real YouTube comments. Authentic, informal, sometimes messy — the most
realistic test of "how do people actually type."

```
Sinhala: යකූ මේක හින්දි සින්දු කියනවනෙ අඩෙන්න.. මු ඉන්දියාවෙ හිටියනම්...
Human:   Yakoo meeka hindi sindu kiyanawane adenna.. Mu indiyawe hitiyanam...
```

### Dataset B — Swa-Bhasha word list (450,587 items)
Individual words. Importantly, each Sinhala word has **multiple accepted
Singlish spellings** attached (real spelling variation collected from
multiple people), not just one:

```
Sinhala: යෝග්‍යතම  ->  yogyathama, ygyathama, yogythama, yogyathma,
                        yogytham, ygythama, ... (16 accepted spellings total)
```

This is useful because it lets us score a method fairly: if it produces any
one of the 16 accepted spellings, that counts as correct, not just one exact
one.

### Dataset C — Augmented sentences (300,000-item sample)
A much larger sentence set, but machine-generated rather than typed by real
people. Used only as a secondary cross-check, since it partly reflects
whatever rules generated it rather than pure human habit. A random sample of
300k (out of 7.2M) was used instead of the full set — statistically this
gives virtually the same result at a fraction of the computation.

## 3. Method: run all four methods, then score them

For every Sinhala item in each dataset:
1. Run it through all four methods to get four Singlish guesses.
2. Compare each guess against the real human answer(s) using several metrics
   (below).
3. Average the scores across the whole dataset, per method.

### Nisansa Sir's Method
Because this method is a web application rather than a local library, every
item has to be sent over the internet. One word per request would have taken
about 19 hours for 450,000 words, so instead we send many words joined
together in a single request, which is about 78x faster and was verified to
give identical results to one-at-a-time requests. The full word list now
takes about an hour, and **all 450,587 words were processed**.

**The v→w fix.** The tool writes ව as `v`, while Sinhala speakers
overwhelmingly type `w`. Since that is a spelling convention rather than a
transliteration error, we rewrite every `v` as `w` in its output before
scoring, and all Nisansa numbers below are for the corrected version. The
rewrite is unambiguous on this data: `w` appears in only 159 of 449,117 raw
outputs (0.03%), so there is nothing for it to collide with.

```
Sinhala:  ආයුබෝවන්
Raw:      aayuboovan
Fixed:    aayuboowan     <- now identical to Phonetic
```

**One BUG of the tool.** It cannot romanize the letter **ඤ** (U+0DA4)
when that letter carries certain vowel signs — specifically when followed by
al-lakuna, ā, i or u. Such input comes back empty. We confirmed this by
testing directly: ඤ on its own works, so do ඤ+ඤ, ක+ඤ and ඤ+e, and so does the
neighbouring letter ඥ. So the tool's mapping table is simply missing those
combinations. This affects **1,470 of 450,587 words (0.33%)**.

Those words are excluded from **all four** methods, so every method is scored
on exactly the same 449,117 items. We considered filling the gaps with a
fallback instead, but the only sensible fallback is our own phonetic method,
and phonetic is one of the methods being compared — giving Nisansa its
competitor's answers would mean its score partly measures phonetic. This is a
genuine limitation of the tool, not a gap in our data, and is reported as one.

## 4. The evaluation metrics

All of these answer the same underlying question — "how different is the
machine's guess from the human's answer?" — just measured in different ways.
Several are needed because each is blind to a different kind of mistake.

**CER (Character Error Rate) — the primary metric.**
Counts how many single-letter changes (insert / delete / swap) are needed to
turn the guess into the correct answer, divided by the answer's length.

```
guess:  aayuboowan   (10 letters)
answer: ayubowan     (8 letters)
2 edits needed -> CER = 2 / 8 = 0.25  (i.e. 25% "character error")
```

Lower is better. This is the standard metric for this kind of task (also
used in speech-to-text and handwriting recognition).

**WER (Word Error Rate).**
Same idea as CER, but counting whole words instead of letters. Useful
because it shows whole-word mistakes, but it is "blind" to near-misses — a
one-letter-off word is scored as a complete miss, same as a totally
different word.

**chrF / chrF++ (character n-gram F-score).**
Instead of exact alignment, this checks how much overlap there is between
small chunks of letters in the guess vs. the answer (e.g. 2-letter and
3-letter sequences), then balances "how much of my guess was right" against
"how much of the answer did I capture." Scored 0–100, higher is better. It
is more forgiving than CER and is a standard metric for languages with rich
word structure — which is why we included it for Sinhala.

**BLEU.**
The standard metric from machine translation, based on overlapping
sequences of whole words. Scored 0–100, higher is better. We report it for
comparability with other research, but flagged it as the least meaningful
metric here, because it operates at the whole-word level and Singlish
variation mostly happens as small spelling changes within words, which BLEU
is not well suited to reward.

**Exact-match %.**
The simplest and strictest check: did the guess match one of the accepted
human answers exactly, character for character? A plain sanity check
alongside the softer metrics above.


## 5. Results

CER by dataset (lower is better; bold = best):

| Dataset | Items | Phonetic | Nisansa | Aksharamukha | uroman |
|---|---|---|---|---|---|
| Social media sentences | 4,397 | **0.182** | **0.182** | 0.191 | 0.228 |
| Swa-Bhasha words | 449,117 | **0.120** | **0.120** | 0.147 | 0.227 |
| Augmented sentences (sample) | 300,000 | **0.112** | not run | 0.139 | 0.210 |

Supporting metrics on the social media dataset (the most realistic test):

| Method | CER ↓ | WER ↓ | chrF ↑ | BLEU ↑ | Exact match % ↑ |
|---|---|---|---|---|---|
| **Phonetic** | **0.182** | **0.606** | **67.8** | **28.6** | **4.2%** |
| **Nisansa** | **0.182** | **0.606** | **67.8** | **28.6** | **4.2%** |
| Aksharamukha | 0.191 | 0.640 | 63.7 | 26.3 | 3.5% |
| uroman | 0.228 | 0.746 | 55.7 | 20.7 | 1.6% |

And on the word list, where the multiple accepted spellings make exact-match
meaningful:

| Method | CER ↓ | chrF ↑ | Exact match % ↑ |
|---|---|---|---|
| **Phonetic** | **0.120** | **78.8** | 33.3% |
| **Nisansa** | **0.120** | 78.7 | **33.4%** |
| Aksharamukha | 0.147 | 69.7 | 24.0% |
| uroman | 0.227 | 51.7 | 9.7% |

**Phonetic and Nisansa are tied.** Their confidence intervals overlap on both
datasets, so the ordering between them is not meaningful, and Nisansa is
fractionally ahead on exact matches on the word list. Aksharamukha and uroman
are genuinely behind: those differences are significant at p < 0.0001, and
effectively zero on the larger datasets.


## 6. Why the results come out this way: spelling conventions

Since the "relaxed" scoring showed all methods get the sounds roughly right,
the real difference is *spelling style*. We measured how often each method
and how often real humans use certain spelling choices:

| | uses "w" not "v" | doubles long vowels | keeps aspiration (th/kh/etc.) |
|---|---|---|---|
| **Real humans** | usually (80% w) | rarely | often |
| **Phonetic** | matches (100% w) | over-uses | matches closely |
| **Nisansa** | matches (100% w) | over-uses | matches closely |
| **Aksharamukha** | matches (100% w) | over-uses | drops it |
| **uroman** | opposite (100% v) | over-uses | drops it |

Phonetic and Nisansa have effectively the same profile, which is why they
score the same. Aksharamukha loses ground by dropping aspiration, and uroman
is last because it does that *and* writes `v` *and* over-doubles consonants.

The one weakness shared by *every* method is over-doubling long vowels
(e.g. "aayuboowan" instead of "ayubowan") — real people rarely double vowels
like this. This is a small, fixable issue: a simple post-processing step that
collapses doubled vowels would likely close much of the remaining gap for
every method.

## 7. Conclusion

**Phonetic and Nisansa's method are tied.** Once the v/w convention is
normalized they are statistically indistinguishable on both datasets, and
neither can be called the better romanizer. Aksharamukha and uroman are
measurably worse.

Choosing between the two tied methods therefore comes down to practical
differences, and here Nisansa's has some drawbacks:

- it **cannot romanize part of the alphabet** (the ඤ combinations above), so
  0.33% of the corpus has no output at all
- it needs the **v→w fix** applied to its output to match how people type
- it is a **web service**, so every item needs a network request, it can change
  or go offline, and the run cannot be reproduced offline

The phonetic method has none of those: it is local, deterministic, covers every
word, and matches human convention as-is. So it is the more convenient option
for the pipeline, but that is a practical judgement, not a quality one.
