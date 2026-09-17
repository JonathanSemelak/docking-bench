#!/usr/bin/env python
"""Cleaning waves for work/.

    python clean.py --report        # what is using space (default)
    python clean.py --wave 1        # safe: logs, temp files, __pycache__
    python clean.py --wave 2        # + the RCSB PDB cache (re-downloadable)
    python clean.py --wave 3        # + everything derived (forces a full re-prep)

Waves are cumulative and ordered by how expensive the thing is to recreate.
Wave 1 costs nothing. Wave 2 costs a re-download. Wave 3 costs a full re-prep
and is only for reclaiming space on a machine that is genuinely out.

Docked results are NEVER deleted by any wave -- they are the expensive thing,
and they are also the smallest.
"""
import argparse, shutil
from pathlib import Path

WORK = Path(__file__).parent / "work"

WAVES = {
    1: [("logs",        ["*.log", "*.tmp"],            "re-run to regenerate")],
    2: [("PDB cache",   ["pdb/*.pdb"],                 "re-downloaded by run_prep.py")],
    3: [("prepared",    ["receptor/*", "ligand/*", "reference/*", "prep.json"],
                                                        "full re-prep needed")],
}


def size_of(paths):
    return sum(p.stat().st_size for p in paths if p.is_file())


def collect(patterns):
    out = []
    for pat in patterns:
        out += [p for p in WORK.glob(pat) if p.is_file()]
    return out


def report():
    total = 0
    print(f"{'what':16s}{'size':>10s}   cost to recreate")
    for w in sorted(WAVES):
        for name, pats, cost in WAVES[w]:
            n = collect(pats)
            sz = size_of(n)
            total += sz
            print(f"  wave {w} {name:9s}{sz/1e6:8.1f} MB   {cost}  ({len(n)} files)")
    res = collect(["results/*"])
    print(f"  {'KEPT':6s} {'results':9s}{size_of(res)/1e6:8.1f} MB   "
          f"never deleted ({len(res)} files)")
    du = shutil.disk_usage(WORK)
    print(f"\nwork/ reclaimable: {total/1e6:.1f} MB    "
          f"disk free: {du.free/1e9:.1f} GB of {du.total/1e9:.0f} GB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wave", type=int, choices=[1, 2, 3])
    ap.add_argument("--report", action="store_true", help="show usage, delete nothing")
    ap.add_argument("--yes", action="store_true", help="skip confirmation")
    a = ap.parse_args()
    if a.report or not a.wave:
        return report()
    victims = []
    for w in range(1, a.wave + 1):
        for name, pats, _ in WAVES[w]:
            victims += collect(pats)
    if not victims:
        print("nothing to clean")
        return
    print(f"wave {a.wave}: {len(victims)} files, {size_of(victims)/1e6:.1f} MB")
    if not a.yes:
        if input("proceed? [y/N] ").strip().lower() != "y":
            print("aborted"); return
    freed = size_of(victims)
    for p in victims:
        p.unlink()
    for pc in WORK.parent.glob("__pycache__"):
        shutil.rmtree(pc, ignore_errors=True)
    print(f"freed {freed/1e6:.1f} MB, "
          f"{shutil.disk_usage(WORK).free/1e9:.1f} GB now free")


if __name__ == "__main__":
    main()
