# Channelrhodopsin: Nobel Prize in Physiology or Medicine 2026

## Request (2026-10-06)

> "refer to @Nobel_Med_2026.md and generate scientific illustrative animation for the molecular interaction. Make it pretty, you can refer to existing examples and workflow for aesthetic reference on how should professional animation looks like"

- **Source document:** `sources/Nobel_Med_2026.md`. It was generated with ChatGPT (web) and shared at <https://chatgpt.com/share/6ac61833-1620-83e8-a4ab-a519971d1b0f>; provenance is in `sources/README.md`. The prize went to Deisseroth, Hegemann and Nagel for light-gated ion channels and optogenetics. The document proposes six directions and recommends building the retinal-pocket shot of direction 1 first.
- **References:** the studio molecular look (atoms as spheres, pale backdrop, shallow depth of field) from earlier in-house work. No reference media are distributed.

## Interpretation

- **The one idea:** a photon isomerises retinal → the protein's interaction network rearranges → a cation pathway connects.
- **Shot built first:** direction 1, "The twist that opens a pathway". It is extended to about 21 s so it opens on the membrane context and ends on ion passage.
- **Subject and structures:**

  | PDB | What it is | Used for | Evidence level |
  | --- | --- | --- | --- |
  | 9GO1 | C1C2 (ChR1/ChR2 chimera), dark state, 2.59 Å | Starting coordinates; the dimer comes from the deposited assembly | experimental |
  | 9GO2 | C1C2 light-activated, alt B (30 % occupancy), early M390-like state | End coordinates of the morph | experimental (endpoint) |
  | — | The path between them | Constrained morph | illustrative |
  | — | Conducting state, ions | Pathway dilation and Na⁺ transits | illustrative |

- **Claims verified numerically:**
  - the C12-C13=C14-C15 dihedral (all-trans → 13-cis);
  - the Lys296 Schiff-base bond;
  - Lys132–Glu129 (9.0 → 2.66 Å);
  - the Trp262 clash if the twist runs alone;
  - the 9GO2 pathway's free radius (interrupted).
- **Look:**
  - atoms as spheres, soft studio light on a pale backdrop, shallow depth of field;
  - one warm accent (amber retinal) against a muted teal protein;
  - evidence level stated on screen.

## Deliverables

- **Format:** about 21 s, 1920×1080, 24 fps, narrative (not a loop).
- **Versions:** labelled and clean.
- **Files:** MP4 + WebM + posters, in `delivery/channelrhodopsin/`.

Result and checks: `record.md`.
