"""Apply each transliteration method to the Sinhala side of a reference corpus.

For every parallel corpus we deduplicate the Sinhala strings, romanize each
unique string once per method (with an on-disk cache so runs are resumable),
then emit an aligned hypotheses file:

    data/reference/transliterated/<corpus>/<method>.jsonl
        {"id": ..., "sinhala": ..., "hypothesis": ...}

Local methods (phonetic, aksharamukha, uroman) are CPU-bound and safe to run on
the full corpora. The `nisansa` method calls a third-party web endpoint once per
string, so it is only appropriate for small corpora (see --help).
"""

import argparse
import importlib
import importlib.util
import json
import sys
import time
from pathlib import Path

from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PARALLEL_DIR = PROJECT_ROOT / "data" / "reference" / "parallel"
OUT_DIR = PROJECT_ROOT / "data" / "reference" / "transliterated"
CACHE_DIR = PROJECT_ROOT / "data" / "reference" / "cache"
TRANSLIT_SRC = PROJECT_ROOT / "src" / "transliteration"

sys.path.insert(0, str(TRANSLIT_SRC))


def _load_methods(names: list[str]) -> dict:
    methods = {}
    for name in names:
        if name == "nisansa_sirs_method":
            spec = importlib.util.spec_from_file_location(
                "nisansa_sirs_method", TRANSLIT_SRC / "nisansa_sir's_method.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            module = importlib.import_module(METHOD_MODULES[name])
        methods[name] = module.transliterate
    return methods


METHOD_MODULES = {
    "phonetic": "phonetic",
    "aksharamukha": "aksharamukha_method",
    "uroman": "uroman_method",
    "nisansa_sirs_method": "nisansa_sirs_method",
}


def _load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _save_cache(path: Path, cache: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(cache, fh, ensure_ascii=False)
    tmp.replace(path)


def _read_unique_sinhala(corpus: str) -> list[str]:
    seen: dict[str, None] = {}
    with (PARALLEL_DIR / f"{corpus}.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            s = json.loads(line)["sinhala"]
            if s not in seen:
                seen[s] = None
    return list(seen)


def _fill_cache_batched(todo: list[str], cache: dict, cache_path: Path,
                        desc: str, save_interval: int, block: int = 2500,
                        passes: int = 3) -> list[str]:
    """Fill the cache using the batched Nisansa client (~70x fewer requests).

    Failures are deliberately *not* cached. The upstream service sheds load
    under sustained traffic, and caching the untranslated source as a stand-in
    silently turns a transport failure into a plausible-looking score (it once
    produced a CER of 0.97 that looked like a real result). Unresolved items are
    retried in later passes and whatever remains is returned, so the caller can
    fail loudly rather than score partial data.
    """
    from nisansa_batch import transliterate_many

    pending = list(todo)
    for attempt in range(1, passes + 1):
        if not pending:
            break
        if attempt > 1:
            tqdm.write(f"  retry pass {attempt}: {len(pending):,} unresolved, pausing 60s")
            time.sleep(60)
        failed: list[str] = []
        since_save = 0
        with tqdm(total=len(pending), desc=f"{desc} p{attempt}", unit="str") as bar:
            for start in range(0, len(pending), block):
                group = pending[start:start + block]
                try:
                    out = transliterate_many(group, progress=bar.update)
                except Exception as exc:
                    tqdm.write(f"  ! block at {start} unresolved ({exc})")
                    failed.extend(group)
                    bar.update(len(group))
                    continue
                for s, r in zip(group, out):
                    if r:
                        cache[s] = r
                    else:
                        failed.append(s)
                since_save += len(group)
                if since_save >= save_interval:
                    _save_cache(cache_path, cache)
                    since_save = 0
        _save_cache(cache_path, cache)
        pending = failed
    return pending


def run_method(corpus: str, method_name: str, fn, save_every: int = 2000) -> None:
    unique = _read_unique_sinhala(corpus)
    cache_path = CACHE_DIR / corpus / f"{method_name}.json"
    cache = _load_cache(cache_path)
    todo = [s for s in unique if s not in cache]
    print(f"[{corpus}/{method_name}] {len(unique):,} unique | cached {len(cache):,} | to do {len(todo):,}")

    # The cache is dumped in full on each checkpoint, so scale the interval to
    # bound total writes to ~15 dumps regardless of corpus size (avoids O(n^2)).
    save_interval = max(save_every, len(todo) // 15 + 1)

    if method_name == "nisansa_sirs_method":
        unresolved = _fill_cache_batched(todo, cache, cache_path,
                                         f"{corpus}/{method_name}", save_interval)
        if unresolved:
            _save_cache(cache_path, cache)
            raise SystemExit(
                f"[{corpus}/{method_name}] {len(unresolved):,} items still unresolved after "
                f"retries. Nothing was faked; re-run to resume from the cache."
            )
    else:
        since_save = 0
        for s in tqdm(todo, desc=f"{corpus}/{method_name}", unit="str"):
            try:
                cache[s] = fn(s)
            except Exception as exc:  # keep going; record the failure verbatim source
                cache[s] = s
                tqdm.write(f"  ! failed on {s[:30]!r}: {exc}")
            since_save += 1
            if since_save >= save_interval:
                _save_cache(cache_path, cache)
                since_save = 0
    _save_cache(cache_path, cache)

    out_path = OUT_DIR / corpus / f"{method_name}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with (PARALLEL_DIR / f"{corpus}.jsonl").open(encoding="utf-8") as fin, \
            out_path.open("w", encoding="utf-8", newline="\n") as fout:
        for line in fin:
            rec = json.loads(line)
            fout.write(json.dumps(
                {"id": rec["id"], "sinhala": rec["sinhala"], "hypothesis": cache.get(rec["sinhala"], "")},
                ensure_ascii=False,
            ) + "\n")
    print(f"[{corpus}/{method_name}] wrote {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, help="corpus name (matches parallel/<corpus>.jsonl)")
    parser.add_argument("--methods", nargs="+", default=["phonetic", "aksharamukha", "uroman"],
                        choices=list(METHOD_MODULES))
    args = parser.parse_args()

    fns = _load_methods(args.methods)
    for method_name in args.methods:
        run_method(args.corpus, method_name, fns[method_name])
