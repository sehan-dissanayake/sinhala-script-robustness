"""Distributed, resumable runner for the Nisansa web romanizer.

The upstream endpoint serves roughly 25k words before it starts shedding load,
so romanizing the 450,587-word corpus has to be spread across several sessions
and several people. This splits the corpus into independent shards that team
members can run in any order, on any machine, and stop at any moment.

Design notes
------------
*Stride assignment.* Item ``i`` belongs to shard ``i % n_shards``. The corpus is
alphabetically sorted, so contiguous ranges would give each member one initial
letter and any partially finished run would be an alphabetically biased slice
(the flaw in the existing 25k block). With a stride, every shard is a
representative spread over the whole corpus, so even a partial result set stays
a usable random sample.

*One file per shard, append-only.* Each shard writes
``shard-XX.jsonl`` and never touches another shard's file, so several people can
commit concurrently without merge conflicts on a large machine-generated file.
Appending one line per result means a run killed mid-flight (or a rate limit
hitting at any moment) loses at most the current batch, and resuming is just
"skip what is already in the file".

*Self-contained manifest.* ``manifest.txt.gz`` holds the corpus item list, so a
teammate can clone the repo and run a shard without downloading or rebuilding
the multi-hundred-MB source datasets.

Usage
-----
    python nisansa_shards.py status
    python nisansa_shards.py run --shard 7          # resumable, stop any time
    python nisansa_shards.py merge                  # once all shards are done

Maintainer-only, already done for the word corpus:
    python nisansa_shards.py init --shards 24
    python nisansa_shards.py seed
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import subprocess
import sys
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PARALLEL_DIR = PROJECT_ROOT / "data" / "reference" / "parallel"
SHARD_ROOT = PROJECT_ROOT / "data" / "reference" / "nisansa_shards"
CACHE_DIR = PROJECT_ROOT / "data" / "reference" / "cache"
TRANSLIT_DIR = PROJECT_ROOT / "data" / "reference" / "transliterated"

METHOD = "nisansa_sirs_method"
DEFAULT_CORPUS = "swa_bhasha_words"

# Items per append. One group is a couple of HTTP requests, so a hard kill costs
# at most this many items of work.
GROUP = 600
# Consecutive failed groups before we conclude the endpoint is shedding load and
# stop cleanly instead of hammering it.
MAX_CONSECUTIVE_FAILURES = 3


def shard_dir(corpus: str) -> Path:
    return SHARD_ROOT / corpus


def meta_path(corpus: str) -> Path:
    return shard_dir(corpus) / "meta.json"


def manifest_path(corpus: str) -> Path:
    return shard_dir(corpus) / "manifest.txt.gz"


def shard_path(corpus: str, shard: int) -> Path:
    return shard_dir(corpus) / f"shard-{shard:02d}.jsonl"


def load_meta(corpus: str) -> dict:
    p = meta_path(corpus)
    if not p.exists():
        raise SystemExit(f"No shard set for '{corpus}'. Run `init` first (maintainer).")
    return json.loads(p.read_text(encoding="utf-8"))


def load_manifest(corpus: str) -> list[str]:
    with gzip.open(manifest_path(corpus), "rt", encoding="utf-8") as fh:
        return fh.read().split("\n")


def shard_items(corpus: str, shard: int, manifest: list[str] | None = None) -> list[str]:
    """The manifest items assigned to one shard, by stride."""
    n = load_meta(corpus)["n_shards"]
    if not 0 <= shard < n:
        raise SystemExit(f"--shard must be 0..{n - 1}")
    return (manifest if manifest is not None else load_manifest(corpus))[shard::n]


def load_shard_results(corpus: str, shard: int) -> dict[str, str]:
    p = shard_path(corpus, shard)
    out: dict[str, str] = {}
    if not p.exists():
        return out
    with p.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue          # tolerate a torn final line from a hard kill
            if rec.get("s") and rec.get("r"):
                out[rec["s"]] = rec["r"]
    return out


# --- commands --------------------------------------------------------------

def cmd_init(corpus: str, n_shards: int) -> None:
    src = PARALLEL_DIR / f"{corpus}.jsonl"
    if not src.exists():
        raise SystemExit(f"{src} missing; build the parallel corpus first.")
    seen: dict[str, None] = {}
    with src.open(encoding="utf-8") as fh:
        for line in fh:
            seen.setdefault(json.loads(line)["sinhala"], None)
    items = list(seen)

    shard_dir(corpus).mkdir(parents=True, exist_ok=True)
    with gzip.open(manifest_path(corpus), "wt", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(items))
    meta_path(corpus).write_text(
        json.dumps({"corpus": corpus, "n_shards": n_shards, "n_items": len(items)}, indent=2),
        encoding="utf-8")
    size = manifest_path(corpus).stat().st_size / 1024 / 1024
    print(f"{corpus}: {len(items):,} items -> {n_shards} shards "
          f"(~{len(items) // n_shards:,} each), manifest {size:.1f} MB")


def cmd_seed(corpus: str) -> None:
    """Fold already-fetched results into their shard files so nobody refetches."""
    meta = load_meta(corpus)
    n = meta["n_shards"]
    existing: dict[str, str] = {}
    for cache_file in (CACHE_DIR / corpus / f"{METHOD}.json",
                       CACHE_DIR / f"{corpus}_nisansacov" / f"{METHOD}.json"):
        if cache_file.exists():
            for k, v in json.loads(cache_file.read_text(encoding="utf-8")).items():
                if v and k != v:          # k == v was the old failure placeholder
                    existing[k] = v
    if not existing:
        print("nothing to seed")
        return

    manifest = load_manifest(corpus)
    owner = {item: i % n for i, item in enumerate(manifest)}
    already = {s: load_shard_results(corpus, s) for s in range(n)}

    added = [0] * n
    handles = {}
    try:
        for item, romanized in existing.items():
            s = owner.get(item)
            if s is None or item in already[s]:
                continue
            if s not in handles:
                handles[s] = shard_path(corpus, s).open("a", encoding="utf-8", newline="\n")
            handles[s].write(json.dumps({"s": item, "r": romanized}, ensure_ascii=False) + "\n")
            already[s][item] = romanized
            added[s] += 1
    finally:
        for h in handles.values():
            h.close()
    print(f"seeded {sum(added):,} existing results into {sum(1 for a in added if a)} shards")


def cmd_status(corpus: str) -> None:
    meta = load_meta(corpus)
    n, total = meta["n_shards"], meta["n_items"]
    print(f"{corpus}: {total:,} items across {n} shards\n")
    print(" shard   done /  total   pct  state")
    done_all = 0
    manifest = load_manifest(corpus)      # decompress once, not once per shard
    for s in range(n):
        items = shard_items(corpus, s, manifest)
        done = len(set(load_shard_results(corpus, s)) & set(items))
        done_all += done
        pct = 100 * done / len(items) if items else 0
        state = "complete" if done == len(items) else ("not started" if done == 0 else "partial")
        print(f"  {s:3d}  {done:6,} / {len(items):6,}  {pct:5.1f}  {state}")
    print(f"\noverall: {done_all:,} / {total:,} ({100 * done_all / total:.1f}%)")
    if done_all == total:
        print("all shards complete -> run `merge`")


class ShardLock:
    """Stop two processes from working the same shard.

    Two runs on one shard duplicate every request, doubling load on an endpoint
    that is already the bottleneck, and gain nothing. The lock is advisory: it
    stores a pid, and a lock left behind by a killed process is reclaimed.
    """

    def __init__(self, corpus: str, shard: int):
        self.path = shard_dir(corpus) / f"shard-{shard:02d}.lock"

    def __enter__(self):
        if self.path.exists():
            try:
                pid = int(self.path.read_text(encoding="utf-8").strip())
            except (ValueError, OSError):
                pid = None
            if pid and _pid_alive(pid):
                raise SystemExit(
                    f"Shard already running in process {pid} ({self.path.name}).\n"
                    f"Pick a different shard, or stop that process first.")
            print(f"(reclaiming stale lock from process {pid})")
        self.path.write_text(str(os.getpid()), encoding="utf-8")
        return self

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)


def _pid_alive(pid: int) -> bool:
    if sys.platform == "win32":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                             capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def cmd_run(corpus: str, shard: int, limit: int | None) -> None:
    from nisansa_batch import transliterate_many

    items = shard_items(corpus, shard)
    have = load_shard_results(corpus, shard)
    todo = [i for i in items if i not in have]
    print(f"[{corpus} shard {shard}] {len(items):,} assigned | "
          f"{len(items) - len(todo):,} done | {len(todo):,} to do")
    if not todo:
        print("shard already complete.")
        return
    if limit:
        todo = todo[:limit]
        print(f"limited to {len(todo):,} this session")

    path = shard_path(corpus, shard)
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    consecutive_failures = 0
    stopped_early = False

    with path.open("a", encoding="utf-8", newline="\n") as out, \
            tqdm(total=len(todo), desc=f"shard {shard}", unit="word") as bar:

        def persist(src: str, romanized: str) -> None:
            """Write each result the moment it arrives, not at end of group.

            The endpoint can begin refusing mid-group; anything already fetched
            has to survive that, otherwise a stop discards completed work.
            """
            nonlocal written
            out.write(json.dumps({"s": src, "r": romanized}, ensure_ascii=False) + "\n")
            out.flush()
            written += 1

        for start in range(0, len(todo), GROUP):
            group = todo[start:start + GROUP]
            try:
                transliterate_many(group, progress=bar.update, on_result=persist,
                                   notify=lambda m: bar.set_postfix_str(m, refresh=True))
                bar.set_postfix_str("")
                consecutive_failures = 0
            except Exception as exc:
                consecutive_failures += 1
                tqdm.write(f"  ! group interrupted ({exc}); {written:,} results kept so far")
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    tqdm.write("  endpoint appears to be refusing traffic; stopping cleanly.")
                    stopped_early = True
                    break
                continue

    remaining = len(items) - len(load_shard_results(corpus, shard))
    print(f"\nwrote {written:,} results. {remaining:,} items left in this shard.")
    if remaining:
        print(f"Rate limited or interrupted? Just run the same command again - it resumes:\n"
              f"  python src/method_evaluation/nisansa_shards.py run --shard {shard}")
    else:
        print("shard complete. Commit the shard file and push.")
    if stopped_early:
        print("(Stopped early on repeated refusals. Waiting a while before retrying helps.)")


def cmd_merge(corpus: str) -> None:
    meta = load_meta(corpus)
    n = meta["n_shards"]
    merged: dict[str, str] = {}
    for s in range(n):
        merged.update(load_shard_results(corpus, s))

    manifest = set(load_manifest(corpus))
    covered = len(merged.keys() & manifest)
    print(f"merged {len(merged):,} results; covers {covered:,} / {len(manifest):,} corpus items "
          f"({100 * covered / len(manifest):.1f}%)")

    cache_file = CACHE_DIR / corpus / f"{METHOD}.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(merged, ensure_ascii=False), encoding="utf-8")
    print(f"wrote cache -> {cache_file.relative_to(PROJECT_ROOT)}")

    src = PARALLEL_DIR / f"{corpus}.jsonl"
    if not src.exists():
        print(f"NOTE: {src.relative_to(PROJECT_ROOT)} not present, so the aligned hypothesis file "
              f"was not written. Rebuild the parallel corpus, or rerun "
              f"transliterate_references.py --corpus {corpus} --methods {METHOD} "
              f"(it will find everything in the cache).")
        return

    out_path = TRANSLIT_DIR / corpus / f"{METHOD}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    missing = 0
    with src.open(encoding="utf-8") as fin, out_path.open("w", encoding="utf-8", newline="\n") as fout:
        for line in fin:
            rec = json.loads(line)
            hyp = merged.get(rec["sinhala"], "")
            missing += not hyp
            fout.write(json.dumps({"id": rec["id"], "sinhala": rec["sinhala"], "hypothesis": hyp},
                                  ensure_ascii=False) + "\n")
    print(f"wrote hypotheses -> {out_path.relative_to(PROJECT_ROOT)}"
          + (f" ({missing:,} items still unromanized)" if missing else ""))
    if missing:
        print("Those items would be scored as empty. Finish the remaining shards, or evaluate on "
              "the covered subset with:\n"
              f"  python src/method_evaluation/sample_corpus.py --corpus {corpus} "
              f"--covered-by {METHOD} --suffix nisansacov")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["init", "seed", "status", "run", "merge"])
    ap.add_argument("--corpus", default=DEFAULT_CORPUS)
    ap.add_argument("--shard", type=int, help="which shard to run (see `status`)")
    ap.add_argument("--shards", type=int, default=24, help="shard count, for `init`")
    ap.add_argument("--limit", type=int, help="stop after this many items this session")
    args = ap.parse_args()

    if args.command == "init":
        cmd_init(args.corpus, args.shards)
    elif args.command == "seed":
        cmd_seed(args.corpus)
    elif args.command == "status":
        cmd_status(args.corpus)
    elif args.command == "merge":
        cmd_merge(args.corpus)
    else:
        if args.shard is None:
            raise SystemExit("run requires --shard N (see `status` for what is unclaimed)")
        with ShardLock(args.corpus, args.shard):
            cmd_run(args.corpus, args.shard, args.limit)
