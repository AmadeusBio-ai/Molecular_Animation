# Sources

| File | What it is | Provenance |
| --- | --- | --- |
| `CRISPR-Like.txt` | The brief: "A hidden repertoire of RNA", seven animation directions for array-associated reverse transcriptases (ART), with structural assets and a Blender approach | Handed over by the owner in `CRISPR-Like/` (dated 2026-10-07). Its links carry `utm_source=chatgpt.com`, so it was generated with ChatGPT; no share link was given. Kept unchanged (SHA-256 `93923aec…2fdde2`). |
| `af3-job-package/` | The AlphaFold Server job package for the SA1 ART locus: README, protein and RNA FASTA, the GenBank excerpt MW218148.1:9421–13020, the job manifest and its validation report | Prepared 2026-10-07 by the same AI-assisted process (its README says so). Copied unchanged from `CRISPR-Like/ART_AlphaFold_Server_jobs/art_af3_jobs/`; the 29 job JSON files are not copied. |
| `../af3/` | AlphaFold Server output for all 29 jobs: model CIFs (5 per job), summary confidences, job requests and `terms_of_use.md` | The owner ran the jobs on AlphaFold Server and saved `CRISPR-Like/folds_2026_10_08_04_51.zip` (SHA-256 `eb42ee4f…dfd055a`). Extracted unchanged; MSAs, templates and full PAE files were left in the zip. **AlphaFold Server Output Terms of Use apply** (`../af3/terms_of_use.md`). |

## Facts checked against public sources (accessed 2026-10-17)

The brief and the job package could not retrieve the preprint PDF. The film's captions use only these:

- Anthropic, "Claude discovers a novel enzyme system" (<https://www.anthropic.com/news/claude-discovers-novel-enzyme-system>): ART is found mainly in bacteriophages; "a long array of evenly spaced DNA repeat sequences"; "The repeat layout resembles a CRISPR array"; "an additional accessory protein of unknown function"; "the ART array is also expressed as a set of distinct short RNAs"; "we don't yet know its function". The preprint is on bioRxiv (10.64898/2026.10.05.755809).
- Drug Discovery News, "Claude spots a mystery enzyme scientists overlooked" (<https://www.drugdiscoverynews.com/claude-spots-a-mystery-enzyme-scientists-overlooked-17549>), reporting the preprint: arrays of 3–21 copies of a 15–49-nt repeat separated by 120–220-nt spacers, in loci that lack cas genes; reanalysed RNA-seq of Staphylococcus phage SA1 infecting *S. lentus*, where array-derived RNAs were up to 8 % of phage RNA 15 min after infection; "Whether the RT is active, whether it interacts with its partner, and what the system does for the phage all remain open questions".
- `forresthu/artmine` README (pinned commit in the job package): the partner is assigned as "the gene directly 3′ of the RT on the RT strand".

Everything else on screen is measured in this project (`../art_locus.py`, `../record.md`).
