# SA1 ART — AlphaFold Server job package

Prepared 7 October 2026. **29 submission jobs; 19 distinct molecular compositions.**
No models have been run or submitted by this package's author.

## Submit the right files

The four JSON files at the package root and all JSON files in `individual_jobs/`
are AlphaFold Server inputs. Every file is a top-level JSON array, including the
single-job files. They use `dialect: alphafoldserver`, `version: 1`, and one string
seed per submission. They are not native local-AlphaFold-3-dialect inputs.

Do not upload `provenance/manifest.json` to AlphaFold. It is documentation, not a job.
Use the combined file OR its component batches; uploading both duplicates jobs.

| Submission file | Jobs | When to run |
|---|---:|---|
| `01_core_5jobs.json` | 5 | First: RT, candidate partner, and the 1:1 RT–partner hypothesis at three seeds. |
| `02_exploratory_RNA_16jobs.json` | 16 | Optional: four window-defined RNAs, each alone, with RT, with partner, and with both. |
| `03_optional_RNA_seed_repeats_8jobs.json` | 8 | Optional: two additional seeds for each ternary RNA hypothesis. |
| `all_29_jobs.json` | 29 | Convenience aggregate; equivalent to the three batches together. |

“Core” does not mean experimentally established. Only the protein sequences are
verified here. A one-copy input is a modeling choice, not proof of native stoichiometry.
If only experimentally supported interaction shots are acceptable, use the protein
monomer predictions as labeled predictions and the existing experimental comparison
structures below; do not treat any ART complex prediction as solved biology.

## Verified protein sequences

| Asset | Accession | Length | CDS coordinates, 1-based inclusive, positive strand |
|---|---|---:|---|
| ART RT candidate | QPI16926.1 | 501 aa | MW218148.1:10647–12152 |
| Immediately downstream candidate partner | QPI16927.1 | 265 aa | MW218148.1:12154–12951 |

The archived GenBank record labels both products “hypothetical protein.” The ART
role assignment follows the locus identified in the public ART replication, rather
than being a product label supplied by the original GenBank submitter. Physical
interaction and native assembly remain unverified.

Both coding sequences were translated with genetic code 11 and matched exactly
to their GenBank protein translations. The stop codons are not submitted. No tags,
mutations, truncations, artificial linkers, or PTMs have been introduced. The RT has
YADD at residues 366–369; this is a sequence annotation, not a demonstration of activity.

## RNA inputs: explicit genomic-window hypothesis

**These are not verified mature ART RNA sequences.** They are exact genomic
segments converted from DNA to RNA (T → U), with deliberately chosen repeat-to-repeat
boundaries. A high-confidence fold cannot establish that those endpoints are biological.

Five 14-nt near-motif starts were found in the upstream tract:
9598, 9810, 9981, 10182, and 10358. The core is `ATATGAATACGTAT`; the first and fifth
instances each have one substitution. Four complete internal windows are supplied:

| RNA | Genome coordinates, 1-based inclusive | Length | Definition |
|---|---|---:|---|
| W1 | MW218148.1:9598–9809 (+) | 212 nt | Motif 1 start to immediately before motif 2. |
| W2 | MW218148.1:9810–9980 (+) | 171 nt | Motif 2 start to immediately before motif 3. |
| W3 | MW218148.1:9981–10181 (+) | 201 nt | Motif 3 start to immediately before motif 4. |
| W4 | MW218148.1:10182–10357 (+) | 176 nt | Motif 4 start to immediately before motif 5. |

The final unit is omitted because its 3′ endpoint was not verified. The linked
paper PDF could not be fully retrieved, so no exact author-supplied mature RNA
endpoints or supplementary prediction inputs were recovered. Transcript processing,
terminal chemical states, modifications and RNA function are not encoded as facts.
Replace these inputs with experimentally delimited transcripts before claiming native
RNA structures. For now, label renders “predicted genomic-window RNA” or “hypothetical
ART assembly; RNA endpoints unverified.”

## Full composition list

| ID | Name | Ordered entities | Total polymer residues | Seeds supplied |
|---|---|---|---:|---|
| 01 | RT_QPI16926 | SA1_RT | 501 | 101 |
| 02 | PARTNER_QPI16927 | SA1_PARTNER | 265 | 101 |
| 03 | HYP_RT_PARTNER_1to1 | SA1_RT, SA1_PARTNER | 766 | 101, 202, 303 |
| 04 | EXPL_RNA_W1_9598_9809 | SA1_RNA_W1 | 212 | 101 |
| 05 | EXPL_RNA_W2_9810_9980 | SA1_RNA_W2 | 171 | 101 |
| 06 | EXPL_RNA_W3_9981_10181 | SA1_RNA_W3 | 201 | 101 |
| 07 | EXPL_RNA_W4_10182_10357 | SA1_RNA_W4 | 176 | 101 |
| 08 | HYP_RT_RNA_W1 | SA1_RT, SA1_RNA_W1 | 713 | 101 |
| 09 | HYP_RT_RNA_W2 | SA1_RT, SA1_RNA_W2 | 672 | 101 |
| 10 | HYP_RT_RNA_W3 | SA1_RT, SA1_RNA_W3 | 702 | 101 |
| 11 | HYP_RT_RNA_W4 | SA1_RT, SA1_RNA_W4 | 677 | 101 |
| 12 | HYP_PARTNER_RNA_W1 | SA1_PARTNER, SA1_RNA_W1 | 477 | 101 |
| 13 | HYP_PARTNER_RNA_W2 | SA1_PARTNER, SA1_RNA_W2 | 436 | 101 |
| 14 | HYP_PARTNER_RNA_W3 | SA1_PARTNER, SA1_RNA_W3 | 466 | 101 |
| 15 | HYP_PARTNER_RNA_W4 | SA1_PARTNER, SA1_RNA_W4 | 441 | 101 |
| 16 | HYP_RT_PARTNER_RNA_W1 | SA1_RT, SA1_PARTNER, SA1_RNA_W1 | 978 | 101, 202, 303 |
| 17 | HYP_RT_PARTNER_RNA_W2 | SA1_RT, SA1_PARTNER, SA1_RNA_W2 | 937 | 101, 202, 303 |
| 18 | HYP_RT_PARTNER_RNA_W3 | SA1_RT, SA1_PARTNER, SA1_RNA_W3 | 967 | 101, 202, 303 |
| 19 | HYP_RT_PARTNER_RNA_W4 | SA1_RT, SA1_PARTNER, SA1_RNA_W4 | 942 | 101, 202, 303 |

The largest job contains 978 polymer residues/nucleotides. Each listed entity has
`count: 1`. Expected input order is RT, partner, then RNA when present, but verify
output chain IDs by sequence rather than assuming chain letters.

## Why these compositions

The monomers provide full-length molecular portraits. The binary protein hypothesis
supplies a possible partner-interface composition. RNA-only jobs support the repertoire
shot. Comparing RT–RNA, partner–RNA, and RT–partner–RNA helps identify which contact
arrangements are consistent across these conditional predictions; it does not prove
binding or infer a physiological assembly pathway. No negative controls or biochemical
experiments are included, and this is not a validated interaction screen.

Seeds 101/202/303 are merely fixed, valid model seeds, not selected for favorable
outcomes. The binary protein hypothesis and ternary hypotheses have three independent
seed requests. Other compositions have one seed in this package. Additional seed
outputs are alternative predictions, not time points, thermal fluctuations, or a
molecular-dynamics trajectory. Inspect them before deciding whether any are suitable
for a clearly labeled illustration.

## Models that do NOT need new AlphaFold jobs

Use existing experimental coordinates for the established-system comparison shots:

- **6AR1:** group II intron RT with RNA–DNA template/primer and incoming dATP.
- **9LM3 / EMD-63214:** Retron-Eco2 triangular assembly.
- **8QBM / EMD-18315:** Retron-Eco1 filament comparison.

These are not ART structures. Preserve their assembly information, ligands and chemical
topology. For the 6AR1 reaction illustration, review the trapped primer-end chemistry
against the original paper before making a reactive model.

No ART job contains an invented DNA primer, dNTP, catalytic metal stoichiometry, or
an asserted retron-style RNA–DNA crosslink. The linked Server schema has a restricted
ligand list; `CCD_DTP` (dATP in 6AR1) is not on that documented list. `CCD_ATP` is not a
chemically equivalent substitute. Simple DNA overview geometry should be built from
sequence with a nucleic-acid modeling tool rather than spending these AF jobs on it.

## Save and review the results

Keep the complete Server result ZIP for each job, including every returned CIF,
confidence JSON, summary-confidence JSON, input request, and output terms. Do not
retain only screenshots or only the winning structure. Exact filenames can vary by
Server version.

Review local fold confidence (pLDDT), domain positioning (PAE), chain-pair interface
confidence where available, serious clashes and chain topology. In ternary jobs,
inspect the protein–RNA interfaces separately: a good global score can be dominated
by the protein–protein arrangement. Seed agreement is supporting consistency only;
no confidence cutoff establishes biochemical binding or validates RNA endpoints.
Do not turn a low-confidence interface into a precise residue-contact animation.

## Commercial-use caveat

AlphaFold Server output terms restrict commercial use of outputs and derivatives.
A professionally commissioned Blender render is not automatically exempt merely
because the inputs are public sequences. Confirm that the intended organization,
use, and distribution are permitted before running or using predictions. This package
does not grant rights to AlphaFold outputs. Read the Server's current output terms,
not only the repository code license. This is a rights check, not a legal opinion.

## Local validation

Run from this folder with Python 3.10+ (standard library only):

```bash
python validate_jobs.py
```

Validation checks JSON structure, sequence alphabets, string seeds, counts, asset
hashes, nucleotide coordinates, the two complete CDS translations, repeat-window
boundaries, identical individual/batch inputs, and unique job names. It does not
submit jobs or prove server-side acceptance or biological validity.

## Provenance and sources

Original genome accession: MW218148.1. Its archived flatfile was retrieved through
the GitHub connector, not directly downloaded anew from NCBI. Pinned archive:

https://github.com/forresthu/artmine/blob/4d72381142519fc4ead259a94f37896b4d1baaf5/data/groundtruth/MW218148.1.gb

Archive commit: `4d72381142519fc4ead259a94f37896b4d1baaf5`.
Reported full GenBank Git blob SHA: `e796e06c76c3f65ce8563c5826179dae0d39e74f`.
The included excerpt contains original genome coordinates 9421–13020. Protein FASTA,
exploratory RNA FASTA, all individual sequence SHA-256 values and the full job manifest
are under `provenance/`. The primary SA1 characterization independently identifies
MW218148 as the deposited genome.

Source URLs (accessed 2026-10-07):

1. Server input schema: https://github.com/google-deepmind/alphafold/blob/main/server/README.md
2. Archived genome: https://github.com/forresthu/artmine/blob/4d72381142519fc4ead259a94f37896b4d1baaf5/data/groundtruth/MW218148.1.gb
3. Public ART replication/locus assignment: https://github.com/forresthu/artmine/blob/4d72381142519fc4ead259a94f37896b4d1baaf5/README.md
4. SA1 original characterization: https://pmc.ncbi.nlm.nih.gov/articles/PMC9096886/
5. Anthropic ART announcement: https://www.anthropic.com/news/claude-discovers-novel-enzyme-system
6. User's ART paper (full retrieval unsuccessful): https://www-cdn.anthropic.com/22573675ada52a8ca8a97a1a4b4326b2f208a071.pdf
7. AF3 confidence definitions: https://github.com/google-deepmind/alphafold3/blob/main/docs/output.md
8. Server output terms: https://alphafoldserver.com/output-terms
9. 6AR1: https://www.rcsb.org/structure/6AR1
10. 9LM3: https://www.rcsb.org/structure/9LM3
11. 8QBM: https://www.rcsb.org/structure/8QBM
