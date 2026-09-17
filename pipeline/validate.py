#!/usr/bin/env python
"""Step 2 validation: can Vina reproduce the crystal poses we have?

Runs one standard condition (24 A box on the site centre, exhaustiveness 8)
for every ligand that has a complete crystal reference, and reports:

  top1   RMSD of the best-*scoring* pose      -- what a student would trust
  best   best RMSD anywhere in the pose list  -- whether the search found it

top1 < 2 A is a success. top1 large while best is small is the interesting
failure: the search found the right answer and the scoring function ranked it
below a wrong one. That distinction is the whole point of the exercise, so it
is reported rather than averaged away.

Note that only the ligand native to each reference receptor is a true
redocking; every other ligand is a cross-dock into a receptor that was
crystallised around something else, and is expected to be harder.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import dockbench as db

ROOT = Path(__file__).parent
WORK = ROOT / "work"
BOX, EXH, NP = 24.0, 8, 9


def main(cpu=0):
    man = {l["id"]: l for l in json.load(open(ROOT / "manifest.json"))["ligands"]}
    prep = json.load(open(WORK / "prep.json"))
    rows, t0 = [], time.time()
    print(f"{'target':7s}{'lig':6s}{'name':22s}{'native':7s}"
          f"{'score1':>8s}{'top1':>7s}{'best':>7s}{'rank*':>6s}  s")
    for key, L in prep["ligands"].items():
        if not L.get("referencePose"):
            continue
        tid, lid = L["target"], L["id"]
        T = prep["targets"][tid]
        native = T.get("pdbId") == L["sourcePdb"] or lid == \
            next(t["refLigand"] for t in json.load(open(ROOT/"manifest.json"))["targets"]
                 if t["id"] == tid)
        t1 = time.time()
        try:
            res = db.dock(WORK / T["receptorPdbqt"], WORK / f"ligand/{tid}_{lid}.pdbqt",
                          T["siteCenter"], [BOX] * 3, exhaustiveness=EXH,
                          n_poses=NP, cpu=cpu, seed=42)
            ref = db.rdkit_from_block(
                (WORK / f"reference/{tid}_{lid}.pdb").read_text(), man[lid]["smiles"])
            rms = []
            for sc, pose in res:
                try:
                    rms.append(db.best_rmsd(db.pose_to_mol(pose), ref))
                except Exception:
                    rms.append(float("nan"))
            top1 = rms[0]
            best = min(r for r in rms if r == r)
            rank = 1 + min(range(len(rms)), key=lambda i: rms[i] if rms[i] == rms[i] else 9e9)
            rows.append({"target": tid, "id": lid, "name": L["name"],
                         "native": bool(native), "score1": res[0][0],
                         "top1": top1, "best": best, "bestRank": rank,
                         "rmsds": rms, "scores": [r[0] for r in res]})
            print(f"{tid:7s}{lid:6s}{L['name'][:21]:22s}{'yes' if native else '-':7s}"
                  f"{res[0][0]:8.2f}{top1:7.2f}{best:7.2f}{rank:6d}  {time.time()-t1:.0f}")
        except Exception as e:
            print(f"{tid:7s}{lid:6s}{L['name'][:21]:22s} FAILED: {e}")
    json.dump(rows, open(WORK / "validation.json", "w"), indent=1)

    ok = [r for r in rows if r["top1"] < 2.0]
    rescued = [r for r in rows if r["top1"] >= 2.0 and r["best"] < 2.0]
    lost = [r for r in rows if r["best"] >= 2.0]
    print(f"\n--- {len(rows)} ligands, {time.time()-t0:.0f}s total ---")
    print(f"  top pose correct (<2 A)        : {len(ok):2d}  {[r['id'] for r in ok]}")
    print(f"  correct pose found but misranked: {len(rescued):2d}  {[r['id'] for r in rescued]}")
    print(f"  never found (<2 A)              : {len(lost):2d}  {[r['id'] for r in lost]}")
    nat = [r for r in rows if r["native"]]
    print(f"  cognate redocking (the real test): "
          f"{[(r['id'], round(r['top1'],2)) for r in nat]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(cpu=int(sys.argv[1]) if len(sys.argv) > 1 else 0))
