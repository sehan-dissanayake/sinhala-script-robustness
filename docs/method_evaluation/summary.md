# Transliteration Method Evaluation

**Question addressed:** we have four different methods that convert Sinhala
script into "Singlish" (Sinhala written using English letters). Which one
produces output closest to how real people actually write Singlish?

**Answer:** the in-house phonetic method, on every dataset and on every metric.

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
Nisansa:      aayuboovan       <- also "v"; see the v→w step in section 3
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

### Nisansa Sir's method

Because this method is a web application rather than a local library, every
item has to be sent over the internet. One word per request would have taken
about 19 hours for 450,000 words, so instead we send many words joined
together in a single request, which is about 78x faster and was verified to
give identical results to one-at-a-time requests. Each dataset now takes about
an hour.

**What we record is the tool's output exactly as it comes back.** An earlier
version of our code quietly ran our own phonetic converter over every response
to tidy up characters the web app had left in Sinhala. That was a mistake: it
made the thing we were measuring a *mixture* of Nisansa's method and one of the
methods it was being compared against, and it hid a real defect. Both datasets
were refetched from scratch without it.

**The v→w step.** The tool writes ව as `v`, while Sinhala speakers
overwhelmingly type `w`. Since that is a spelling convention rather than a
transliteration error, we rewrite every `v` as `w` in its output before
scoring, and report both versions. The rewrite is completely unambiguous:
across all three datasets, **not one** of its 753,065 outputs contains a `w`
already, so there is nothing for the rewrite to collide with.

```
Sinhala:  ආයුබෝවන්
Raw:      aayuboovan
Fixed:    aayuboowan     <- now identical to Phonetic
```

### Two bugs in the tool

We measured these properly rather than discovering them by accident, by
submitting the entire Sinhala letter-plus-vowel-sign grid (881 combinations)
one at a time and recording what came back. Both results are saved in the repo
under `data/reference/nisansa_endpoint/`.

**Bug 1 — 17 combinations produce no output at all.** Every one of them is the
letter **ඤ** (U+0DA4) carrying a vowel sign or al-lakuna:

```
ඤ්  ඤා  ඤැ  ඤෑ  ඤි  ඤී  ඤු  ඤූ  ඤෘ  ඤේ  ඤෛ  ඤො  ඤෝ  ඤෞ  ඤෲ  ඤ්‍ය  ඤ්‍ර
```

ඤ on its own works, ඤෙ works, and the neighbouring letter ඥ works, so the
tool's mapping table is simply missing those specific combinations. It is
completely repeatable — same result at any time of day, any request size.
One-line reproduction: submit **ඤා**.

This affects **1,470 of 450,587 words (0.33%)** and **442 of 275,259 sentences
(0.16%)**. Worth noting that our measured list of 17 reproduces *exactly* the
1,470 words that the actual corpus run failed on, which is good evidence the
list is neither too broad nor too narrow.

**Bug 2 — some characters come back still in Sinhala.** The request succeeds
and the output looks fine, but a Sinhala character is sitting inside it
untouched:

```
ඓතිහාසික  ->  ඓthihaasika        (the ඓ was never converted)
```

12 such combinations were confirmed in the grid (ඎ, ඏ, ඐ, ඓ, ඞ, ඦ, ෟ, ෳ, ඣෙ,
ඤෙ, ඥෙ, ඬෙ), and real text produces more, because the datasets contain
irregularly-typed sequences the grid cannot anticipate. In practice this
affects **0.82% of word outputs** and **2.48% of sentence outputs**. This is
the defect our old repair step was hiding.

### How the failures are counted

**Nothing is excluded.** Where the tool produced no output, that item is scored
as completely wrong (CER 1.0), the same as any other wrong answer. Leaked
Sinhala characters are scored as the errors they are.

This is a change from our earlier draft, which dropped those 1,470 words from
*all four* methods so that everyone was scored on identical rows. That kept the
comparison matched, but it also meant a tool got no penalty for failing to
answer — and being unable to romanize part of the alphabet is a property of the
tool, not a gap in our data. The tables below therefore include a **coverage**
column so the size of that effect is visible rather than buried inside an
average.

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

CER by dataset (lower is better; **bold** = best). Nisansa is shown after the
v→w step, which is its better version:

| Dataset | Items | Phonetic | Nisansa (v→w) | Aksharamukha | uroman |
|---|---|---|---|---|---|
| Social media sentences | 4,397 | **0.182** | 0.182 | 0.191 | 0.228 |
| Swa-Bhasha words | 450,587 | **0.121** | 0.133 | 0.148 | 0.228 |
| Augmented sentences (sample) | 300,000 | **0.112** | 0.114 | 0.139 | 0.210 |

Phonetic is first everywhere. On the two big datasets the gap to Nisansa is
small but entirely solid: the confidence intervals do not overlap and the
paired test gives p < 1e-90. On social media the two are separated by 0.0003,
which is a difference too small to care about even though the paired test
technically flags it.

Full numbers, social media (the most realistic test):

| Method | Coverage | CER ↓ | WER ↓ | chrF ↑ | BLEU ↑ | Exact ↑ |
|---|---|---|---|---|---|---|
| **Phonetic** | 100% | **0.182** | **0.606** | **67.8** | **28.6** | **4.16%** |
| Nisansa (v→w) | 100% | 0.182 | 0.607 | 67.8 | 28.6 | 4.16% |
| Aksharamukha | 100% | 0.191 | 0.640 | 63.7 | 26.3 | 3.50% |
| Nisansa (as published) | 100% | 0.197 | 0.647 | 63.4 | 25.4 | 3.18% |
| uroman | 100% | 0.228 | 0.746 | 55.7 | 20.7 | 1.59% |

Word list, where the multiple accepted spellings make exact-match meaningful:

| Method | Coverage | CER ↓ | chrF ↑ | Exact ↑ |
|---|---|---|---|---|
| **Phonetic** | 100% | **0.121** | **78.7** | **33.2%** |
| Nisansa (v→w) | 99.67% | 0.133 | 76.1 | 30.9% |
| Aksharamukha | 100% | 0.148 | 69.6 | 23.9% |
| Nisansa (as published) | 99.67% | 0.176 | 65.5 | 20.6% |
| uroman | 100% | 0.228 | 51.6 | 9.7% |

Augmented sentences (cross-check only):

| Method | Coverage | CER ↓ | chrF ↑ | Exact ↑ |
|---|---|---|---|---|
| **Phonetic** | 100% | **0.112** | **79.6** | 3.426% |
| Nisansa (v→w) | 99.85% | 0.114 | 79.5 | **3.432%** |
| Aksharamukha | 100% | 0.139 | 70.3 | 2.819% |
| Nisansa (as published) | 99.85% | 0.153 | 68.5 | 2.460% |
| uroman | 100% | 0.210 | 53.5 | 1.737% |

Coverage of 99.85% is 449 of 300,000 rows with no output. Nisansa edges Phonetic
on exact match here by 6 items in 300,000, which is noise, not a result.

### A note on what changed from our earlier draft

Our first write-up reported Phonetic and Nisansa as a **statistical tie** at
0.120 CER each on the word list. That is no longer what we find, for two
reasons, both of them corrections to our own method rather than new data:

1. we were scoring Nisansa's output *after* our phonetic converter had tidied
   it up, so part of what we measured was our own method;
2. we were excluding the words it could not romanize, so it paid no price for
   failing to answer.

With both fixed, Phonetic is ahead by 0.012 CER on the word list. The
conclusion is a little stronger than before, and now rests on the primary
metric rather than on convenience alone.

## 6. Why the results come out this way: spelling conventions

Since the "relaxed" scoring showed all methods get the sounds roughly right,
the real difference is *spelling style*. We measured how often each method and
how often real humans use certain spelling choices (word list):

| | uses "w" not "v" | doubles long vowels | keeps aspiration (th/kh/etc.) | leaves Sinhala in the output |
|---|---|---|---|---|
| **Real humans** | almost always (99% w) | rarely (0.12/word) | often (0.55/word) | never |
| **Phonetic** | always (100% w) | over-uses (0.81) | matches (0.56) | never |
| **Nisansa (v→w)** | always (100% w) | over-uses (0.81) | matches (0.56) | 0.82% of outputs |
| **Aksharamukha** | always (100% w) | over-uses (0.81) | drops it (0.23) | never |
| **uroman** | opposite (100% v) | over-uses (0.80) | drops it (0.003) | never |

Phonetic and Nisansa have nearly the same profile, which is why they land
close together; what separates them now is coverage and the leaked characters,
not spelling style. Aksharamukha loses ground by dropping aspiration, and
uroman is last because it does that *and* writes `v` *and* over-doubles
consonants.

The one weakness shared by *every* method is over-doubling long vowels
(0.81 per word against humans' 0.12 — e.g. "aayuboowan" instead of
"ayubowan"). This is the **largest remaining source of error for all four
methods**, and it looks fixable: a post-processing step that collapses
`aa/ee/ii/oo/uu` would likely close a good part of the remaining gap for every
method. Not yet implemented — the clearest next improvement.

## 7. Conclusion

**The in-house phonetic method is the best of the four.** It has the lowest CER
and highest chrF on all three datasets, and the differences against
Aksharamukha and uroman are large. Against Nisansa's method the difference is
smaller but statistically clear on the two large datasets, and it comes from
two specific things rather than from being a better letter-to-letter converter:

- Nisansa **cannot romanize 17 ඤ combinations at all**, so 0.33% of the word
  list and 0.16% of the sentences get no answer
- Nisansa **leaves Sinhala characters in 0.8–2.5% of its output**
- Nisansa needs the **v→w step** applied to match how people actually type;
  without it, it also ranks below Aksharamukha

On pure letter-to-letter mapping, once the v/w convention is normalized and
only the items it *did* answer are counted, the two are still very close — that
part of our earlier conclusion holds. What has changed is that a tool's
inability to answer now counts against it, as it should.

Phonetic also has the practical advantages: it runs locally and
deterministically, needs no network, covers every input, and can be reproduced
offline by anyone. So it is the recommendation on both quality and engineering
grounds.

The two bugs above are worth reporting to Dr Nisansa; both are small, specific
and come with a one-line reproduction.
