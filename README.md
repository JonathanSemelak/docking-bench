# Docking Bench

**Live: https://jonathansemelak.github.io/docking-bench/**

A static, precomputed docking demo for teaching. Students pick a target and a
ligand, see the pose in 3D, and compare scores — with no server, no install,
and nothing to compute at runtime.

## Files

| File | What it is |
|---|---|
| `docking-bench-standalone.html` | Everything in one file. Double-click to open. No server needed. |
| `index.html` + `data.json` | The same app, split. Use this for hosting and for swapping in your own data. |
| `analogs.json` | 96 precomputed analogs of the quinazoline core. |
| `pipeline/` | Everything needed to regenerate `data.json` from real Vina runs. See its own README. |
| `GUIA-ACTIVIDADES.md` | A 90-minute classroom activity guide, in Spanish, covering both tabs. |
| `GUIA-ACTIVIDADES-CLAVE.md` | The answer key for it. Every number checked against the dataset. Do not hand out. |
| `GUIA-ACTIVIDADES.pdf` | The same guide as a fillable PDF form — students type into it and save. |
| `GUIA-ACTIVIDADES-CLAVE.pdf` | The answer key as a PDF. Do not hand out. |
| `guia.html` | The guide as a styled web page with fill-in fields, servable next to `index.html`. |
| `build_guia_pdf.py`, `build_clave_pdf.py` | Regenerate the two PDFs. Need `reportlab`. |

`data.json` is produced by `pipeline/`, which is in this repo and runs offline
once prepared. `analogs.json` was built by an RDKit enumeration script that is
not included; the section on it below describes the method rather than a file
you can run.

## Try it first

Open `docking-bench-standalone.html` in a browser. Two targets are included:

- **HIV-1 protease** (1HSG) with ten inhibitors — all nine FDA-approved
  protease inhibitors plus the cyclic urea DMP323
- **EGFR kinase** (1M17) with ten inhibitors — erlotinib, gefitinib, lapatinib,
  osimertinib, afatinib, neratinib, dacomitinib, AEE788, TAK-285 and a
  pyrrolotriazine

**Every score and pose is real AutoDock Vina 1.2.5 output**, produced by the
pipeline in `pipeline/`. Crystal reference poses come from the best-resolution
structure of each ligand (darunavir from 2HS1 at 0.84 A) superposed into the
reference receptor frame. RMSD is symmetry-corrected.

Only indinavir and erlotinib are native to their reference receptor. The other
eighteen are cross-docks into a receptor crystallised around something else,
which is the realistic case and the harder one.

**One caveat to state in class:** all waters were removed during receptor
preparation. In 1HSG that deletes HOH 308, which bridges both Ile50 flap NH
groups 2.68 A from indinavir and is contacted by every peptidomimetic protease
inhibitor in the set. It is a standard thing to do and a real handicap, and the
cyclic urea DMP323 is the one ligand designed to be indifferent to it.

## The teaching hook

Nothing here is staged. **Erlotinib docked into 1M17 — its own crystal
structure — scores -7.22 for a pose 7.90 A from the answer, while the pose that
reproduces the crystal at 1.43 A ranks fifth and scores worse.** That holds
across exhaustiveness 8, 32 and 64 and three random seeds, so it is not a
sampling accident: Vina finds the right pose every time and ranks four wrong
ones above it.

What makes that trustworthy rather than alarming is the control. Indinavir,
run through the identical pipeline, redocks to 0.60 A at rank 1.

Switching the scoring function to Vinardo pulls erlotinib to 3.08 A and
atazanavir from 11.56 A to 1.30 A, without changing the search at all. That is
the lesson in one click: the failure is in the scoring, not the searching.

### The setup selector

Eight conditions ship with the dataset, and switching between them is the
exercise. Median top-1 RMSD over the ligands that have a crystal reference:

| Setup | median RMSD | crystal pose outside the box |
|---|---|---|
| Tight box, 18 A | 5.75 | 6 |
| Standard, 24 A, exh 8 | 7.01 | 2 |
| Standard box, exh 32 | 7.90 | 2 |
| Loose box, 34 A | 7.87 | 0 |
| Mis-centred by 6 A | 8.69 | 10 |
| Vinardo scoring | 4.98 | 2 |
| Blind, whole protein | 8.94 | 0 |
| **Standard + flap water** (HIV only) | **3.70** | 0 |

Two of those rows are worth dwelling on. **Searching harder does not help** --
exhaustiveness 32 is no better than 8, because the search was never the problem.
And **mis-centring the box by 6 A gets nothing right at all**, largely because
for ten ligands it puts the answer outside the box entirely; the app says so
rather than letting that read as a scoring failure.

### What one water molecule does

The biggest single improvement in the whole dataset comes from *preparation*,
not from any docking parameter. Restoring the conserved waters that bridge the
Ile50 flaps to the ligand halves the median error on HIV-1 protease:

| Ligand | Dry | + water |
|---|---|---|
| Saquinavir | 10.21 | **2.43** |
| Ritonavir | 11.76 | **3.34** |
| Darunavir | 4.78 | 3.74 |
| Amprenavir | 4.50 | 3.67 |
| DMP323 | 6.14 | 4.36 |
| Indinavir | 0.60 | 0.61 |
| **Tipranavir** | **2.31** | **10.77** |

Tipranavir is the one that gets *worse*, and it is the one that should: it is a
non-peptidic inhibitor that contacts the flap NH groups directly and displaces
that water rather than binding through it. Putting the water back blocks it.
The cyclic urea DMP323 displaces the same water and does not follow the
pattern, so treat this as one clean case rather than a tidy two-class result --
which is itself a fair thing to show students about real data.

The waters are not hand-picked. `pipeline/prep_wet.py` keeps any water within
3.6 A of the native ligand that also makes at least two polar contacts to
protein, which is the usual working definition of a bridging water. In 1HSG
that selects three, including HOH 308 at 2.68 A. In 1M17 it selects none, so
EGFR has no wet variant and the setup is skipped for that target rather than
silently docked against a different receptor.

The lapatinib case is real too. Lapatinib binds an inactive,
αC-helix-out conformation of EGFR (1XKK); 1M17 is closer to active. Cross-docking
into the wrong receptor conformation is one of the standard ways docking fails,
and the back-pocket contacts (Lys721, Glu738) make it visible.


## Classroom guide (Spanish)

[`GUIA-ACTIVIDADES.md`](GUIA-ACTIVIDADES.md) is a ready-to-run 90-minute activity
guide in Spanish: 45 minutes in the Pose tab, 35 in Design, 10 to close. It walks
students from the indinavir control through the erlotinib scoring failure, the
mis-centred box, Vinardo, the flap water, and the score-versus-potency table,
then has them build erlotinib from the bare core and dock their own analogs.

[`GUIA-ACTIVIDADES-CLAVE.md`](GUIA-ACTIVIDADES-CLAVE.md) is the teacher's copy:
every expected value, the discussion answers, a timing plan, and the objections
that come up in the room. All of its numbers were read out of `data.json` and
`analogs.json` rather than remembered, so regenerating the data means rechecking
the key.

The guide quotes every button and column label in English, as they appear in the
app, so nothing has to be translated in the room.

The material is branded for the **Universidad Siglo 21** team teaching
*Diseñá tu propio fármaco*, and carries no timings — pace it however the session
runs. The teacher key keeps a suggested schedule.

It ships in three shapes, all with the same content:

- `GUIA-ACTIVIDADES.md` — the source to read and edit.
- `guia.html` — a styled page whose tables are fill-in fields; answers are kept
  in the student's own browser, and a block at the end of B3 builds the rows to
  paste into the shared class spreadsheet. Serve it next to `index.html`.
- `GUIA-ACTIVIDADES.pdf` — a **fillable PDF form**: 101 named text fields, so
  students type into it in Acrobat Reader, macOS Preview or the browser's own
  viewer and save a copy. Field names match the input ids of the HTML version.

Regenerate the PDFs with `python3 build_guia_pdf.py` and
`python3 build_clave_pdf.py`. **Each script holds its own copy of the text and
does not read the markdown**, so a change to the guide has to be made in the
markdown, in `guia.html` and in the matching script.

## Design mode

The second tab turns the same pocket into a medicinal-chemistry exercise.

Students start from the **4-anilinoquinazoline core** that erlotinib and
gefitinib share, and hang substituents off two vectors that point in opposite
directions:

- **R1**, the aniline meta position, aims into the hydrophobic back pocket past
  the Thr766 gatekeeper. Small and greasy is rewarded; wide is punished.
- **R2**, the quinazoline 6-position, leaves the ATP cleft toward solvent. It is
  where you spend polarity for free.

Twelve R1 groups x eight R2 groups = 96 analogs, every one enumerated ahead of
time with a 2D depiction and real RDKit descriptors (MW, cLogP, TPSA, HBD/HBA,
rotatable bonds, Fsp3). R1 substituents are highlighted blue in the drawing, R2
in amber, so it is obvious what just changed.

Two cells are landmarks: `ethynyl + 2-methoxyethoxy` **is** erlotinib, exactly,
and students reach it in two clicks. That moment — "wait, I just drew a real
drug" — is worth more than any slide.

### Suggestions and coaching

The chips under the structure ("Make it bigger here", "Something more polar",
"Add an H-bond donor", "Add a ring") re-sort or filter the analog gallery for
the **active vector** using the precomputed descriptors. Nothing is hardcoded
per molecule; it all falls out of the numbers.

The line above the chips reacts to what the student has built — flagging a bulky
group aimed at the gatekeeper, polarity buried in a greasy pocket, a greasy
group wasted on solvent, or a molecule that has drifted past MW 500. The rules
live in `coachFor()` in `index.html` and are short enough to rewrite for your
own scaffold.


### Viewing

The pocket panel in Design mode has an **Expand** button that hands the 3D view
the whole screen; Escape or Close returns it. The viewer element is physically
moved between mount points rather than duplicated, so camera state and the
surface survive the trip.

Surface generation is asynchronous and takes a second or two. The viewer draws a
cartoon immediately and swaps it for the surface once that lands, so the panel is
never blank while it computes -- and if surface generation fails outright, the
cartoon simply stays. A translucent surface with ribbon showing through it reads
as mud, which is why the two are never drawn together.

In-flight surfaces are tagged with a sequence number so that rapidly switching
ligand or mode discards stale results instead of stacking them.

### A note on the 2D drawings

RDKit centres a molecule on a fixed canvas, so an elongated molecule like a
quinazoline leaves roughly a third of the canvas height empty. In a layout whose
height is the binding constraint, that dead margin is exactly what makes the
drawing look small. The build step therefore measures the true content
bounds of each SVG and retargets the `viewBox` to them, so every drawing carries
its own aspect ratio and fills whatever box CSS gives it. If you regenerate and
the structures suddenly look tiny again, that cropping step is the first thing
to check.

### The Dock button

Design mode has a **Dock this analog** button with a progress bar. The
four-second pause doing "Generating conformers / Searching the pocket /
Scoring poses" is doing real pedagogical work — it is the only moment in the
lesson that conveys docking costs something, which is why there is no way to
skip it.

The score is honest about itself. If an analog in `analogs.json` has a `score`
field, that number is shown with a green **vina** tag. If it does not, the app
synthesises a deterministic placeholder from size and polarity and labels it
**mock** in amber, with a line under it saying so. Nothing silently pretends to
be a docking result.

**All 96 analogs now carry real scores**, docked into 1M17 by
`pipeline/dock_analogs.py`, so the amber tag should not appear. The control is
built in: `CCH|MEO` is erlotinib exactly, and it scores -7.25 against the -7.21
that the same molecule gets in the main dataset -- 0.04 kcal/mol apart, by two
independent paths through the pipeline.

Scores stay cached for the session and appear on the gallery cards, so students
can dock several analogs and compare them side by side.

To swap in real numbers, add one field per analog:

```jsonc
"analogs": {
  "CCH|MEO": { "r1":"CCH", "r2":"MEO", "score": -8.94, ... }
}
```

The keys are `R1id|R2id`, using the R-group ids listed under `vectors` in
`analogs.json`. Dock the 96 SMILES with Vina + Meeko, then write the top score of
each into the matching key.

### Building your own scaffold

Swapping in a different scaffold means writing a short RDKit enumeration script
that emits `analogs.json` in the shape the app reads. The pieces it needs:

- a **template SMILES** with `{R1}` / `{R2}` placeholders. Keep placeholders inside
  branches, and number any rings in your R-groups from 4 upward so they do not
  collide with the scaffold's ring closures.
- the **two substituent lists**. Hydrogen is `[H]`, not an empty string.
- `scaffold.vectors` — the pocket context text students read.
- the **landmark cells** worth naming.

```bash
pip install rdkit
```

Two things that will bite you. Check one depiction renders before you ship 96 of
them. And if you minify the SVGs — worth it, ~17 KB down to ~7 KB each —
collapsing whitespace too aggressively welds `<svg` to its first attribute and
every drawing silently disappears.

## Pocket surface

Both modes can show a molecular surface of the residues within 9 Å of the
ligand, coloured by residue class:

| Colour | Class |
|---|---|
| Gold | Hydrophobic (Ala, Val, Leu, Ile, Met, Phe, Trp, Pro, Gly, Cys) |
| Green | Polar (Ser, Thr, Asn, Gln, Tyr) |
| Blue | Basic (Arg, Lys, His) |
| Red | Acidic (Asp, Glu) |

### Pocket residues, by H-bond role

The other pocket view names the residues lining the site and colours them by
what they can do in a hydrogen bond, which is the question the surface cannot
answer:

| Colour | Role | What to hang off your vector |
|---|---|---|
| Red | Accepts (Asp, Glu) | an N-H or O-H |
| Blue | Donates (Arg, Lys, Trp) | an N or O |
| Purple | Either (Ser, Thr, Tyr, Asn, Gln, His, Cys) | either |
| Gold | Hydrophobic | something greasy |

Backbone N-H and C=O do both everywhere, which is why the hinge contact works
and why the backbone is not coloured per residue.

The shell is computed from whatever ligand is on screen, so in Design mode it
follows the analog the student just built rather than the native ligand. Only
the polar residues are labelled -- a 5 A shell holds twenty-odd residues and
naming all of them buries the view, while the greasy ones read from colour
alone. On HIV-1 protease the Asp25/Asp25' dyad shows up as two red side chains
directly under the ligand; on EGFR the Thr766 gatekeeper and Lys721 in the back
pocket are both named.

Available in both tabs. The surface and the residue sticks are alternatives
rather than layers, because sticks poking through a translucent surface reads
as mud.

**The surface is residue-class colouring, not electrostatics.** It is computed in the
browser from a lookup table, so it costs nothing and is honest about what it
shows: where the greasy walls and the charged patches are. A real electrostatic
potential map (APBS/PB solver) would need precomputed grids and is a different
job. For "what should I grow into this space", the residue view is the one
students can actually reason from — and on HIV-1 protease the Asp25/Asp25'
dyad shows up as a red patch directly under the ligand, which makes the point
better than any caption.


## Data schema

Each ligand can carry several docking **setups** — different box sizes,
centres, search depths or scoring functions. When `data.json` has a top-level
`setups` list, each ligand's poses live under `runs` and the app shows a setup
selector; with a single setup it uses `poses` directly and the selector is
hidden, so both shapes work.

```jsonc
{
  "setups": [{ "id":"standard", "label":"Standard, 24 A, exh 8",
               "box":24, "exhaustiveness":8, "scoring":"vina", "center":"site" }],
  "targets": [{
    "id": "hivpr",
    "name": "HIV-1 protease",
    "blurb": "Shown next to the ligand list.",
    "siteLabel": "Asp25 / Asp25' dyad",
    "pdbData": "ATOM      1  N   PRO A   1 ...",  // receptor, bundled
    "pdbId": "1HSG",                              // fallback: fetch from RCSB
    "box": { "center": [13.07, 22.47, 5.56], "size": [24, 24, 24] },
    "ligands": [{
      // with several setups, poses move under runs:
      //   "runs": [{ "setupId":"standard", "refInBox":true, "poses":[...] }]
      // refInBox records whether the crystal pose was even inside the search
      // box, so a large RMSD is never mistaken for a scoring failure when the
      // box simply ruled the right answer out.
      "id": "MK1",
      "name": "Indinavir",
      "provenance": "native ligand of this structure",
      "isNative": true,
      "heavyAtoms": 45,
      "experimental": null,          // e.g. "Ki 0.56 nM" — shows in the panel
      "referencePose": "HETATM ...", // crystal pose, drawn in green
      "poses": [{
        "rank": 1,
        "score": -10.46,             // kcal/mol
        "rmsdToRef": 0.0,            // Å, vs referencePose
        "ligandEfficiency": 0.232,
        "contacts": ["ASP25B", "ASP25A"],  // top pose only
        "pdb": "HETATM ..."
      }]
    }]
  }]
}
```

Only `name`, `poses[].score`, and `poses[].pdb` are strictly required. Anything
missing degrades gracefully — no reference pose just means no green overlay.

The app tries `fetch('./data.json')` first and falls back to the copy embedded
in the HTML, so the same file works served *and* opened directly.

### One trap worth knowing

Ligand PDB blocks must be column-correct. Coordinates start at **column 31**,
and it is easy to forget the single-character altLoc field at column 17 — which
shifts every coordinate one place left and makes 3Dmol fail with an unhelpful
`Cannot read properties of undefined (reading 'symmetries')`. Use a PDB writer that
respects the fixed columns rather than assembling the lines with string
formatting of your own.

## Using your own targets

1. Prepare each receptor once, by hand. This is where docking quality is won or
   lost — strip waters and buffer components, add hydrogens at the right pH,
   decide what to do with metals and cofactors.
   ```bash
   reduce receptor.pdb > receptor_h.pdb
   mk_prepare_receptor.py -i receptor_h.pdb -o receptor
   ```
2. Decide the search box — centre and size — and collect your ligand SMILES,
   plus a reference SDF for any ligand with a known crystal pose.
3. Dock them and write the results out in the schema below. Budget roughly
   10–60 s per ligand at exhaustiveness 16.
   ```bash
   pip install vina meeko rdkit numpy
   ```
4. Drop the new `data.json` next to `index.html`.

To find a box centre, take the centroid of a known bound ligand. A 22–26 Å cube
is usually right for a well-defined pocket; much larger and scores get noisy.

## Publishing it so other people can use it

The whole thing is static files, so "hosting" just means putting a folder on the
web. GitHub Pages is the shortest path and is free.

**If you just want a link, fast:** upload only
`docking-bench-standalone.html` — it is entirely self-contained.

1. Create a GitHub account if you do not have one, then make a new **public**
   repository, e.g. `docking-bench`.
2. On the repo page choose **Add file -> Upload files** and drag in
   `index.html`, `data.json`, and `analogs.json`. Commit.
3. Go to **Settings -> Pages**. Under "Build and deployment", set Source to
   **Deploy from a branch**, branch `main`, folder `/ (root)`. Save.
4. Wait a minute or two. Your site appears at
   `https://<username>.github.io/docking-bench/`.

The file must be named `index.html` for step 4 to serve it at the bare URL. If
you upload the standalone file under its own name, the link is
`https://<username>.github.io/docking-bench/docking-bench-standalone.html` —
which works, but renaming it to `index.html` gives you a much nicer URL to put
on a slide.

Updating later means uploading a new `data.json` over the old one; the page
picks it up on the next reload. Note that GitHub Pages caches aggressively, so
tell students to hard-refresh if you push a change mid-lesson.

**Alternatives, same effort:** Netlify and Cloudflare Pages both let you drag a
folder onto a web page and get a URL back without touching git. Netlify Drop
(`app.netlify.com/drop`) is the fastest of all — no account needed for a
temporary link.

**Do not** email the standalone HTML as an attachment. At 1.3 MB it will
survive, but most mail clients strip or sandbox HTML attachments and the
students will not be able to open it.

## Deploying (reference)

Any static host works — there is no backend.

**Cloudflare Pages or Netlify:** push the folder to a repo and connect it.
Drag-and-drop deploy also works if you'd rather not use git.

**GitHub Pages:** push to a repo, then Settings → Pages → deploy from branch.
Fine for this app, since nothing here needs custom headers. (It would *not* be
fine if you later added in-browser Vina via Webina, which needs COOP/COEP
headers that GitHub Pages cannot set.)

`data.json` is ~490 KB raw but ~98 KB gzipped, which every one of these hosts
does automatically.

**In the room:** put a QR code to the URL on your first slide. And keep the
standalone HTML on a USB stick — it needs no network at all, which has saved
more than one demo.

## Running locally

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

Or just double-click `docking-bench-standalone.html`.

## Credits

Structures from the RCSB PDB: 1HSG, 1HXB, 2IEN, 1HPX, 1HVR, 1M17, 2ITY, 1XKK,
2J6M. Rendering by [3Dmol.js](https://3dmol.csb.pitt.edu/). Swap in Mol* if you
want higher-end representations; the data schema doesn't care which viewer reads it.
