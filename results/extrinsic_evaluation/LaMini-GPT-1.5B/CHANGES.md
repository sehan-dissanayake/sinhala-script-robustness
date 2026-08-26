# Fixes Applied — LaMini-GPT-1.5B Evaluation Notebook

## Root Cause

`LaMini-GPT-1.5B` is a fine-tuned `gpt2-xl`, and every GPT-2 size has a **position
embedding table of exactly 1024 slots** (`n_positions` / `max_position_embeddings`
= 1024). The notebook had:

```python
MAX_INPUT_TOKENS = 4096
```

This only controls tokenizer truncation — it does not reflect what the model can
actually handle. Any prompt tokenizing to somewhere between 1024 and 4096 tokens
was passed through **untruncated**, generated `position_ids >= 1024`, and the
position-embedding lookup (`vectorized_gather_kernel`) read out of bounds on the
GPU, causing:

```
AcceleratorError: CUDA error: device-side assert triggered
```

This crashed ~3% into the Sinhala MMLU run rather than immediately, because it
only triggered once a prompt happened to be long enough. Sinhala text inflates
heavily under GPT-2's English-centric BPE vocabulary (often several tokens per
character), so a question + 4 options can cross 1024 tokens even when it looks
short in characters.

**Additional wrinkle:** once a CUDA device-side assert fires, the whole CUDA
context is poisoned — every subsequent CUDA call in that process fails,
including `torch.cuda.empty_cache()` inside the existing `except` block (visible
as the second, nested exception in the original traceback). This means the
existing per-item error handling could never have protected the run; the only
real fix is preventing the overflow from happening at all.

---

## Change 1 — Dynamic input-token cap (Cell: "Load Model & Tokenizer")

Added logic, run right after the model loads, that reads the model's *actual*
context limit and clamps `MAX_INPUT_TOKENS` to it:

```python
_model_ctx = (
    getattr(model.config, "max_position_embeddings", None)
    or getattr(model.config, "n_positions", None)
    or getattr(tokenizer, "model_max_length", None)
)
if not _model_ctx or _model_ctx > 100_000:  # tokenizer placeholder is often 1e30
    _model_ctx = 1024

_SAFETY_MARGIN = 8
MAX_INPUT_TOKENS = max(1, min(MAX_INPUT_TOKENS, _model_ctx - MAX_NEW_TOKENS - _SAFETY_MARGIN))
tokenizer.truncation_side = "left"
```

- For `LaMini-GPT-1.5B` this resolves to `1024 - 40 - 8 = 976`.
- It's computed dynamically (not hard-coded to 1024) so the same notebook stays
  correct if reused later for a model with a different/larger context window.
- `truncation_side = "left"` is also set: the default ("right") would have cut
  off the trailing `Answer:` cue and broken the extraction regex. Truncating
  from the left drops the least-important leading boilerplate first.

## Change 2 — Config cell comment update

Updated the comment on `MAX_INPUT_TOKENS = 4096` to clarify it's now just an
upper-bound safety cap, and that the real value used at runtime is computed
after the model loads (see Change 1).

## Change 3 — Tightened `T1_direct` prompt (Cell: "Prompt Templates")

`build_mcq_prompt_t1` and `build_sold_prompt_t1` were shortened and the
"answer only" instruction was made more prominent and redundant:

- Removed redundant boilerplate sentences to reduce token usage per prompt.
- The "reply with ONLY the number / ONLY 'NOT' or 'OFF' — no words, no
  explanation" instruction now appears **twice**: once up front, and again
  right at the answer slot itself (e.g. `Answer (number 1/2/3/4 only):`).
- This makes the instruction survive even if left-truncation ever trims the
  front of a very long prompt.

**Before:**
```python
f"This is a multiple-choice question related to the {_humanize_domain(subject)}. "
f"Choose the correct or most appropriate answer from answers {valid_range} for the "
f"following question. {NO_REPEAT_INSTRUCTION} Respond with only the number "
f"({valid_range}) and nothing else.\n"
f"Question: {question}\n{options_str}\nAnswer:"
```

**After:**
```python
f"Multiple-choice question ({_humanize_domain(subject)}). "
f"Reply with ONLY the number ({valid_range}) -- no words, no explanation.\n"
f"Question: {question}\n{options_str}\nAnswer (number {valid_range} only):"
```

(Same pattern applied to the no-subject MCQ variant and to `build_sold_prompt_t1`.)

---

## Net Effect

- No prompt can generate a `position_id` beyond what the model architecture
  supports, so the `device-side assert` cannot recur.
- If a prompt is unusually long, it's truncated from the least useful end
  (the front) rather than losing the `Answer:` cue.
- The active `T1_direct` template is shorter (saves tokens) and more robust
  about enforcing "answer only" output, even under truncation.
