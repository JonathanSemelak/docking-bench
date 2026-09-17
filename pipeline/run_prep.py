#!/usr/bin/env python
"""Stage 1: fetch structures, superpose, and prepare everything for docking.

Writes a self-contained work/ directory:
    work/pdb/          cached RCSB downloads
    work/receptor/     cleaned PDB + PDBQT per target
    work/ligand/       per-ligand PDBQT (docking input, from SMILES)
    work/reference/    crystal pose in the reference receptor frame
    work/prep.json     box definitions + per-ligand provenance

After this runs, nothing else needs the network.
"""
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
import dockbench as db

ROOT = Path(__file__).parent
WORK = ROOT / "work"
MAN = json.load(open(ROOT / "manifest.json"))


def clean_receptor(model, chains, out_pdb):
    """Protein-only PDB: drop waters, ions, ligands and alternate locations."""
    from Bio.PDB import PDBIO, Select

    class Prot(Select):
        def accept_chain(self, c):
            return c.id in chains
        def accept_residue(self, r):
            return r.id[0] == " "          # standard amino acids only
        def accept_atom(self, a):
            # keep the primary altLoc; a disordered side chain otherwise
            # produces duplicate atoms that confuse receptor preparation
            return (not a.is_disordered()) or a.get_altloc() in (" ", "A")

    io = PDBIO(); io.set_structure(model); io.save(str(out_pdb), Prot())


def protonate(inp, out):
    """Add hydrogens at pH 7 and rebuild missing side-chain atoms."""
    from pdbfixer import PDBFixer
    from openmm.app import PDBFile
    fx = PDBFixer(filename=str(inp))
    fx.findMissingResidues(); fx.missingResidues = {}   # no loop modelling
    fx.findNonstandardResidues(); fx.replaceNonstandardResidues()
    fx.removeHeterogens(keepWater=False)
    fx.findMissingAtoms(); fx.addMissingAtoms()
    fx.addMissingHydrogens(7.0)
    with open(out, "w") as fh:
        PDBFile.writeFile(fx.topology, fx.positions, fh, keepIds=True)
    return out


def fix_terminal_oxt(path):
    """Repair C-terminal carboxylate oxygens that PDBFixer places badly.

    PDBFixer sometimes puts OXT ~1.77 A from CA instead of the correct ~2.4 A,
    which is a distorted CA-C-OXT angle of about 78 deg rather than 117. The
    geometry is only slightly wrong, but RDKit's proximity-based bond
    perception then reads CA-OXT as a real bond, giving that carbon a valence
    of five and aborting receptor preparation. Rebuild OXT by mirroring O
    across the CA->C axis.
    """
    lines = Path(path).read_text().splitlines()
    res = {}
    for i, L in enumerate(lines):
        if L.startswith(("ATOM", "HETATM")):
            key = (L[21], L[22:27])
            res.setdefault(key, {})[L[12:16].strip()] = i

    def xyz(i):
        return np.array([float(lines[i][30 + 8 * k:38 + 8 * k]) for k in range(3)])

    fixed = 0
    for key, at in res.items():
        if not {"OXT", "C", "O", "CA"} <= set(at):
            continue
        CA, C, O = xyz(at["CA"]), xyz(at["C"]), xyz(at["O"])
        if np.linalg.norm(xyz(at["OXT"]) - CA) >= 2.1:
            continue                                   # already fine
        u = (C - CA) / np.linalg.norm(C - CA)
        v = O - C
        v_par = np.dot(v, u) * u
        new = C + (v_par - (v - v_par))
        new = C + (new - C) / np.linalg.norm(new - C) * 1.25
        i = at["OXT"]
        lines[i] = lines[i][:30] + f"{new[0]:8.3f}{new[1]:8.3f}{new[2]:8.3f}" + lines[i][54:]
        fixed += 1
    if fixed:
        Path(path).write_text("\n".join(lines) + "\n")
    return fixed


def receptor_pdbqt(pdb_in, basename):
    r = subprocess.run(["mk_prepare_receptor.py", "--read_pdb", str(pdb_in),
                        "-o", str(basename), "-p", "-a"],
                       capture_output=True, text=True)
    out = Path(str(basename) + ".pdbqt")
    if not out.exists():
        raise RuntimeError(f"receptor prep failed:\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
    return out


def ligand_pdbqt(smiles, out_path, seed=0xD0CC):
    """3D ligand from SMILES -> PDBQT, via RDKit ETKDG + Meeko.

    Docking input deliberately comes from SMILES, not from the crystal
    coordinates: starting the search from the answer would flatter every
    score in the benchmark.
    """
    from rdkit import Chem
    from rdkit.Chem import AllChem
    from meeko import MoleculePreparation, PDBQTWriterLegacy

    base = Chem.MolFromSmiles(smiles)
    if base is None:
        raise RuntimeError(f"unparseable SMILES: {smiles[:60]}")
    n = base.GetNumAtoms()

    # Meeko can fail on a molecule purely because of the order its atoms are
    # numbered in -- a terminal alkyne written first (erlotinib's canonical
    # SMILES starts "C#C...") raises "list.remove(x): x not in list", while
    # the identical molecule written another way prepares fine. Renumbering
    # is chemically a no-op, so retry with the atoms in a different order
    # rather than dropping the ligand.
    orders = [None, list(range(n))[::-1], list(range(1, n)) + [0]]
    last = None
    for order in orders:
        try:
            mol = base if order is None else Chem.RenumberAtoms(base, order)
            m = Chem.AddHs(mol)
            ps = AllChem.ETKDGv3(); ps.randomSeed = seed
            if AllChem.EmbedMolecule(m, ps) != 0:
                ps.useRandomCoords = True
                if AllChem.EmbedMolecule(m, ps) != 0:
                    raise RuntimeError("embedding failed")
            AllChem.MMFFOptimizeMolecule(m, maxIters=2000)
            setup = MoleculePreparation()(m)[0]
            txt, ok, err = PDBQTWriterLegacy.write_string(setup)
            if not ok:
                raise RuntimeError(f"meeko writer: {err}")
            Path(out_path).write_text(txt)
            return out_path
        except Exception as e:
            last = e
    raise RuntimeError(f"ligand prep failed after {len(orders)} atom orderings: {last}")


def main():
    for d in ("pdb", "receptor", "ligand", "reference"):
        (WORK / d).mkdir(parents=True, exist_ok=True)
    cache = WORK / "pdb"
    ligs_by_t = {}
    for l in MAN["ligands"]:
        ligs_by_t.setdefault(l["target"], []).append(l)

    out = {"targets": {}, "ligands": {}}

    for tgt in MAN["targets"]:
        tid, pdbid = tgt["id"], tgt["pdbId"]
        print(f"\n=== {tid}  reference receptor {pdbid} ===")
        ref_model = db.load(db.fetch_pdb(pdbid, cache))
        chains = [c.id for c in ref_model if len(db.ca_map(ref_model, c.id)) > 50]
        print(f"  protein chains: {chains}")

        raw = WORK / "receptor" / f"{tid}_raw.pdb"
        clean_receptor(ref_model, chains, raw)
        prot = protonate(raw, WORK / "receptor" / f"{tid}_h.pdb")
        nfix = fix_terminal_oxt(prot)
        if nfix:
            print(f"  repaired {nfix} misplaced OXT")
        rec = receptor_pdbqt(prot, WORK / "receptor" / tid)
        print(f"  receptor PDBQT: {rec.name} ({rec.stat().st_size//1024} KB)")

        # box centre = centroid of the native ligand in this structure
        native = db.ligand_atoms(ref_model, tgt["refLigand"])
        centre = np.array([a[2] for a in native[0][2]]).mean(0)

        # blind box = whole protein plus a margin
        allxyz = np.array([a.get_coord() for ch in ref_model if ch.id in chains
                           for r in ch for a in r])
        lo, hi = allxyz.min(0) - 5, allxyz.max(0) + 5

        out["targets"][tid] = {
            **{k: tgt[k] for k in ("id", "name", "pdbId", "siteLabel", "blurb")},
            "chains": chains,
            "receptorPdbqt": str(rec.relative_to(WORK)),
            "receptorPdb": str(Path(prot).relative_to(WORK)),
            "siteCenter": [round(float(x), 3) for x in centre],
            "blindCenter": [round(float(x), 3) for x in (lo + hi) / 2],
            "blindSize": [round(float(x), 1) for x in (hi - lo)],
        }
        print(f"  site centre {centre.round(2)}   blind box {(hi-lo).round(1)}")

        for l in ligs_by_t[tid]:
            lid = l["id"]
            try:
                mob = db.load(db.fetch_pdb(l["sourcePdb"], cache))
                mchains = [c.id for c in mob if len(db.ca_map(mob, c.id)) > 50]
                R, t, rms, perm, n = db.superpose(mob, ref_model, mchains, chains)
                copies = db.ligand_atoms(mob, lid)
                if not copies:
                    raise RuntimeError(f"ligand {lid} not found in {l['sourcePdb']}")
                # pick the copy closest to the reference site after transform
                best, bestd = None, 1e9
                for ch, rid, atoms in copies:
                    c = (np.array([a[2] for a in atoms]) @ R.T + t).mean(0)
                    d = float(np.linalg.norm(c - centre))
                    if d < bestd:
                        best, bestd = (ch, rid, atoms), d
                blk = db.pdb_block(best[2], lid, transform=(R, t))
                # A crystal copy can be incomplete: disordered atoms are simply
                # never modelled. Dacomitinib, for instance, has no complete
                # copy anywhere in the PDB (22/33 and 28/33 atoms). Such a
                # ligand is still perfectly dockable -- it just has no usable
                # ground-truth pose, so RMSD is undefined and the app shows no
                # green overlay rather than a misleading one.
                n_modelled = len(best[2])
                complete = n_modelled >= l["heavyAtoms"]
                rec = {**l, "alignCA": round(rms, 3), "alignN": n,
                       "chainPerm": "".join(perm), "siteDist": round(bestd, 2),
                       "modelledAtoms": n_modelled, "ok": True}
                if complete:
                    mol = db.rdkit_from_block(blk, l["smiles"])
                    (WORK / "reference" / f"{tid}_{lid}.pdb").write_text(blk)
                    rec["referencePose"] = True
                    rec["refAtoms"] = mol.GetNumAtoms()
                else:
                    rec["referencePose"] = False
                    rec["refNote"] = (f"crystal copy incomplete "
                                      f"({n_modelled}/{l['heavyAtoms']} heavy atoms)")
                ligand_pdbqt(l["smiles"], WORK / "ligand" / f"{tid}_{lid}.pdbqt")
                out["ligands"][f"{tid}_{lid}"] = rec
                flag = "" if complete else f"  NO REF ({n_modelled}/{l['heavyAtoms']})"
                print(f"   {lid:4s} {l['name']:20s} CA={rms:5.3f}A n={n:3d} "
                      f"site_d={bestd:5.2f}A{flag}")
            except Exception as e:
                out["ligands"][f"{tid}_{lid}"] = {**l, "ok": False, "error": str(e)}
                print(f"   {lid:4s} {l['name']:20s} FAILED: {e}")

    json.dump(out, open(WORK / "prep.json", "w"), indent=1)
    good = sum(1 for v in out["ligands"].values() if v.get("ok"))
    print(f"\nprepared {good}/{len(out['ligands'])} ligands -> {WORK/'prep.json'}")
    return 0 if good == len(out["ligands"]) else 1


if __name__ == "__main__":
    sys.exit(main())
