"""Core routines for building a real Docking Bench dataset.

Pipeline in three stages, each a separate script so the expensive one can be
array-jobbed on a cluster:

    run_prep.py   fetch structures, superpose onto the reference receptor,
                  write receptor/ligand PDBQT + the crystal reference pose
    run_dock.py   run the docking matrix (this is the slow one)
    build_data.py assemble data.json for the web app

Nothing here talks to the network except fetch_pdb(), which caches, so a
prepared work/ directory is self-contained and can be shipped to a cluster.
"""
from __future__ import annotations
import json, os, sys, urllib.request, warnings
from pathlib import Path
import numpy as np

warnings.filterwarnings("ignore")

RCSB = "https://files.rcsb.org/download/{}.pdb"

# ---------------------------------------------------------------- structures

def fetch_pdb(pdbid: str, cache: Path) -> Path:
    """Download a PDB file once and cache it."""
    cache.mkdir(parents=True, exist_ok=True)
    p = cache / f"{pdbid.upper()}.pdb"
    if not p.exists() or p.stat().st_size == 0:
        with urllib.request.urlopen(RCSB.format(pdbid.upper()), timeout=120) as r:
            p.write_bytes(r.read())
    return p


def load(path: Path):
    from Bio.PDB import PDBParser
    return PDBParser(QUIET=True).get_structure(path.stem, str(path))[0]


AA3 = {"ALA":"A","ARG":"R","ASN":"N","ASP":"D","CYS":"C","GLN":"Q","GLU":"E",
       "GLY":"G","HIS":"H","ILE":"I","LEU":"L","LYS":"K","MET":"M","PHE":"F",
       "PRO":"P","SER":"S","THR":"T","TRP":"W","TYR":"Y","VAL":"V",
       "MSE":"M","SEC":"U","PYL":"O"}


def ca_map(model, chain_id):
    """{residue number: CA coordinate} for one chain."""
    out = {}
    for res in model[chain_id]:
        if "CA" in res and res.id[0] == " ":
            out[res.id[1]] = res["CA"].get_coord()
    return out


def chain_seq(model, chain_id):
    """(one-letter sequence, [CA coords]) in residue order.

    Residue *numbers* are deliberately not used for matching. Different
    depositions of the same protein routinely use different conventions --
    EGFR structures appear both in mature numbering (1M17: 672-995) and in
    precursor numbering that includes the 24-residue signal peptide
    (4I22: 700-1014). Matching on number silently pairs the wrong residues.
    """
    seq, xyz = [], []
    for res in model[chain_id]:
        if res.id[0] != " " or "CA" not in res:
            continue
        seq.append(AA3.get(res.get_resname().strip(), "X"))
        xyz.append(res["CA"].get_coord())
    return "".join(seq), np.array(xyz)


def align_pairs(sa, sb):
    """Indices (ia, ib) of matched residues from a global sequence alignment."""
    from Bio import Align
    al = Align.PairwiseAligner(scoring="blastn" if False else None)
    al.mode = "global"
    al.open_gap_score, al.extend_gap_score = -11, -1
    al.substitution_matrix = Align.substitution_matrices.load("BLOSUM62")
    try:
        best = al.align(sa, sb)[0]
    except Exception:
        return [], []
    ia, ib = [], []
    for (a0, a1), (b0, b1) in zip(best.aligned[0], best.aligned[1]):
        for k in range(a1 - a0):
            if sa[a0 + k] == sb[b0 + k]:        # identities only
                ia.append(a0 + k); ib.append(b0 + k)
    return ia, ib


def kabsch(P, Q):
    """Rotation+translation taking P onto Q (both N x 3). Returns (R, t)."""
    pc, qc = P.mean(0), Q.mean(0)
    H = (P - pc).T @ (Q - qc)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1.0, 1.0, d])
    R = Vt.T @ D @ U.T
    return R, qc - R @ pc


def superpose(mobile_model, ref_model, mobile_chains, ref_chains, trim=2.0):
    """Best-fit mobile onto ref over sequence-aligned CA atoms.

    Chain permutations are tried because a homodimer like HIV-1 protease can
    be superposed two ways and only one is right. After the first fit, atoms
    further than `trim` angstrom are dropped and the fit repeated, so a
    hinge-bent domain or a disordered tail cannot drag the core off.

    Returns (R, t, rmsd, permutation, n_atoms).
    """
    import itertools
    best = None
    # A structure may hold more copies of the protein than the reference does
    # (4I24 is a dimer, 1M17 a monomer), so match subsets in both directions.
    n_pair = min(len(mobile_chains), len(ref_chains))
    combos = [(mp, rp)
              for mp in itertools.permutations(mobile_chains, n_pair)
              for rp in itertools.permutations(ref_chains, n_pair)]
    for mperm, perm in combos:
        P, Q = [], []
        for mc, rc in zip(mperm, perm):
            sm, xm = chain_seq(mobile_model, mc)
            sr, xr = chain_seq(ref_model, rc)
            im, ir = align_pairs(sm, sr)
            if len(im) < 30:
                continue
            P.append(xm[im]); Q.append(xr[ir])
        if not P:
            continue
        P, Q = np.vstack(P), np.vstack(Q)
        R, t = kabsch(P, Q)
        for _ in range(3):                       # iterative outlier rejection
            d = np.linalg.norm((P @ R.T + t) - Q, axis=1)
            keep = d < max(trim, np.percentile(d, 25))
            if keep.sum() < 30 or keep.all():
                break
            R, t = kabsch(P[keep], Q[keep])
        d = np.linalg.norm((P @ R.T + t) - Q, axis=1)
        keep = d < max(trim, np.percentile(d, 25))
        rms = float(np.sqrt((d[keep] ** 2).mean()))
        if best is None or rms < best[2]:
            best = (R, t, rms, perm, int(keep.sum()))
    if best is None:
        raise RuntimeError("no sequence correspondence found")
    return best


# ------------------------------------------------------------------ ligands

def ligand_atoms(model, resname):
    """All copies of a HETATM residue, as (chain, resid, [(name, element, xyz)])."""
    hits = []
    for ch in model:
        for res in ch:
            if res.get_resname().strip() == resname.strip():
                atoms = [(a.get_name(), a.element, a.get_coord())
                         for a in res if a.element != "H"]
                if atoms:
                    hits.append((ch.id, res.id[1], atoms))
    return hits


def pdb_block(atoms, resname, chain="L", resid=1, transform=None):
    """Column-correct HETATM block.

    Coordinates start at column 31 and the altLoc field at column 17 must be
    present even when blank -- omitting it shifts every coordinate one place
    left, which 3Dmol reports as a completely unrelated error about
    'symmetries'. Hence the explicit field widths below.
    """
    out = []
    for i, (name, elem, xyz) in enumerate(atoms, 1):
        if transform is not None:
            R, t = transform
            xyz = R @ np.asarray(xyz) + t
        x, y, z = xyz
        nm = name if len(name) >= 4 else f" {name:<3s}"
        out.append(
            f"HETATM{i:5d} {nm:<4s}{'':1s}{resname:>3s} {chain:1s}{resid:4d}{'':4s}"
            f"{x:8.3f}{y:8.3f}{z:8.3f}{1.0:6.2f}{0.0:6.2f}{'':10s}{elem:>2s}"
        )
    out.append("END")
    return "\n".join(out)


def rdkit_from_block(block, smiles):
    """Crystal coordinates + bond orders from the CCD SMILES."""
    from rdkit import Chem
    from rdkit.Chem import AllChem
    raw = Chem.MolFromPDBBlock(block, removeHs=True, sanitize=False)
    if raw is None:
        raise ValueError("could not parse ligand PDB block")
    ref = Chem.MolFromSmiles(smiles)
    if ref is None:
        raise ValueError(f"bad CCD SMILES: {smiles[:60]}")
    ref = Chem.RemoveHs(ref)
    try:
        return AllChem.AssignBondOrdersFromTemplate(ref, raw)
    except Exception as e:
        raise ValueError(f"bond-order assignment failed: {e}")


def best_rmsd(probe, ref):
    """Symmetry-corrected heavy-atom RMSD (RDKit GetBestRMS).

    Plain atom-order RMSD is wrong for anything with a symmetric group -- a
    flipped phenyl is chemically identical but scores several angstrom.
    """
    from rdkit import Chem
    from rdkit.Chem import rdMolAlign
    p, r = Chem.Mol(probe), Chem.Mol(ref)
    p = Chem.RemoveHs(p); r = Chem.RemoveHs(r)
    return float(rdMolAlign.CalcRMS(p, r))


# ------------------------------------------------------------------- docking

def box_contains(mol_or_atoms, centre, size, margin=0.0):
    """Does a pose fit inside the search box? Returns (fits, worst_overhang)."""
    xyz = np.asarray(mol_or_atoms, dtype=float)
    lo = np.asarray(centre) - np.asarray(size) / 2 + margin
    hi = np.asarray(centre) + np.asarray(size) / 2 - margin
    over = np.maximum(lo - xyz, 0).max(initial=0), np.maximum(xyz - hi, 0).max(initial=0)
    worst = float(max(over))
    return worst <= 0.0, worst


def dock(receptor_pdbqt, ligand_pdbqt, centre, size, exhaustiveness=8,
         n_poses=9, sf="vina", cpu=0, seed=42, spacing=0.375):
    """Run Vina and return [(score, pose_pdbqt_string), ...] best first."""
    from vina import Vina
    v = Vina(sf_name=sf, cpu=cpu, seed=seed, verbosity=0)
    v.set_receptor(str(receptor_pdbqt))
    v.set_ligand_from_file(str(ligand_pdbqt))
    v.compute_vina_maps(center=[float(x) for x in centre],
                        box_size=[float(x) for x in size], spacing=spacing)
    v.dock(exhaustiveness=exhaustiveness, n_poses=n_poses)
    en = np.atleast_2d(v.energies(n_poses=n_poses))
    blob = v.poses(n_poses=n_poses)
    chunks, cur = [], []
    for line in blob.splitlines():
        cur.append(line)
        if line.startswith("ENDMDL"):
            chunks.append("\n".join(cur)); cur = []
    if cur:
        chunks.append("\n".join(cur))
    return [(float(en[i][0]), chunks[i]) for i in range(min(len(chunks), len(en)))]


def pose_to_mol(pose_pdbqt):
    """Docked PDBQT pose -> RDKit mol with correct bond orders (via Meeko)."""
    from meeko import PDBQTMolecule, RDKitMolCreate
    pm = PDBQTMolecule(pose_pdbqt, is_dlg=False, skip_typing=True)
    mols = RDKitMolCreate.from_pdbqt_mol(pm)
    if not mols or mols[0] is None:
        raise ValueError("could not rebuild molecule from pose")
    return mols[0]


def pose_coords(pose_pdbqt):
    """Heavy-atom coordinates straight out of a PDBQT pose."""
    out = []
    for L in pose_pdbqt.splitlines():
        if L.startswith(("ATOM", "HETATM")):
            el = L[77:79].strip() or L[12:16].strip()[0]
            if el.upper() not in ("H", "HD", "HS"):
                out.append([float(L[30:38]), float(L[38:46]), float(L[46:54])])
    return np.array(out)
