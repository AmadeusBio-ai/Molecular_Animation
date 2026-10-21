# ART: a hidden repertoire of RNA

## Request (owner, 2026-10-17)

> "finish the CRISPR-like animation"

Follow-up (owner, 2026-10-17): "add motions like brownian motion to the molecule to make it look more realistic ... think about molecularly of how everything should move, search in depth, then output based on an accurate schematic." Version 2 (`record.md`, `docs/motion.md`).

- **Source documents:** `sources/CRISPR-Like.txt` (the brief, AI-generated), `sources/af3-job-package/` (the AlphaFold Server inputs and the SA1 genome excerpt) and `af3/` (the owner's AlphaFold Server results). Provenance and the public facts the captions rely on: `sources/README.md`.
- **What existed before:** the brief, the job package and the AlphaFold results. No scene, script or render had been started; "finish" is read as "make the film from these".
- **References:** none. The look is the studio "mist" look of amadeusbio.ai (as in the channelrhodopsin v2 film).

## Interpretation

- **The one idea:** a repeat pattern in a phage genome → is expressed as a set of distinct RNAs → which sit beside a reverse transcriptase and a partner protein whose relationship is unknown.
- **What was built, and why:** the brief recommends building "the repeat-array → RNA-repertoire transition first" and ending on "the unresolved partner". The film is that ART-specific core: its sections 1, 3 and 6, with the RT itself as the middle beat.
  - **Left out:** the phage exterior (section 2: the brief allots it 8–10 s and calls it less distinctive), and the comparison systems 6AR1, 9LM3 and 8QBM (sections 4, 5, 7). They are not ART structures, and the brief itself wants them as separate, clearly labelled companions. They are the natural next films.
- **Subject and structures:**

  | Source | What it is | Used for | Evidence level |
  | --- | --- | --- | --- |
  | GenBank MW218148.1:9421–10900 | Phage SA1 sequence: the array tract and the start of the RT gene | The DNA, base pair by base pair; the lit repeats | sequence: experimental. Repeat boundaries: our comparison. Helix: ideal B-DNA from 1BNA templates. Path: illustrative |
  | 1BNA (PDB) | B-DNA dodecamer | Base-pair templates and the helix step | experimental (template) |
  | AF3 jobs 04–07, model 0 | RNAs of the four motif-to-motif windows W1–W4 | The RNA repertoire | prediction, low confidence (mean pLDDT 40–50); RNA ends are window choices |
  | AF3 job 01, model 0 | RT QPI16926.1 (501 aa) | The RT and its YADD motif (366–369) | prediction, pTM 0.80 |
  | AF3 job 02, model 0 | Partner QPI16927.1 (265 aa) | The partner | prediction, low confidence (pTM 0.21, mean pLDDT 33) |
  | AF3 jobs 03, 08–19 | RT–partner, RT–RNA, partner–RNA and three-part complexes | Not shown: ipTM 0.07–0.24, no confident interface | (rejected) |

- **Claims verified numerically** (`art_locus.py`, `tests/test_art_rna.py`):
  - the 14-nt seed `ATATGAATACGTAT` occurs five times in the tract (≤ 1 mismatch), on the + strand only;
  - around it, a 49-nt repeat; copies 3–5 are 98–100 % identical, copies 1–2 degenerate (63 %, 57 %);
  - spacers of 122–163 nt, within the reported 120–220 nt; repeat length within the reported 15–49 nt (cas genes were not searched for in SA1: the caption quotes the general report that ART loci lack them);
  - the RT and partner CDS start with ATG; YADD sits at RT residues 366–369 with pLDDT 92;
  - AF3 confidences per model and for all 23 complex jobs.
- **Beats** (editorial timing, 24 fps, 31 s):

  | Screen time | Beat | Evidence level |
  | --- | --- | --- |
  | 0–7 s | Close on the DNA, repeat 1 lights; pull back as repeats 2–5 recur | sequence; DNA shape illustrative |
  | 7–11 s | The whole array; a flat locus map: array, RT gene, partner gene | sequence and GenBank annotation |
  | 11–17.5 s | Four RNAs resolve beneath their units, guide lines to their origin | AF3 predictions, low confidence |
  | 18–24.5 s | Travel to the RT, cutaway to the YADD motif | AF3 prediction |
  | 25–31 s | The partner resolves; dashed "?" links between RNA, RT and partner | hypotheses; no complex shown |

- **Look:** the website's "mist" look: pale blue-grey backdrop, slate DNA, amber for the repeats (the one warm accent), teal RNA, navy RT, coral partner. Low-confidence predictions are translucent, as in the website's AlphaFold stills. The brief's palette (amber DNA, teal RNA, violet RT, coral partner, ivory annotations) is adapted to the house look: the repeats, not the whole DNA, carry the amber.

## Deliverables

- **Format:** 31 s, 1920×1080, 24 fps, narrative.
- **Versions:** labelled and clean.
- **Files:** MP4 (H.264) + WebM (VP9) + four posters, in `delivery/art-rna/`, with the AlphaFold Server terms file.

## Constraints, assumptions and open questions

- **AlphaFold Server Output Terms** apply to the RNAs, RT and partner. Output is for non-commercial use, with an exception for open-source release. The owner applied that exception to the AlphaFold still on amadeusbio.ai; the same reasoning is assumed here, and the labelled film carries a notice. The owner should confirm before any public or commercial use.
- **Positions are editorial.** The RNAs hang below their units and the RT and partner sit beyond unit 4 by choice. Nothing about cellular location or binding is implied, and the molecules never touch (clearances in `record.md`).
- **RNA ends:** the AF3 inputs are motif-to-motif genomic windows, not mapped transcripts.
- **Not verified against the preprint itself:** its PDF was not retrievable. Captions use only facts from the public summaries listed in `sources/README.md`.
