#!/usr/bin/env python
"""Build a receptor variant that keeps conserved structural waters.

Docking normally strips every water, which is standard practice and, for some
targets, a real handicap. HIV-1 protease is the textbook case: a single water
bridges the two Ile50 flap NH groups to the ligand, and every peptidomimetic
inhibitor in this set hydrogen-bonds to it. The cyclic ureas were designed
specifically to displace it.

A water is kept when it looks structural rather than incidental:

  - within `LIG_CUT` of the native ligand, and
  - donating or accepting to at least `MIN_PROT` protein N/O atoms

which is the usual working definition of a bridging water and keeps the
decision out of the hands of whoever is running the script.

Writes <target>_wet.pdbqt and records it in prep.json as receptorPdbqtWet.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import dockbench as db
from run_prep import protonate, fix_terminal_oxt, receptor_pdbqt

ROOT = Path(__file__).parent
WORK = ROOT / "work"
LIG_CUT, PROT_CUT, MIN_PROT = 3.6, 3.5, 2


def conserved_waters(model, chains, lig_xyz):
    """Waters bridging the ligand to at least MIN_PROT protein polar atoms."""
    prot = np.array([a.get_coord() for ch in model if ch.id in chains
                     for r in ch if r.id[0] == " " for a in r
                     if a.element in ("N", "O")])
    keep = []
    for ch in model:
        for r in ch:
            if r.get_resname() != "HOH" or "O" not in r:
                continue
            w = r["O"].get_coord()
            if np.linalg.norm(lig_xyz - w, axis=1).min() > LIG_CUT:
                continue
            n = int((np.linalg.norm(prot - w, axis=1) < PROT_CUT).sum())
            if n >= MIN_PROT:
                keep.append((ch.id, r.id[1], w, n))
    return keep


def main():
    prep = json.load(open(WORK / "prep.json"))
    man = json.load(open(ROOT / "manifest.json"))
    changed = False
    for T in man["targets"]:
        tid = T["id"]
        P = prep["targets"][tid]
        model = db.load(db.fetch_pdb(T["pdbId"], WORK / "pdb"))
        chains = P["chains"]
        lig = np.array([a[2] for a in db.ligand_atoms(model, T["refLigand"])[0][2]])
        keep = conserved_waters(model, chains, lig)
        print(f"{tid} ({T['pdbId']}): {len(keep)} conserved water(s)")
        for ch, rid, w, n in keep:
            d = float(np.linalg.norm(lig - w, axis=1).min())
            print(f"   HOH {rid} chain {ch}: {d:.2f} A from ligand, "
                  f"{n} protein polar contacts")
        if not keep:
            print("   -> no wet variant for this target")
            continue

        # protein + the kept waters, then the usual preparation
        raw = WORK / "receptor" / f"{tid}_raw.pdb"
        lines = [L for L in raw.read_text().splitlines() if L.startswith(("ATOM", "TER"))]
        for i, (ch, rid, w, n) in enumerate(keep, 1):
            lines.append(
                f"HETATM{90000+i:5d}  O   HOH W{i:4d}    "
                f"{w[0]:8.3f}{w[1]:8.3f}{w[2]:8.3f}{1.0:6.2f}{0.0:6.2f}"
                f"{'':10s}{'O':>2s}")
        wet_raw = WORK / "receptor" / f"{tid}_wet_raw.pdb"
        wet_raw.write_text("\n".join(lines) + "\nEND\n")

        # PDBFixer would delete the waters again via removeHeterogens, so the
        # protein is protonated on its own and the waters are appended after.
        prot = protonate(raw, WORK / "receptor" / f"{tid}_wet_h.pdb")
        fix_terminal_oxt(prot)
        txt = [L for L in Path(prot).read_text().splitlines()
               if L.startswith(("ATOM", "TER"))]
        for i, (ch, rid, w, n) in enumerate(keep, 1):
            txt.append(
                f"HETATM{90000+i:5d}  O   HOH W{i:4d}    "
                f"{w[0]:8.3f}{w[1]:8.3f}{w[2]:8.3f}{1.0:6.2f}{0.0:6.2f}"
                f"{'':10s}{'O':>2s}")
        Path(prot).write_text("\n".join(txt) + "\nEND\n")
        try:
            rec = receptor_pdbqt(prot, WORK / "receptor" / f"{tid}_wet")
        except Exception as e:
            print(f"   receptor prep failed, skipping wet variant: {str(e)[:200]}")
            continue
        P["receptorPdbqtWet"] = str(rec.relative_to(WORK))
        P["waters"] = [{"chain": c, "resid": int(r), "ligandDist": round(
            float(np.linalg.norm(lig - w, axis=1).min()), 2), "protContacts": n}
            for c, r, w, n in keep]
        changed = True
        print(f"   -> {rec.name}")
    if changed:
        json.dump(prep, open(WORK / "prep.json", "w"), indent=1)
        print("\nprep.json updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
