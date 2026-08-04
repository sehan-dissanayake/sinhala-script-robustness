"""Distributed, resumable runner for the Nisansa web romanizer.

Romanizing the 450,587-word and 275,259-sentence corpora through a third-party
web form takes hours, so this splits a corpus into independent shards that team
members can run in any order, on any machine, and stop at any moment.

What the runner records
-----------------------
The endpoint's output, verbatim. Two defects are captured rather than papered
over, because the evaluation counts them as the tool's genuine errors:

  * items the endpoint cannot romanize at all (it returns an empty placeholder)
    are recorded in ``unsupported.json`` and scored as an empty hypothesis, i.e.
    CER 1.0. They are no longer dropped from the comparison.
  * characters the endpoint returns unromanized inside otherwise valid output
    (ඓ, ඞ, ඦ and friends - see ``nisansa_probe.py``) are kept as-is. An earlier
    revision ran the in-house phonetic romanizer over every response to patch
    these up, which silently turned the measured system into a hybrid of two
    methods under test. Shard data produced before that change needs
    ``refetch-leaks`` to become comparable.

Design notes
------------
*Stride assignment.* Item ``i`` belongs to shard ``i % n_shards``. The word
corpus is alphabetically sorted, so contiguous ranges would give each member one
initial letter and any partially finished run would be an alphabetically biased
slice. With a stride, every shard is a representative spread over the whole
corpus, so even a partial result set stays a usable random sample.

*One file per shard, append-only.* Each shard writes ``shard-XX.jsonl`` and
never touches another shard's file, so several people can commit concurrently
without merge conflicts on a large machine-generated file. Appending one line
per result means a run killed mid-flight loses at most the current batch, and
resuming is just "skip what is already in the file". Later lines win on load, so
a corrected result can be appended without rewriting history.

*Self-contained manifest.* ``manifest.txt.gz`` holds the corpus item list, so a
teammate can clone the repo and run a shard without rebuilding the source
datasets.

Usage
-----
    python nisansa_shards.py status --corpus swa_bhasha_words
    python nisansa_shards.py run --corpus swa_bhasha_words --all
    python nisansa_shards.py run --corpus swa_bhasha_words --shard 7
    python nisansa_shards.py refetch-leaks --corpus swa_bhasha_words
    python nisansa_shards.py merge --corpus swa_bhasha_words

Maintainer-only, once per corpus:
    python nisansa_shards.py init --corpus <name> --shards 24
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
LEAKING_PATH = PROJECT_ROOT / "data" / "reference" / "nisansa_endpoint" / "leaking_sequences.json"

METHOD = "nisansa_sirs_method"
DEFAULT_CORPUS = "swa_bhasha_words"

# Items per append. One group is a couple of dozen HTTP requests, so a hard kill
# costs at most this many items of work.
GROUP = 600
# Consecutive failed groups before we conclude the endpoint is unreachable and
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


def unsupported_path(corpus: str) -> Path:
    return shard_dir(corpus) / "unsupported.json"


def load_unsupported(corpus: str) -> dict[str, str]:
    """Items the endpoint cannot romanize, mapped to why.

    Kept out of the shard result files so those stay pure endpoint output, and
    kept out of the "to do" count so a run can reach 100% instead of forever
    reporting a handful of items left. These are *not* excluded from scoring:
    `merge` writes them out with an empty hypothesis so the evaluation charges
    the tool for them.
    """
    p = unsupported_path(corpus)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_unsupported(corpus: str, data: dict[str, str]) -> None:
    unsupported_path(corpus).parent.mkdir(parents=True, exist_ok=True)
    unsupported_path(corpus).write_text(
        json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


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
            # Later lines win, so an appended correction supersedes the original.
            if rec.get("s") and rec.get("r"):
                out[rec["s"]] = rec["r"]
    return out


def leaking_sequences() -> list[str]:
    if not LEAKING_PATH.exists():
        raise SystemExit(
            f"{LEAKING_PATH.relative_to(PROJECT_ROOT)} missing.\n"
            f"Run: python src/method_evaluation/nisansa_probe.py")
    return json.loads(LEAKING_PATH.read_text(encoding="utf-8"))["sequences"]


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
    if any("\n" in i for i in items):
        raise SystemExit("corpus contains embedded newlines; manifest format cannot hold them")

    shard_dir(corpus).mkdir(parents=True, exist_ok=True)
    with gzip.open(manifest_path(corpus), "wt", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(items))
    meta_path(corpus).write_text(
        json.dumps({"corpus": corpus, "n_shards": n_shards, "n_items": len(items)}, indent=2),
        encoding="utf-8")
    size = manifest_path(corpus).stat().st_size / 1024 / 1024
    print(f"{corpus}: {len(items):,} items -> {n_shards} shards "
          f"(~{len(items) // n_shards:,} each), manifest {size:.1f} MB")


def cmd_seed(corpus: str, allow_repaired: bool) -> None:
    """Fold already-fetched results into their shard files so nobody refetches."""
    if not allow_repaired:
        raise SystemExit(
            "The on-disk caches were produced with the phonetic repair pass, which\n"
            "patched leaked Sinhala characters using one of the competing methods.\n"
            "Seeding them mixes two conventions into one result set.\n"
            "Pass --allow-repaired if you really want that, then run `refetch-leaks`.")
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
    print(" shard   done /  total   pct  fail  state")
    done_all = skip_all = 0
    manifest = load_manifest(corpus)      # decompress once, not once per shard
    skip = load_unsupported(corpus)
    for s in range(n):
        items = set(shard_items(corpus, s, manifest))
        done = len(set(load_shard_results(corpus, s)) & items)
        n_skip = len(items & set(skip))
        done_all += done
        skip_all += n_skip
        # An item the endpoint cannot romanize counts as resolved: it will never
        # succeed, so leaving it outstanding would stop a shard reaching 100%.
        resolved = done + n_skip
        pct = 100 * resolved / len(items) if items else 0
        state = ("complete" if resolved >= len(items)
                 else "not started" if resolved == 0 else "partial")
        print(f"  {s:3d}  {done:6,} / {len(items):6,}  {pct:5.1f} {n_skip:5,}  {state}")
    resolved_all = done_all + skip_all
    print(f"\noverall: {done_all:,} romanized + {skip_all:,} unromanizable "
          f"= {resolved_all:,} / {total:,} ({100 * resolved_all / total:.1f}%)")
    if skip_all:
        print(f"the {skip_all:,} unromanizable items are scored as empty output "
              f"(CER 1.0), not excluded")
    if resolved_all >= total:
        print("all shards complete -> run `refetch-leaks`, then `merge`")


class ShardLock:
    """Stop two processes from working the same shard.

    Two runs on one shard duplicate every request, doubling load on an endpoint
    that is already the bottleneck, and gain nothing. The lock is advisory: it
    stores a pid, and a lock left behind by a killed process is reclaimed.
    """

    def __init__(self, corpus: str, shard: int):
        self.path = shard_dir(corpus) / f"shard-{shard:02d}.lock"

    def __enter__(self):
        # Create exclusively: checking for the file and then writing it is a
        # race, and two runs launched in the same second both got through it.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for attempt in (1, 2):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w") as fh:
                    fh.write(str(os.getpid()))
                return self
            except FileExistsError:
                try:
                    pid = int(self.path.read_text(encoding="utf-8").strip())
                except (ValueError, OSError):
                    pid = None
                if pid and pid != os.getpid() and _pid_alive(pid):
                    raise SystemExit(
                        f"Shard {self.path.stem.split('-')[-1]} is already running in "
                        f"process {pid}.\nRun `status` and pick a shard nobody is on, "
                        f"or stop that process first.")
                if attempt == 1:
                    print(f"(reclaiming stale lock from process {pid})")
                    self.path.unlink(missing_ok=True)
        raise SystemExit(f"could not acquire {self.path.name}")

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


def _fetch_into_shard(corpus: str, shard: int, todo: list[str], desc: str) -> tuple[int, bool]:
    """Fetch `todo` and append results to the shard file. Returns (written, stopped_early)."""
    from nisansa_batch import transliterate_many

    path = shard_path(corpus, shard)
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    consecutive_failures = 0
    stopped_early = False
    unsupported = load_unsupported(corpus)
    known_unsupported = len(unsupported)

    with path.open("a", encoding="utf-8", newline="\n") as out, \
            tqdm(total=len(todo), desc=desc, unit="item") as bar:

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
                                   unsupported=unsupported,
                                   notify=lambda m: bar.set_postfix_str(m, refresh=True))
                bar.set_postfix_str("")
                consecutive_failures = 0
            except Exception as exc:
                consecutive_failures += 1
                tqdm.write(f"  ! group interrupted ({exc}); {written:,} results kept so far")
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    tqdm.write("  repeated transport failures; stopping cleanly.")
                    stopped_early = True
                    break
                continue
            # Persist the failure list as we go: a long run that is killed
            # should not have to rediscover which items the endpoint refuses.
            if len(unsupported) > known_unsupported:
                save_unsupported(corpus, unsupported)
                known_unsupported = len(unsupported)

    if len(unsupported) > known_unsupported:
        save_unsupported(corpus, unsupported)
    return written, stopped_early


def cmd_run(corpus: str, shard: int, limit: int | None) -> None:
    items = shard_items(corpus, shard)
    have = load_shard_results(corpus, shard)
    skip = load_unsupported(corpus)
    todo = [i for i in items if i not in have and i not in skip]
    n_skip = sum(1 for i in items if i in skip)
    print(f"[{corpus} shard {shard}] {len(items):,} assigned | {len(have):,} done | "
          f"{n_skip:,} refused by endpoint | {len(todo):,} to do")
    if not todo:
        print("shard already complete.")
        return
    if limit:
        todo = todo[:limit]
        print(f"limited to {len(todo):,} this session")

    written, stopped_early = _fetch_into_shard(corpus, shard, todo, f"shard {shard}")

    unsupported = load_unsupported(corpus)
    done = load_shard_results(corpus, shard)
    remaining = len([i for i in items if i not in done and i not in unsupported])
    print(f"\nwrote {written:,} results. {remaining:,} items left in this shard.")
    if remaining:
        print(f"Interrupted? Just run the same command again - it resumes:\n"
              f"  python src/method_evaluation/nisansa_shards.py run "
              f"--corpus {corpus} --shard {shard}")
    else:
        print("shard complete.")
    if stopped_early:
        print("(Stopped early on repeated transport failures. Try again later.)")


def cmd_run_all(corpus: str, limit: int | None) -> None:
    """Work every shard in turn, in one process. Resumable: rerun the same command."""
    n = load_meta(corpus)["n_shards"]
    for s in range(n):
        lock = ShardLock(corpus, s)
        try:
            lock.__enter__()
        except SystemExit as exc:
            print(f"skipping shard {s}: {exc}")
            continue
        try:
            print(f"\n--- shard {s} of {n} ---")
            cmd_run(corpus, s, limit)
        finally:
            lock.__exit__()
    print("\npass over all shards finished. Run `status` to confirm, then "
          "`refetch-leaks` and `merge`.")


def cmd_reset(corpus: str, yes: bool) -> None:
    """Clear a corpus's shard results so it can be refetched from scratch.

    Needed once, to replace results produced with the phonetic repair pass. A
    targeted `refetch-leaks` is cheaper but cannot be trusted to be complete:
    the probe grid covers well-formed aksharas, and the corpora also contain
    malformed sequences (a vowel sign followed by al-lakuna, an independent
    vowel carrying a vowel sign) that leak without matching any probed unit.
    A full refetch removes the need to reason about coverage at all.

    The previous results stay in git history, so this is recoverable.
    """
    n = load_meta(corpus)["n_shards"]
    paths = [p for p in (shard_path(corpus, s) for s in range(n)) if p.exists()]
    total = sum(len(load_shard_results(corpus, s)) for s in range(n))
    print(f"{corpus}: {len(paths)} shard file(s), {total:,} results, "
          f"{len(load_unsupported(corpus)):,} recorded failures")
    if not yes:
        raise SystemExit(
            "This deletes those results so they can be refetched raw.\n"
            "They remain in git history (`git checkout -- data/reference/nisansa_shards`).\n"
            "Re-run with --yes to proceed.")
    for p in paths:
        p.unlink()
    unsupported_path(corpus).unlink(missing_ok=True)
    print(f"cleared. Now run: run --corpus {corpus} --all")


def cmd_refetch_leaks(corpus: str) -> None:
    """Re-fetch items whose cached result may have been altered by phonetic repair.

    Cheap, but NOT a substitute for `reset` + a full run when the goal is to
    remove phonetic-repair contamination. It only finds items matching the
    probed leak table, and real corpora contain malformed sequences that leak
    without matching any probed akshara. Use it to top up a corpus that is
    already raw, not to convert a repaired one.

    Corrections are appended to the owning shard file; later lines win on load.
    """
    leaks = leaking_sequences()
    n = load_meta(corpus)["n_shards"]
    manifest = load_manifest(corpus)
    owner = {item: i % n for i, item in enumerate(manifest)}
    affected = [i for i in manifest if any(s in i for s in leaks)]
    print(f"{corpus}: {len(leaks)} leaking sequence(s); "
          f"{len(affected):,} of {len(manifest):,} items contain one")
    if not affected:
        print("nothing to refetch.")
        return

    by_shard: dict[int, list[str]] = {}
    for item in affected:
        by_shard.setdefault(owner[item], []).append(item)

    before = {}
    total_written = 0
    for s in sorted(by_shard):
        before[s] = load_shard_results(corpus, s)
        with ShardLock(corpus, s):
            written, _ = _fetch_into_shard(corpus, s, by_shard[s], f"leaks shard {s}")
        total_written += written

    changed = same = 0
    for s in sorted(by_shard):
        after = load_shard_results(corpus, s)
        for item in by_shard[s]:
            old, new = before[s].get(item), after.get(item)
            if new is None:
                continue
            if old is None or old == new:
                same += 1
            else:
                changed += 1
    print(f"\nrefetched {total_written:,}; {changed:,} results changed, {same:,} unchanged.")
    print("Now rerun `merge`, then derive_nisansa_w.py and run_evaluation.py.")


def cmd_merge(corpus: str) -> None:
    meta = load_meta(corpus)
    n = meta["n_shards"]
    merged: dict[str, str] = {}
    for s in range(n):
        merged.update(load_shard_results(corpus, s))

    manifest = set(load_manifest(corpus))
    unsupported = load_unsupported(corpus)
    covered = len(merged.keys() & manifest)
    refused = len(manifest & set(unsupported))
    print(f"merged {len(merged):,} results; covers {covered:,} / {len(manifest):,} corpus items "
          f"({100 * covered / len(manifest):.1f}%)")
    print(f"{refused:,} items refused by the endpoint -> written as empty output "
          f"and scored as errors")
    outstanding = len(manifest) - covered - refused
    if outstanding:
        print(f"WARNING: {outstanding:,} items neither romanized nor refused. Finish the "
              f"run before merging, or they will be scored as failures they are not.")

    cache_file = CACHE_DIR / corpus / f"{METHOD}.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(merged, ensure_ascii=False), encoding="utf-8")
    print(f"wrote cache -> {cache_file.relative_to(PROJECT_ROOT)}")

    src = PARALLEL_DIR / f"{corpus}.jsonl"
    if not src.exists():
        print(f"NOTE: {src.relative_to(PROJECT_ROOT)} not present, so the aligned hypothesis file "
              f"was not written. Rebuild the parallel corpus and rerun `merge`.")
        return

    out_path = TRANSLIT_DIR / corpus / f"{METHOD}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    empty = 0
    with src.open(encoding="utf-8") as fin, out_path.open("w", encoding="utf-8", newline="\n") as fout:
        for line in fin:
            rec = json.loads(line)
            hyp = merged.get(rec["sinhala"], "")
            empty += not hyp
            rec = {"id": rec["id"], "sinhala": rec["sinhala"], "hypothesis": hyp}
            records.append(rec)
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"wrote hypotheses -> {out_path.relative_to(PROJECT_ROOT)} "
          f"({empty:,} rows with empty output)")

    # The v->w rewrite is a preprocessing stage of this method, not an optional
    # extra, so it runs here rather than needing a separate command.
    from derive_nisansa_w import apply_to, write_variant
    rewritten, stats = apply_to(records)
    w_path = write_variant(corpus, rewritten)
    print(f"wrote v->w preprocessed -> {w_path.relative_to(PROJECT_ROOT)} "
          f"({stats['changed']:,} rewritten; {stats['collisions']:,} outputs already "
          f"contained a w, so the mapping is unambiguous)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command",
                    choices=["init", "seed", "status", "run", "reset",
                             "refetch-leaks", "merge"])
    ap.add_argument("--corpus", default=DEFAULT_CORPUS)
    ap.add_argument("--shard", type=int, help="which shard to run (see `status`)")
    ap.add_argument("--all", action="store_true", help="run every shard in turn")
    ap.add_argument("--shards", type=int, default=24, help="shard count, for `init`")
    ap.add_argument("--limit", type=int, help="stop after this many items per shard")
    ap.add_argument("--allow-repaired", action="store_true",
                    help="permit `seed` from a phonetic-repaired cache")
    ap.add_argument("--yes", action="store_true", help="confirm `reset`")
    args = ap.parse_args()

    if args.command == "init":
        cmd_init(args.corpus, args.shards)
    elif args.command == "seed":
        cmd_seed(args.corpus, args.allow_repaired)
    elif args.command == "status":
        cmd_status(args.corpus)
    elif args.command == "reset":
        cmd_reset(args.corpus, args.yes)
    elif args.command == "refetch-leaks":
        cmd_refetch_leaks(args.corpus)
    elif args.command == "merge":
        cmd_merge(args.corpus)
    else:
        if args.all:
            cmd_run_all(args.corpus, args.limit)
        elif args.shard is None:
            raise SystemExit("run requires --shard N or --all (see `status`)")
        else:
            with ShardLock(args.corpus, args.shard):
                cmd_run(args.corpus, args.shard, args.limit)
