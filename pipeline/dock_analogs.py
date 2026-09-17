#!/usr/bin/env python
"""Dock the Design-tab analogs for real and write scores into analogs.json.

The app shows a green "vina" tag when an analog carries a `score` field and an
amber "mock" tag when it has to synthesise one, so filling these in is what
turns the design exercise from a plausible-looking game into something backed
by the same engine as the rest of the dataset.

    python dock_analogs.py                 # all 96, resumable
    python dock_analogs.py --limit 4       # a quick check first

CCH|MEO is erlotinib exactly, so its score should land on top of the AQ4 score
in the main dataset. That is the built-in control and it is checked at the end.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import dockbench as db
from run_prep import ligand_pdbqt

ROOT = Path(__file__).parent
WORK = ROOT / "work"
ANALOGS = ROOT.parent / "analogs.json"
TMP = WORK / "analogs"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--cpu", type=int, default=0)
    ap.add_argument("--exhaustiveness", type=int, default=8)
    ap.add_argument("--box", type=float, default=24.0)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()

    TMP.mkdir(parents=True, exist_ok=True)
    A = json.load(open(ANALOGS))
    prep = json.load(open(WORK / "prep.json"))
    tid = A["scaffold"].get("target", "egfr")
    T = prep["targets"][tid]
    rec = WORK / T["receptorPdbqt"]

    keys = [k for k in A["analogs"] if a.redo or "score" not in A["analogs"][k]]
    if a.limit:
        keys = keys[:a.limit]
    print(f"{len(keys)} analogs to dock into {tid} ({T['pdbId']}), "
          f"{a.box} A box, exhaustiveness {a.exhaustiveness}")

    t0 = time.time()
    for i, k in enumerate(keys, 1):
        an = A["analogs"][k]
        try:
            lp = TMP / (k.replace("|", "_") + ".pdbqt")
            if not lp.exists():
                ligand_pdbqt(an["smiles"], lp)
            res = db.dock(rec, lp, T["siteCenter"], [a.box] * 3,
                          exhaustiveness=a.exhaustiveness, n_poses=5,
                          cpu=a.cpu, seed=42)
            an["score"] = round(res[0][0], 2)
            an["scoreSource"] = "vina"
            print(f"  [{i}/{len(keys)}] {k:14s} {an.get('name') or '':22s} "
                  f"{an['score']:7.2f}", flush=True)
        except Exception as e:
            an["scoreError"] = str(e)[:200]
            print(f"  [{i}/{len(keys)}] {k:14s} FAILED: {str(e)[:90]}", flush=True)
        if i % 10 == 0 or i == len(keys):
            json.dump(A, open(ANALOGS, "w"), separators=(",", ":"))

    json.dump(A, open(ANALOGS, "w"), separators=(",", ":"))
    done = [v for v in A["analogs"].values() if "score" in v]
    print(f"\n{len(done)}/{len(A['analogs'])} analogs scored in {time.time()-t0:.0f}s")

    # control: CCH|MEO is erlotinib, so it should match AQ4 in the main set
    erl = A["analogs"].get("CCH|MEO", {}).get("score")
    if erl is not None:
        import gzip, glob
        R = {}
        for f in glob.glob(str(WORK / "results" / "*.json.gz")):
            with gzip.open(f, "rt") as fh:
                R.update(json.load(fh))
        ref = R.get("egfr_AQ4|standard")
        if ref and "poses" in ref:
            d = abs(erl - ref["poses"][0]["score"])
            print(f"control: CCH|MEO (erlotinib) {erl:.2f} vs AQ4 in main set "
                  f"{ref['poses'][0]['score']:.2f}  -> {d:.2f} kcal/mol apart "
                  f"{'OK' if d < 0.5 else 'CHECK THIS'}")
    if done:
        ss = sorted(v["score"] for v in done)
        print(f"score range: {ss[0]:.2f} to {ss[-1]:.2f} kcal/mol")


if __name__ == "__main__":
    main()
