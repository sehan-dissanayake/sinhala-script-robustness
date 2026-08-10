"""
Sinhala Script Robustness — Transliteration Inspector
====================================================

A local Streamlit app to visually compare Sinhala Unicode source text against
its four Romanized ("Singlish") counterparts.

Run from the project root:

    streamlit run src/webapp/app.py

Expected data layout (relative to the project root):

    data/processed/sinhala_mmlu.jsonl
    data/processed/sold.jsonl
    data/romanized/<method>/sinhala_mmlu_romanized.jsonl
    data/romanized/<method>/sold_romanized.jsonl

where <method> is one of: aksharamukha, nisansa_sirs_method, phonetic, uroman.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from statistics import mean
from typing import Any

import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# app.py lives at <project_root>/src/webapp/app.py  ->  parents[2] is the root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

METHODS: tuple[str, ...] = (
    "aksharamukha",
    "nisansa_sirs_method",
    "phonetic",
    "uroman",
)

METHOD_LABELS: dict[str, str] = {
    "aksharamukha": "Aksharamukha",
    "nisansa_sirs_method": "Nisansa Sir's method",
    "phonetic": "Phonetic",
    "uroman": "uroman",
}

# Muted, colour-blind-safe accents. Used only as a 3px rail on each card so the
# text itself stays black-on-background and remains easy to read.
METHOD_ACCENTS: dict[str, str] = {
    "aksharamukha": "#3d7ea6",
    "nisansa_sirs_method": "#8a6bbf",
    "phonetic": "#2e8b6f",
    "uroman": "#c07830",
}


@dataclass(frozen=True)
class DatasetSpec:
    label: str
    key: str
    processed_file: str
    romanized_file: str
    kind: str  # "mmlu" (question + options) or "flat" (single text)


DATASETS: dict[str, DatasetSpec] = {
    "SinhalaMMLU": DatasetSpec(
        label="SinhalaMMLU",
        key="sinhala_mmlu",
        processed_file="sinhala_mmlu.jsonl",
        romanized_file="sinhala_mmlu_romanized.jsonl",
        kind="mmlu",
    ),
    "SOLD": DatasetSpec(
        label="SOLD",
        key="sold",
        processed_file="sold.jsonl",
        romanized_file="sold_romanized.jsonl",
        kind="flat",
    ),
    "Global PIQA": DatasetSpec(
        label="Global PIQA",
        key="global_piqa",
        processed_file="global_piqa.jsonl",
        romanized_file="global_piqa_romanized.jsonl",
        kind="mmlu",
    ),
}

PUNCTUATION = ".,!?;:\"'“”‘’()[]{}<>«»…"


def _version_tuple(raw: str) -> tuple[int, ...]:
    return tuple(int(m.group()) for m in (re.match(r"\d+", p) for p in raw.split(".")[:3]) if m)


# Streamlit 1.49 replaced `use_container_width=True` with `width="stretch"`.
# Pick whichever the installed version understands so the app runs on both.
STRETCH: dict[str, Any] = (
    {"width": "stretch"}
    if _version_tuple(st.__version__) >= (1, 49)
    else {"use_container_width": True}
)


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                st.warning(f"Skipped malformed line {line_no} in `{path.name}`: {exc}")
    return rows


@st.cache_data(show_spinner="Loading dataset…")
def load_dataset(data_dir_str: str, dataset_name: str) -> dict[str, Any]:
    """Load one dataset and join every romanization to it on `id`."""
    data_dir = Path(data_dir_str)
    spec = DATASETS[dataset_name]

    base_path = data_dir / "processed" / spec.processed_file
    problems: list[str] = []

    if not base_path.exists():
        return {"error": f"Source file not found: `{base_path}`"}

    order: list[str] = []
    records: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(base_path):
        rid = str(row.get("id", "")).strip()
        if not rid:
            continue
        if rid not in records:
            order.append(rid)
            records[rid] = {"base": row, "methods": {}}

    missing: dict[str, list[str]] = {}
    for method in METHODS:
        rom_path = data_dir / "romanized" / method / spec.romanized_file
        if not rom_path.exists():
            problems.append(f"Missing file for **{METHOD_LABELS[method]}**: `{rom_path}`")
            missing[method] = list(order)
            continue

        seen: set[str] = set()
        for row in _read_jsonl(rom_path):
            rid = str(row.get("id", "")).strip()
            if not rid:
                continue
            if rid not in records:  # present only in a romanized file
                order.append(rid)
                records[rid] = {"base": row, "methods": {}}
            records[rid]["methods"][method] = row
            seen.add(rid)
        missing[method] = [rid for rid in order if rid not in seen]

    return {
        "spec": spec,
        "order": order,
        "records": records,
        "missing": missing,
        "problems": problems,
    }


# --------------------------------------------------------------------------- #
# ID lookup
# --------------------------------------------------------------------------- #


def resolve_id(query: str, order: list[str]) -> tuple[str | None, list[str]]:
    """Resolve free-text input to a record id.

    Accepts `sold_0001`, `0001`, `1`, or any substring. Returns
    (resolved_id, suggestions).
    """
    q = query.strip().lower()
    if not q:
        return None, []

    exact = {rid.lower(): rid for rid in order}
    if q in exact:
        return exact[q], []

    if q.isdigit():
        wanted = int(q)
        for rid in order:
            tail = re.search(r"(\d+)\s*$", rid)
            if tail and int(tail.group(1)) == wanted:
                return rid, []

    matches = [rid for rid in order if q in rid.lower()]
    if len(matches) == 1:
        return matches[0], []
    return None, matches[:25]


# --------------------------------------------------------------------------- #
# Diffing
# --------------------------------------------------------------------------- #


def tokenize(text: str) -> list[str]:
    return re.findall(r"\S+", text or "")


def normalize(token: str, case_sensitive: bool) -> str:
    tok = token if case_sensitive else token.lower()
    return tok.strip(PUNCTUATION)


def _char_diff_html(ref_token: str, cmp_token: str, case_sensitive: bool) -> str:
    """Underline the characters inside `cmp_token` that differ from `ref_token`."""
    a = ref_token if case_sensitive else ref_token.lower()
    b = cmp_token if case_sensitive else cmp_token.lower()
    matcher = SequenceMatcher(a=a, b=b, autojunk=False)
    out: list[str] = []
    for tag, _, _, j1, j2 in matcher.get_opcodes():
        piece = html.escape(cmp_token[j1:j2])
        if not piece:
            continue
        out.append(piece if tag == "equal" else f"<u>{piece}</u>")
    return "".join(out)


def diff_html(ref_text: str, cmp_text: str, case_sensitive: bool) -> str:
    """Render `cmp_text`, marking every token that differs from `ref_text`."""
    ref_tokens, cmp_tokens = tokenize(ref_text), tokenize(cmp_text)
    if not cmp_tokens:
        return '<span class="muted">— no output for this method —</span>'
    if not ref_tokens:
        return html.escape(cmp_text)

    a = [normalize(t, case_sensitive) for t in ref_tokens]
    b = [normalize(t, case_sensitive) for t in cmp_tokens]
    matcher = SequenceMatcher(a=a, b=b, autojunk=False)

    parts: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            parts.extend(html.escape(t) for t in cmp_tokens[j1:j2])
        elif tag == "delete":
            parts.append('<span class="gap" title="no counterpart here">·</span>')
        elif tag == "insert":
            parts.extend(f'<mark class="diff">{html.escape(t)}</mark>' for t in cmp_tokens[j1:j2])
        else:  # replace
            if (i2 - i1) == (j2 - j1):  # 1:1, so a character-level diff is meaningful
                for offset in range(j2 - j1):
                    inner = _char_diff_html(
                        ref_tokens[i1 + offset], cmp_tokens[j1 + offset], case_sensitive
                    )
                    parts.append(f'<mark class="diff">{inner}</mark>')
            else:
                parts.extend(
                    f'<mark class="diff">{html.escape(t)}</mark>' for t in cmp_tokens[j1:j2]
                )
    return " ".join(parts)


def align_to_reference(ref_tokens: list[str], cmp_tokens: list[str], case_sensitive: bool) -> list[str]:
    """Map `cmp_tokens` onto the slots of `ref_tokens` so methods stack in a table."""
    slots: list[list[str]] = [[] for _ in ref_tokens]
    if not ref_tokens:
        return []

    a = [normalize(t, case_sensitive) for t in ref_tokens]
    b = [normalize(t, case_sensitive) for t in cmp_tokens]
    for tag, i1, i2, j1, j2 in SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                slots[i1 + offset].append(cmp_tokens[j1 + offset])
        elif tag == "replace":
            if (i2 - i1) == (j2 - j1):
                for offset in range(i2 - i1):
                    slots[i1 + offset].append(cmp_tokens[j1 + offset])
            else:
                slots[i1].extend(cmp_tokens[j1:j2])
        elif tag == "insert":
            target = min(max(i1 - 1, 0), len(slots) - 1)
            slots[target].extend(cmp_tokens[j1:j2])
        # "delete" leaves the slot empty on purpose
    return [" ".join(s) for s in slots]


# --------------------------------------------------------------------------- #
# Rendering helpers
# --------------------------------------------------------------------------- #

CSS = """
<style>
  .sinhala {
    font-family: "Noto Sans Sinhala", "Iskoola Pota", "Nirmala UI", "Malithi Web", sans-serif;
    font-size: 1.35rem;
    line-height: 2.1;
  }
  .roman {
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.98rem;
    line-height: 1.85;
    word-break: break-word;
  }
  .method-head {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.72rem;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    opacity: 0.75;
    margin-bottom: 0.35rem;
  }
  .rail { width: 3px; height: 0.95rem; border-radius: 2px; display: inline-block; }
  mark.diff {
    background: rgba(255, 190, 60, 0.34);
    color: inherit;
    border-radius: 3px;
    padding: 0 2px;
  }
  mark.diff u { text-decoration: underline 2px rgba(215, 65, 55, 0.95); }
  .gap { opacity: 0.35; }
  .muted { opacity: 0.55; font-style: italic; }
  .chip {
    display: inline-block;
    font-size: 0.72rem;
    letter-spacing: 0.04em;
    padding: 0.12rem 0.5rem;
    border-radius: 999px;
    border: 1px solid rgba(128, 128, 128, 0.45);
    margin-right: 0.35rem;
    opacity: 0.9;
  }
  .opt-key { font-weight: 700; opacity: 0.6; margin-right: 0.4rem; }
</style>
"""


def method_header(method: str, is_reference: bool) -> str:
    tag = " · reference" if is_reference else ""
    return (
        f'<div class="method-head">'
        f'<span class="rail" style="background:{METHOD_ACCENTS[method]}"></span>'
        f"{html.escape(METHOD_LABELS[method])}{tag}</div>"
    )


def render_method_card(method: str, text: str, ref_text: str, case_sensitive: bool, highlight: bool) -> None:
    body = (
        diff_html(ref_text, text, case_sensitive)
        if highlight
        else (html.escape(text) if text else '<span class="muted">— no output for this method —</span>')
    )
    with st.container(border=True):
        st.markdown(method_header(method, method == st.session_state.get("reference")), unsafe_allow_html=True)
        st.markdown(f'<div class="roman">{body}</div>', unsafe_allow_html=True)


def render_comparison(
    texts: dict[str, str], reference: str, layout: str, case_sensitive: bool, highlight: bool
) -> None:
    ref_text = texts.get(reference, "")
    if layout == "Grid (2 × 2)":
        for row_start in (0, 2):
            cols = st.columns(2, gap="medium")
            for col, method in zip(cols, METHODS[row_start : row_start + 2]):
                with col:
                    render_method_card(method, texts.get(method, ""), ref_text, case_sensitive, highlight)
    else:
        for method in METHODS:
            render_method_card(method, texts.get(method, ""), ref_text, case_sensitive, highlight)


def render_token_table(
    sinhala_text: str, texts: dict[str, str], reference: str, case_sensitive: bool
) -> None:
    """The core research view: one column per word, four methods stacked beneath."""
    ref_tokens = tokenize(texts.get(reference, ""))
    if not ref_tokens:
        st.info("The reference method has no output for this record, so tokens cannot be aligned.")
        return

    table: dict[str, list[str]] = {}
    sin_tokens = tokenize(sinhala_text)
    if len(sin_tokens) == len(ref_tokens):
        table["Sinhala"] = sin_tokens

    for method in METHODS:
        table[METHOD_LABELS[method]] = align_to_reference(
            ref_tokens, tokenize(texts.get(method, "")), case_sensitive
        )

    df = pd.DataFrame(table)
    df.index = pd.RangeIndex(1, len(df) + 1, name="#")

    method_cols = [METHOD_LABELS[m] for m in METHODS]

    def variant_count(row: pd.Series) -> int:
        vals = {normalize(str(row[c]), case_sensitive) for c in method_cols if str(row[c]).strip()}
        return len(vals)

    agreement = df.apply(variant_count, axis=1)
    df.insert(0, "Variants", agreement)

    def shade(row: pd.Series) -> list[str]:
        if row["Variants"] > 1:
            return ["background-color: rgba(255, 190, 60, 0.16)"] * len(row)
        return [""] * len(row)

    if len(sin_tokens) != len(ref_tokens):
        st.caption(
            f"Sinhala column hidden: the source has {len(sin_tokens)} tokens but the reference "
            f"romanization has {len(ref_tokens)}, so a 1:1 word alignment is not reliable here."
        )

    divergent = int((agreement > 1).sum())
    st.caption(
        f"{divergent} of {len(df)} word positions have more than one spelling across the four methods."
    )

    try:
        st.dataframe(df.style.apply(shade, axis=1), **STRETCH)
    except Exception:  # pandas Styler is optional; never let it break the view
        st.dataframe(df, **STRETCH)


# --------------------------------------------------------------------------- #
# Navigation callbacks
# --------------------------------------------------------------------------- #


def _step(order: list[str], delta: int) -> None:
    current = st.session_state.get("current_id")
    idx = order.index(current) if current in order else 0
    st.session_state.current_id = order[min(max(idx + delta, 0), len(order) - 1)]


def _run_search(order: list[str]) -> None:
    resolved, suggestions = resolve_id(st.session_state.get("search_query", ""), order)
    if resolved:
        st.session_state.current_id = resolved
        st.session_state.search_note = None
    else:
        st.session_state.search_note = suggestions or []


# --------------------------------------------------------------------------- #
# Overview statistics
# --------------------------------------------------------------------------- #


@st.cache_data(show_spinner="Scoring divergence between methods…")
def divergence_table(data_dir_str: str, dataset_name: str, limit: int) -> pd.DataFrame:
    bundle = load_dataset(data_dir_str, dataset_name)
    order, records = bundle["order"], bundle["records"]

    rows: list[dict[str, Any]] = []
    for rid in order[:limit]:
        rec = records[rid]
        texts = {
            m: str(rec["methods"].get(m, {}).get("text_romanized", "") or "") for m in METHODS
        }
        present = [t for t in texts.values() if t.strip()]
        token_lists = [[w.lower() for w in tokenize(t)] for t in present]

        sims = [
            SequenceMatcher(a=token_lists[i], b=token_lists[j], autojunk=False).ratio()
            for i in range(len(token_lists))
            for j in range(i + 1, len(token_lists))
        ]
        rows.append(
            {
                "id": rid,
                "distinct_outputs": len({t.strip().lower() for t in present}),
                "mean_similarity": round(mean(sims), 4) if sims else None,
                "missing_methods": len(METHODS) - len(present),
                "preview": (present[0][:90] + "…") if present and len(present[0]) > 90 else (present[0] if present else ""),
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #


def main() -> None:
    st.set_page_config(
        page_title="Sinhala Script Robustness — Transliteration Inspector",
        page_icon="🔤",
        layout="wide",
    )
    st.markdown(CSS, unsafe_allow_html=True)

    # ---- Sidebar: data source -------------------------------------------- #
    st.sidebar.title("Inspector")

    data_dir_str = st.sidebar.text_input(
        "Data directory",
        value=str(PROJECT_ROOT / "data"),
        help="Change this only if your data lives outside the project root.",
    )
    if st.sidebar.button("Reload files from disk", **STRETCH):
        st.cache_data.clear()
        st.rerun()

    dataset_name = st.sidebar.selectbox("Dataset", list(DATASETS.keys()))
    bundle = load_dataset(data_dir_str, dataset_name)

    if "error" in bundle:
        st.error(bundle["error"])
        st.stop()

    spec: DatasetSpec = bundle["spec"]
    order: list[str] = bundle["order"]
    records: dict[str, dict[str, Any]] = bundle["records"]

    for problem in bundle["problems"]:
        st.sidebar.warning(problem)

    if not order:
        st.error(f"No records found in `{data_dir_str}/processed/{spec.processed_file}`.")
        st.stop()

    # Keep the selected id valid when the dataset changes.
    if st.session_state.get("current_id") not in order:
        st.session_state.current_id = order[0]

    # ---- Sidebar: navigation --------------------------------------------- #
    st.sidebar.divider()
    st.sidebar.text_input(
        "Find by id",
        key="search_query",
        placeholder=f"{spec.key.split('_')[-1]}_0001, 0001, or 1",
        on_change=_run_search,
        args=(order,),
    )
    note = st.session_state.get("search_note")
    if note is not None:
        if note:
            st.sidebar.caption("Did you mean: " + ", ".join(f"`{s}`" for s in note))
        else:
            st.sidebar.caption("No record matches that id.")

    st.sidebar.selectbox("Record", order, key="current_id")

    prev_col, next_col = st.sidebar.columns(2)
    position = order.index(st.session_state.current_id)
    prev_col.button(
        "← Previous",
        **STRETCH,
        disabled=position == 0,
        on_click=_step,
        args=(order, -1),
    )
    next_col.button(
        "Next →",
        **STRETCH,
        disabled=position == len(order) - 1,
        on_click=_step,
        args=(order, 1),
    )
    st.sidebar.caption(f"Record {position + 1} of {len(order)}")

    # ---- Sidebar: view options ------------------------------------------- #
    st.sidebar.divider()
    st.session_state.reference = st.sidebar.selectbox(
        "Compare against",
        METHODS,
        format_func=lambda m: METHOD_LABELS[m],
        help="Differences are highlighted relative to this method.",
    )
    layout = st.sidebar.radio("Layout", ["Stacked rows", "Grid (2 × 2)"], horizontal=True)
    highlight = st.sidebar.toggle("Highlight differences", value=True)
    case_sensitive = st.sidebar.toggle("Case-sensitive comparison", value=False)

    reference = st.session_state.reference
    record = records[st.session_state.current_id]
    base = record["base"]

    # ---- Main ------------------------------------------------------------ #
    compare_tab, overview_tab = st.tabs(["Compare", "Overview"])

    with compare_tab:
        chips = [f'<span class="chip">{html.escape(str(base.get("id", "")))}</span>']
        for field in ("label", "domain", "difficulty"):
            if base.get(field):
                chips.append(
                    f'<span class="chip">{field}: {html.escape(str(base[field]))}</span>'
                )
        absent = [METHOD_LABELS[m] for m in METHODS if m not in record["methods"]]
        st.markdown(" ".join(chips), unsafe_allow_html=True)
        if absent:
            st.warning("No romanization for this record from: " + ", ".join(absent))

        # Source text
        st.markdown("#### Source (Unicode)")
        with st.container(border=True):
            st.markdown(
                f'<div class="sinhala">{html.escape(str(base.get("text_unicode", "")))}</div>',
                unsafe_allow_html=True,
            )

        texts = {
            m: str(record["methods"].get(m, {}).get("text_romanized", "") or "") for m in METHODS
        }

        st.markdown("#### Romanizations")
        render_comparison(texts, reference, layout, case_sensitive, highlight)

        st.markdown("#### Word alignment")
        render_token_table(str(base.get("text_unicode", "")), texts, reference, case_sensitive)

        # Options (SinhalaMMLU only)
        if spec.kind == "mmlu" and base.get("options"):
            st.divider()
            st.markdown("#### Answer options")
            options = list(base.get("options", []))
            correct = str(base.get("label", "")).strip().upper()

            for i, option_unicode in enumerate(options):
                key = chr(ord("A") + i)
                marker = "  ✅" if key == correct else ""
                with st.container(border=True):
                    st.markdown(
                        f'<div class="sinhala"><span class="opt-key">{key}.</span>'
                        f"{html.escape(str(option_unicode))}{marker}</div>",
                        unsafe_allow_html=True,
                    )
                    option_texts = {}
                    for method in METHODS:
                        arr = record["methods"].get(method, {}).get("options_romanized", []) or []
                        option_texts[method] = str(arr[i]) if i < len(arr) else ""
                    ref_option = option_texts.get(reference, "")
                    for method in METHODS:
                        body = (
                            diff_html(ref_option, option_texts[method], case_sensitive)
                            if highlight
                            else html.escape(option_texts[method])
                        )
                        st.markdown(
                            f'<div class="method-head" style="margin-top:.45rem">'
                            f'<span class="rail" style="background:{METHOD_ACCENTS[method]}"></span>'
                            f"{html.escape(METHOD_LABELS[method])}</div>"
                            f'<div class="roman">{body or "—"}</div>',
                            unsafe_allow_html=True,
                        )

        with st.expander("Raw JSON"):
            st.json(
                {
                    "processed": base,
                    **{METHOD_LABELS[m]: record["methods"].get(m) for m in METHODS},
                }
            )

    with overview_tab:
        st.markdown("#### Coverage")
        coverage = pd.DataFrame(
            [
                {
                    "method": METHOD_LABELS[m],
                    "records": len(order) - len(bundle["missing"].get(m, [])),
                    "missing": len(bundle["missing"].get(m, [])),
                }
                for m in METHODS
            ]
        )
        st.dataframe(coverage, hide_index=True, **STRETCH)

        for method in METHODS:
            gaps = bundle["missing"].get(method, [])
            if gaps:
                with st.expander(f"{METHOD_LABELS[method]} — {len(gaps)} missing ids"):
                    st.code(", ".join(gaps[:500]) + (" …" if len(gaps) > 500 else ""))

        st.divider()
        st.markdown("#### Where the methods disagree most")
        st.caption(
            "Scores each record by mean pairwise token similarity across the four methods. "
            "Low similarity means the transliterations diverge — those are the interesting cases."
        )
        limit = st.number_input(
            "Records to score",
            min_value=1,
            max_value=len(order),
            value=min(500, len(order)),
            step=max(1, min(50, len(order) // 10 or 1)),
        )
        if st.button("Score records"):
            table = divergence_table(data_dir_str, dataset_name, int(limit))
            st.session_state.divergence = (
                dataset_name,
                table.sort_values("mean_similarity", na_position="first"),
            )

        scored = st.session_state.get("divergence")
        if scored and scored[0] == dataset_name:
            table = scored[1]
            st.dataframe(table, hide_index=True, **STRETCH)
            st.download_button(
                "Download as CSV",
                table.to_csv(index=False).encode("utf-8"),
                file_name=f"{spec.key}_divergence.csv",
                mime="text/csv",
            )


if __name__ == "__main__":
    main()