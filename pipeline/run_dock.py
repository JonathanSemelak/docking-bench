#!/usr/bin/env python
"""Stage 2: run the docking matrix. This is the slow stage.

    python run_dock.py                      # everything, serially
    python run_dock.py --setups standard    # one condition
    python run_dock.py --shard 3/16         # for an HPC array job

Each shard writes work/results/<shard>.json; build_data.py merges whatever is
present, so a partial matrix still produces a usable dataset.

Threading note: at exhaustiveness 8 Vina only runs 8 independent searches and
cannot use many more than 8 threads, so throughput on a big node comes from
running several ligands at once with modest --cpu, not from one job with all
of them. Blind docking is the exception -- give it everything, and run it
serially, because a whole-protein box builds grid maps of roughly a gigabyte
and twenty of those at once will swap the machine to death.
"""
from __future__ import annotations
import argparse, gzip, json, os, shutil, time
from pathlib import Path
import numpy as np
import dockbench as db

ROOT = Path(__file__).parent
WORK = ROOT / "work"
N_POSES = 9


MIN_FREE_GB = 2.0


def free_gb(path):
    st = shutil.disk_usage(path)
    return st.free / 1e9


def check_disk(path, need=None):
    """Refuse to start another run when the disk is nearly full.

    Results are small (tens of KB per run), but this machine runs at 94%
    occupancy and a job that dies half-written is worse than one that stops
    cleanly, so every run checks before it writes.
    """
    need = MIN_FREE_GB if need is None else need
    g = free_gb(path)
    if g < need:
        raise SystemExit(f"ABORT: only {g:.1f} GB free on {path} "
                         f"(need {need} GB). Nothing written.")
    return g


def load_results(p):
    if p.exists():
        with gzip.open(p, "rt") as fh:
            return json.load(fh)
    plain = p.with_suffix("")          # migrate an older uncompressed shard
    if plain.suffix == ".json" and plain.exists():
        d = json.load(open(plain))
        plain.unlink()
        return d
    return {}


def save_results(p, d):
    tmp = p.with_suffix(".tmp")
    with gzip.open(tmp, "wt") as fh:
        json.dump(d, fh)
    tmp.replace(p)                     # atomic: never leave a half-written shard


def box_for(setup, T):
    if setup["center"] == "blind":
        return T["blindCenter"], T["blindSize"]
    c = list(T["siteCenter"])
    if setup["center"] == "offset":
        c = [c[i] + setup.get("offset", [0, 0, 0])[i] for i in range(3)]
    return c, [float(setup["box"])] * 3


def main():
    global MIN_FREE_GB
    ap = argparse.ArgumentParser()
    ap.add_argument("--setups", nargs="*", default=None)
    ap.add_argument("--ligands", nargs="*", default=None)
    ap.add_argument("--shard", default="1/1", help="k/N for array jobs")
    ap.add_argument("--cpu", type=int, default=0, help="0 = all cores")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--min-free-gb", type=float, default=MIN_FREE_GB,
                    help="abort rather than run below this much free disk")
    a = ap.parse_args()

    MIN_FREE_GB = a.min_free_gb
    k, n = (int(x) for x in a.shard.split("/"))
    prep = json.load(open(WORK / "prep.json"))
    man = {l["id"]: l for l in json.load(open(ROOT / "manifest.json"))["ligands"]}
    setups = json.load(open(ROOT / "setups.json"))["setups"]
    if a.setups:
        setups = [s for s in setups if s["id"] in a.setups]

    jobs = [(lk, s) for lk in prep["ligands"] for s in setups
            if prep["ligands"][lk].get("ok")
            and (not a.ligands or prep["ligands"][lk]["id"] in a.ligands)]
    jobs = jobs[k - 1::n]
    (WORK / "results").mkdir(exist_ok=True)
    out_path = WORK / "results" / f"shard{k:03d}of{n:03d}.json.gz"
    done = load_results(out_path)

    print(f"shard {k}/{n}: {len(jobs)} jobs ({len(done)} already done), "
          f"{free_gb(WORK):.1f} GB free")
    for i, (lk, s) in enumerate(jobs, 1):
        key = f"{lk}|{s['id']}"
        if key in done:
            continue
        check_disk(WORK)
        L = prep["ligands"][lk]
        T = prep["targets"][L["target"]]
        centre, size = box_for(s, T)
        # A setup may ask for a receptor variant (e.g. one that keeps the
        # conserved waters). Targets without that variant are skipped rather
        # than silently docked against the wrong receptor.
        rec_key = "receptorPdbqt" + s.get("receptor", "").capitalize()
        if rec_key not in T:
            print(f"  [{i}/{len(jobs)}] {lk:12s} {s['id']:9s} "
                  f"skipped: no '{s.get('receptor')}' receptor for this target",
                  flush=True)
            continue
        receptor = WORK / T[rec_key]
        t0 = time.time()
        try:
            res = db.dock(receptor,
                          WORK / f"ligand/{L['target']}_{L['id']}.pdbqt",
                          centre, size, exhaustiveness=s["exhaustiveness"],
                          n_poses=N_POSES, sf=s["scoring"], cpu=a.cpu, seed=a.seed)
            ref = None
            if L.get("referencePose"):
                ref = db.rdkit_from_block(
                    (WORK / f"reference/{L['target']}_{L['id']}.pdb").read_text(),
                    man[L["id"]]["smiles"])
            poses = []
            for rank, (sc, pose) in enumerate(res, 1):
                rec = {"rank": rank, "score": round(sc, 3), "pdbqt": pose}
                if ref is not None:
                    try:
                        rec["rmsdToRef"] = round(db.best_rmsd(db.pose_to_mol(pose), ref), 3)
                    except Exception:
                        rec["rmsdToRef"] = None
                poses.append(rec)
            # was the right answer even reachable in this box?
            ref_in_box = None
            if L.get("referencePose"):
                xyz = db.pose_coords((WORK / f"reference/{L['target']}_{L['id']}.pdb").read_text())
                ref_in_box = bool(db.box_contains(xyz, centre, size)[0])
            done[key] = {"ligand": lk, "setup": s["id"], "center": list(map(float, centre)),
                         "size": list(map(float, size)), "refInBox": ref_in_box,
                         "receptor": s.get("receptor") or "apo",
                         "seconds": round(time.time() - t0, 1), "poses": poses}
            r0 = poses[0].get("rmsdToRef")
            print(f"  [{i}/{len(jobs)}] {lk:12s} {s['id']:9s} "
                  f"score={poses[0]['score']:7.2f} rmsd1={r0 if r0 is not None else '-':>6} "
                  f"inbox={ref_in_box} {time.time()-t0:5.0f}s", flush=True)
        except Exception as e:
            done[key] = {"ligand": lk, "setup": s["id"], "error": str(e)}
            print(f"  [{i}/{len(jobs)}] {lk:12s} {s['id']:9s} FAILED: {e}", flush=True)
        save_results(out_path, done)
    sz = out_path.stat().st_size / 1e6 if out_path.exists() else 0
    print(f"wrote {out_path.name} ({sz:.1f} MB), {free_gb(WORK):.1f} GB free")


if __name__ == "__main__":
    main()
