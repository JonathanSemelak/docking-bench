#!/usr/bin/env python
"""Stage 3: assemble ../data.json for the web app.

    python build_data.py                    # single setup, the app's original schema
    python build_data.py --setup vinardo
    python build_data.py --multi            # all setups, requires the app to support them

The single-setup form emits exactly the schema the app already reads, so real
numbers can replace the synthetic ones without touching index.html. --multi
adds a `setups` list and turns each ligand's `poses` into `runs`, which needs
the newer viewer.
"""
from __future__ import annotations
import argparse, glob, gzip, json
from pathlib import Path
import numpy as np
import dockbench as db

ROOT = Path(__file__).parent
WORK = ROOT / "work"
OUT = ROOT.parent / "data.json"

# Ki/IC50 values are quoted from the primary literature for context only; they
# are not used in any calculation.
EXPERIMENTAL = {
    "MK1": "Ki 0.56 nM", "ROC": "Ki 0.12 nM", "017": "Kd 4.5 pM",
    "RIT": "Ki 15 pM", "478": "Ki 0.6 nM", "AB1": "Ki 1.3 pM",
    "TPV": "Ki 8 pM", "1UN": "Ki 2 nM", "DR7": "Ki 0.19 nM",
    "AQ4": "IC50 2 nM", "IRE": "IC50 33 nM", "FMM": "IC50 10.8 nM",
    "YY3": "IC50 12 nM", "HKI": "IC50 92 nM", "0WN": "IC50 0.5 nM",
    "1C9": "IC50 6 nM", "AEE": "IC50 2 nM",
}


AD_TO_ELEMENT = {
    "A": "C", "C": "C", "N": "N", "NA": "N", "NS": "N",
    "O": "O", "OA": "O", "OS": "O", "S": "S", "SA": "S",
    "P": "P", "F": "F", "CL": "Cl", "BR": "Br", "I": "I",
    "MG": "Mg", "CA": "Ca", "MN": "Mn", "FE": "Fe", "ZN": "Zn",
}


def pdbqt_to_pdb(pose, resname, chain="L", resid=1):
    """PDBQT pose -> column-correct PDB HETATM block.

    Coordinates begin at column 31 and the altLoc field at column 17 must be
    present even when blank. Getting this wrong shifts every coordinate one
    place left and makes 3Dmol fail with an error about 'symmetries' that
    says nothing about columns.
    """
    out, i = [], 0
    for L in pose.splitlines():
        if not L.startswith(("ATOM", "HETATM")):
            continue
        el = L[77:79].strip()
        if el.upper() in ("HD", "HS", "H"):
            continue
        # Meeko breaks macrocycles to make them flexible and marks the break
        # with glue atoms: G* are pseudo-atoms that exist only to close the
        # ring during search and must not reach the viewer, while CG* are the
        # real ring carbons either side of the break.
        if el.upper().startswith("G"):
            continue
        if el.upper().startswith("CG"):
            el = "C"
        # AutoDock types are not element symbols: A is aromatic carbon, and
        # NA/OA/SA are hydrogen-bond-accepting N/O/S. Mapping by first letter
        # turns A into the non-existent element "A", which RDKit rejects and
        # 3Dmol renders as nothing.
        el = AD_TO_ELEMENT.get(el.upper(), "".join(c for c in el if c.isalpha())[:2] or "C")
        i += 1
        name = L[12:16].strip() or el
        nm = name if len(name) >= 4 else f" {name:<3s}"
        x, y, z = float(L[30:38]), float(L[38:46]), float(L[46:54])
        out.append(f"HETATM{i:5d} {nm:<4s}{'':1s}{resname:>3s} {chain:1s}{resid:4d}"
                   f"{'':4s}{x:8.3f}{y:8.3f}{z:8.3f}{1.0:6.2f}{0.0:6.2f}"
                   f"{'':10s}{el:>2s}")
    return "\n".join(out)


def contacts(pose_pdbqt, receptor_pdb, cutoff=4.0):
    """Residues with any heavy atom within `cutoff` of the pose."""
    lig = db.pose_coords(pose_pdbqt)
    if not len(lig):
        return []
    res = {}
    for L in Path(receptor_pdb).read_text().splitlines():
        if not L.startswith("ATOM") or L[76:78].strip() == "H":
            continue
        key = f"{L[17:20].strip()}{L[22:26].strip()}{L[21]}"
        res.setdefault(key, []).append([float(L[30:38]), float(L[38:46]), float(L[46:54])])
    hits = []
    for key, xyz in res.items():
        d = np.linalg.norm(lig[:, None, :] - np.array(xyz)[None, :, :], axis=2).min()
        if d < cutoff:
            hits.append((d, key))
    return [k for _, k in sorted(hits)][:8]


def load_results():
    R = {}
    for f in sorted(glob.glob(str(WORK / "results" / "*.json.gz"))):
        with gzip.open(f, "rt") as fh:
            R.update(json.load(fh))
    return R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", default="standard")
    ap.add_argument("--multi", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    prep = json.load(open(WORK / "prep.json"))
    man = json.load(open(ROOT / "manifest.json"))
    setups = {s["id"]: s for s in json.load(open(ROOT / "setups.json"))["setups"]}
    R = load_results()
    have = sorted({v["setup"] for v in R.values() if "setup" in v})
    use = have if a.multi else [a.setup]
    missing = [s for s in use if s not in have]
    if missing:
        raise SystemExit(f"no results for setup(s) {missing}; have {have}")

    targets = []
    for T in man["targets"]:
        tid = T["id"]
        P = prep["targets"][tid]
        rec_pdb = WORK / "receptor" / f"{tid}_raw.pdb"
        pdb_data = "\n".join(L for L in rec_pdb.read_text().splitlines()
                             if L.startswith(("ATOM", "TER")))
        ligands = []
        for L in man["ligands"]:
            if L["target"] != tid:
                continue
            key = f"{tid}_{L['id']}"
            pl = prep["ligands"][key]
            entry = {
                "id": L["id"], "name": L["name"],
                "provenance": (L["provenance"] or
                               f"crystal pose from {L['sourcePdb']}"),
                "isNative": L["id"] == T["refLigand"],
                "heavyAtoms": L["heavyAtoms"],
                "experimental": EXPERIMENTAL.get(L["id"]),
                "sourcePdb": L["sourcePdb"],
                "covalent": L["covalent"],
            }
            ref_file = WORK / "reference" / f"{tid}_{L['id']}.pdb"
            if pl.get("referencePose") and ref_file.exists():
                entry["referencePose"] = ref_file.read_text().replace("\nEND", "")
            elif pl.get("refNote"):
                entry["referenceNote"] = pl["refNote"]

            def poses_for(sid):
                r = R.get(f"{key}|{sid}")
                if not r or "error" in r:
                    return None, r
                out = []
                for p in r["poses"]:
                    d = {"rank": p["rank"], "score": p["score"],
                         "pdb": pdbqt_to_pdb(p["pdbqt"], L["id"])}
                    if p.get("rmsdToRef") is not None:
                        d["rmsdToRef"] = p["rmsdToRef"]
                    d["ligandEfficiency"] = round(abs(p["score"]) / L["heavyAtoms"], 3)
                    if p["rank"] == 1:
                        d["contacts"] = contacts(p["pdbqt"], rec_pdb)
                    out.append(d)
                return out, r

            if a.multi:
                runs = []
                for sid in use:
                    ps, r = poses_for(sid)
                    if ps is None:
                        continue
                    runs.append({"setupId": sid, "poses": ps,
                                 "refInBox": r.get("refInBox"),
                                 "box": {"center": r["center"], "size": r["size"]},
                                 "seconds": r.get("seconds")})
                if not runs:
                    continue
                entry["runs"] = runs
            else:
                ps, r = poses_for(a.setup)
                if ps is None:
                    continue
                entry["poses"] = ps
                entry["refInBox"] = r.get("refInBox")
            ligands.append(entry)

        s = setups[use[0]]
        box_c = R[f"{tid}_{ligands[0]['id']}|{use[0]}"]["center"] if not a.multi \
            else P["siteCenter"]
        box_s = R[f"{tid}_{ligands[0]['id']}|{use[0]}"]["size"] if not a.multi \
            else [24.0] * 3
        targets.append({
            "id": tid, "name": T["name"], "blurb": T["blurb"],
            "siteLabel": T["siteLabel"], "pdbId": T["pdbId"],
            "pdbData": pdb_data,
            "box": {"center": [round(x, 2) for x in box_c],
                    "size": [round(x, 1) for x in box_s]},
            "ligands": ligands,
        })

    data = {
        "generated": ("AutoDock Vina 1.2.5, real runs. "
                      + (f"setups: {', '.join(use)}" if a.multi
                         else f"setup: {a.setup} ({setups[a.setup]['label']})")),
        "provenance": {
            "engine": "AutoDock Vina 1.2.5",
            "receptorPrep": "PDBFixer pH 7.0, waters removed, Meeko",
            "ligandPrep": "RDKit ETKDGv3 from CCD SMILES, MMFF94, Meeko",
            "rmsd": "symmetry-corrected heavy-atom RMSD (RDKit CalcRMS)",
            "caveats": [
                "Poses are docked from SMILES, not from crystal coordinates.",
                "All waters were removed. In 1HSG this deletes HOH 308, which "
                "bridges both Ile50 flap NH groups 2.68 A from indinavir and is "
                "contacted by every peptidomimetic protease inhibitor here.",
                "Only indinavir and erlotinib are native to their reference "
                "receptor; the other 18 ligands are cross-docked.",
                "Osimertinib, neratinib, dacomitinib and afatinib bind EGFR "
                "covalently at Cys797 but are docked non-covalently.",
            ],
        },
        "targets": targets,
    }
    if a.multi:
        data["setups"] = [setups[s] for s in use]
    Path(a.out).write_text(json.dumps(data, separators=(",", ":")))
    n = sum(len(t["ligands"]) for t in targets)
    print(f"wrote {a.out}  ({Path(a.out).stat().st_size/1e6:.2f} MB, "
          f"{len(targets)} targets, {n} ligands, setups={use})")


if __name__ == "__main__":
    main()
