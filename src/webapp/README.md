# Transliteration Inspector

A local Streamlit app for comparing Sinhala Unicode source text against its four
Romanized counterparts (`aksharamukha`, `nisansa_sirs_method`, `phonetic`, `uroman`).

## Install

```bash
pip install "streamlit>=1.32" pandas
```

## Run

From the **project root** (not from inside `src/webapp/`):

```bash
streamlit run src/webapp/app.py
```

The app opens at <http://localhost:8501>. It resolves `data/` relative to the project
root using its own file location, so the working directory does not matter — but the
`streamlit run` path above is the conventional one.

To use a different port:

```bash
streamlit run src/webapp/app.py --server.port 8600
```

## Expected data layout

```
data/
├── processed/
│   ├── sinhala_mmlu.jsonl
│   └── sold.jsonl
└── romanized/
    ├── aksharamukha/
    │   ├── sinhala_mmlu_romanized.jsonl
    │   └── sold_romanized.jsonl
    ├── nisansa_sirs_method/…
    ├── phonetic/…
    └── uroman/…
```

Records are joined across files on the `id` field. Ids present in a romanized file but
missing from `processed/` are still shown; ids missing from a romanized file are
reported in the **Overview** tab.

## What each control does

| Control | Effect |
| --- | --- |
| **Data directory** | Point the app at a different `data/` folder. |
| **Reload files from disk** | Clear the cache after regenerating a `.jsonl`. |
| **Dataset** | Switch between SinhalaMMLU and SOLD. |
| **Find by id** | Accepts `sold_0001`, `0001`, `1`, or any substring. Ambiguous input lists candidates. |
| **Record** | Dropdown of every id in the dataset. |
| **← Previous / Next →** | Step through records in file order. |
| **Compare against** | The method used as the diff baseline. |
| **Layout** | Stacked rows (better for long SOLD tweets) or a 2 × 2 grid. |
| **Highlight differences** | Marks tokens that differ from the baseline; underlines the exact characters that changed. |
| **Case-sensitive comparison** | Off by default, so `Vesak` and `vesak` count as the same token. |

## Views

**Compare tab**

1. Source text in Sinhala Unicode, with `label` / `domain` / `difficulty` chips.
2. The four romanizations, each with differences highlighted against the baseline.
3. **Word alignment** — one row per word position, one column per method, with a
   `Variants` count. Rows where the methods disagree are shaded. This is the fastest
   way to find systematic differences (for example `t` vs `th`, `v` vs `w`).
4. For SinhalaMMLU, the same treatment for each answer option, with the correct
   answer marked.
5. Raw JSON for the record from all five files.

**Overview tab**

- Per-method coverage and a list of any missing ids.
- A divergence score: mean pairwise token similarity across the four methods per
  record. Sort ascending to find the records where the methods disagree most — useful
  for sampling qualitative examples. Exportable as CSV.

## Adding a fifth method

Add the folder name to `METHODS` and a display name to `METHOD_LABELS` in `app.py`,
plus a colour in `METHOD_ACCENTS`. Everything else adapts automatically.

## Adding another dataset

Add an entry to `DATASETS`:

```python
"MyDataset": DatasetSpec(
    label="MyDataset",
    key="my_dataset",
    processed_file="my_dataset.jsonl",
    romanized_file="my_dataset_romanized.jsonl",
    kind="flat",   # or "mmlu" if it has an `options` array
),
```

## Note on Sinhala rendering

The app requests `Noto Sans Sinhala` with fallbacks to `Iskoola Pota` and `Nirmala UI`.
If Sinhala shows as boxes, install a Sinhala font locally (on Debian/Ubuntu:
`sudo apt install fonts-noto-sinhala`).