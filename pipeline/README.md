# Docking Bench pipeline

Builds a real, reproducible docking dataset for the Docking Bench web app:
20 ligands across two targets, docked under several deliberately different
protocols so students can see how much the *setup* moves the answer.

## Install

```bash
conda env create -f env.yaml
conda activate dockbench
```

## Run

```bash
python run_prep.py          # fetch + superpose + prepare   (needs network, ~5 min)
python validate.py          # sanity check: can Vina reproduce known poses?
python run_dock.py          # the docking matrix            (the slow one)
python build_data.py        # assemble ../data.json
```

`run_prep.py` is the only stage that touches the network. Once `work/` exists
it is self-contained and can be copied to a cluster.

## What is in the set

Twenty ligands, every (ligand, PDB) pair verified against RCSB:

- **HIV-1 protease**, reference receptor **1HSG** — all nine FDA-approved
  protease inhibitors plus the cyclic urea DMP323. Crystal poses come from the
  best-resolution structure of each (darunavir from 2HS1 at 0.84 A).
- **EGFR kinase domain**, reference receptor **1M17** — erlotinib, gefitinib,
  lapatinib, osimertinib, afatinib, neratinib, dacomitinib, AEE788, TAK-285 and
  a pyrrolotriazine.

Only indinavir (HIV-1 protease) and erlotinib (EGFR) are *native* to their
reference receptor. Everything else is a cross-dock into a receptor that was
crystallised around a different molecule, which is the realistic case and the
harder one.

## Things worth knowing

**Numbering is not a reliable way to match residues.** EGFR structures appear
both in mature numbering (1M17: 672-995) and in precursor numbering that
includes the 24-residue signal peptide (4I22: 700-1014). Matching on residue
number pairs the wrong amino acids and produces a 21 A "superposition" that
still looks like a successful fit. Alignment here is sequence-based.

**Crystal ligands can be incomplete.** Dacomitinib has no complete copy
anywhere in the PDB (22/33 and 28/33 heavy atoms in 4I23 and 4I24). It is still
docked, but it carries no reference pose and therefore no RMSD, rather than a
misleading partial one.

**PDBFixer sometimes misplaces OXT**, putting it ~1.77 A from CA instead of
~2.4. RDKit then perceives a CA-OXT bond, that carbon reaches valence five, and
receptor preparation dies with a message that says nothing about termini.
`fix_terminal_oxt()` rebuilds it.

**The tight box excludes the answer.** An 18 A box on the EGFR site centre does
not contain the crystal pose of six of the nine EGFR ligands; even 24 A clips
neratinib and the pyrrolotriazine. That is a legitimate thing to show students,
but the dataset records whether the reference pose was inside the box for each
run, so "docking got it wrong" is never confused with "the right answer was not
reachable".

**Docking input comes from SMILES, not from the crystal coordinates.** Starting
the search from the answer would flatter every number in the benchmark.

**Four of the EGFR ligands are covalent** (osimertinib, neratinib, dacomitinib,
afatinib all target Cys797). They are docked non-covalently, like any other
ligand, which is not how they actually bind. The manifest flags them.
