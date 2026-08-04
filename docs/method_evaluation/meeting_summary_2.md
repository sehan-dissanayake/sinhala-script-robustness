# Transliteration Evaluation: Follow-up

*Second update. The first summary covered the four methods, the datasets and the
metrics; this one covers what changed since.*

Three things happened since the last meeting. We got Nisansa's method running
over the whole 450k word corpus instead of a small slice, we found out why it
kept failing, and we tested the v/w suggestion from the last meeting. The last
one changed our conclusion, so it is worth going through properly.

## 1. The rate limit that was never a rate limit

Last time, Nisansa's method was only evaluated on 25,000 words, because the web
endpoint kept refusing our requests. We had assumed we were being rate limited
after using it too heavily, and everything we tried fitted that story: it worked
fine for the first 25,000 words and then started failing about 30% of the time.

We were wrong, and it cost us a fair amount of time. What eventually gave it
away was a simple test. We took 60 batches that had failed and retried each one
six times. Not a single one ever succeeded on a retry. Every batch that worked,
worked on the first attempt.

That is not what throttling looks like. Throttling is transient, so retrying
eventually works. This was deterministic, which meant the *content* of the
request was the problem, not the timing or the volume. So we took a failing batch
of 250 words, split it in half, tested each half, and kept splitting until one
word was left.

## 2. The actual bug

The endpoint cannot romanize the letter **ඤ** (U+0DA4) when it carries certain
vowel signs. We narrowed it down by probing directly:

| Input | Result |
|---|---|
| ඤ on its own | works |
| ඤ + ඤ, ක + ඤ, ඤ + ක, ඤ + e | works |
| ඤ followed by al-lakuna, ā, i or u | **fails** |
| ඥ (U+0DA5, the neighbouring letter) | works |

So it is not the letter itself. The tool's mapping table is missing those
specific combinations, and when it hits one it returns an empty result instead of
an error. Because one bad word takes down the whole request it travels in, and
because a 250-word batch has roughly a 30 to 47% chance of containing one, it
looked exactly like a server refusing traffic.

1,470 of the 450,587 words (0.33%) are affected, and they cluster
alphabetically. That is why one of our runs appeared to fail from its very first
request: it happened to start inside a cluster.

Once we filtered those words out client-side and stopped retrying (retrying was
provably useless), throughput went from about 3 words per second to about 133.
The full corpus finished in roughly an hour instead of the 19 hours we had
originally estimated. **449,117 words romanized, 99.7% coverage.**

This is worth reporting to Dr Nisansa. It is a reproducible bug with a one-line
test case: submit ඤා and the output comes back empty.

## 3. What we did with the 1,470 words

We excluded them from **all** methods, so every method is scored on exactly the
same 449,117 rows.

We considered filling the gaps with a rule-based fallback instead, but the only
sensible fallback available is our own phonetic method, and phonetic is one of
the methods being compared. Lending Nisansa the output of its competitor would
mean its score partly measures phonetic. The effect would have been tiny at 0.33%
of items, but it is the wrong thing to do, and a reviewer would be right to
question it.

The important point is that this is not a hole in our data. It is a real
limitation of the tool, and it is reported as one.

## 4. The v/w test, and why it changed our conclusion

Last meeting we explained Nisansa's weaker score mainly by the v/w convention:
it writes ව as `v`, while Sinhala speakers overwhelmingly type `w`. The
suggestion was to rewrite the `v` as `w` and score it again. We did exactly
that, on the corrected version only.

It needed no refetching, since it is a post-process of results we already had.
The rewrite is also unambiguous on this data: `w` appears in only 159 of 449,117
Nisansa outputs, so there was nothing for a v to w mapping to collide with.

| Corpus | Nisansa as published | Nisansa with v→w | Phonetic |
|---|---|---|---|
| Social media (4,397) | 0.197 | **0.182** | 0.182 |
| Swa-Bhasha words (449,117) | 0.163 | **0.120** | 0.120 |

The gap closes completely. The confidence intervals now overlap phonetic's on
both corpora, so the two are a statistical tie, and the v→w version is even
fractionally ahead on exact matches (33.4% against 33.3% on words).

This is consistent with something already in our earlier numbers that we had not
pushed on: the "relaxed" metric, which normalises spelling style before scoring,
had already shown the two methods at identical CER to four decimal places.

**So the conclusion has to be stated differently now.** We can no longer say
phonetic transliterates better than Nisansa's method, because it does not.
Nisansa is not a worse romanizer. It writes `v`, and Sinhala speakers type `w`.
Once that single convention is normalised, the two are equivalent.

Phonetic is still our recommendation, but on practical grounds rather than
quality:

- it already matches human convention, with no post-processing needed
- it runs locally and deterministically, with no network dependency
- it covers the whole corpus, including the words Nisansa cannot handle
- anyone can reproduce the entire run offline

## 5. Final results

Character Error Rate, lower is better. Scored on identical items, case folded.

| Method | Social media | Swa-Bhasha words | Augmented (300k) |
|---|---|---|---|
| Phonetic | **0.182** | **0.120** | **0.112** |
| Nisansa + v→w | 0.182 | 0.120 | not run |
| Aksharamukha | 0.191 | 0.147 | 0.139 |
| Nisansa as published | 0.197 | 0.163 | not run |
| uroman | 0.228 | 0.227 | 0.210 |

Phonetic and Nisansa+v→w are tied at the top. Aksharamukha is clearly behind,
mainly because it drops aspiration. uroman is last on every corpus.

One more correction we made to our own method: with 449,117 items, a CER
difference of 0.0001 comes out "statistically significant" while being
meaningless. The report now decides ties from the confidence intervals rather
than declaring a winner on any difference at all.

## 6. Where things stand

The transliteration comparison is finished. Nisansa's method is now evaluated on
the full corpus rather than a biased 25,000-word slice, so the sampling caveat
from last time is gone.

Remaining item, unchanged from last meeting: every method over-doubles long
vowels compared to how people actually type (about 0.8 per token against a human
rate of 0.12). Collapsing `aa/ee/ii/oo/uu` in post-processing would close roughly
half the remaining error for all of them, and it is a small change.

---

*Full tables, statistical tests and charts:* `docs/method_evaluation/README.md`
*and* `results/method_evaluation/`.
