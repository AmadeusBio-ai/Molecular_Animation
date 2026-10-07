# __TITLE__: production record

<!-- Write as you go and finish it at delivery (docs/workflow.md, step 9). Keep it short and factual; say how
each thing was checked. Model: examples/channelrhodopsin/record.md. -->

## What was built

| File | Role |
| --- | --- |
| `__SCRIPT__.py` | Shot script: rebuilds scene `__SCENE__` into `__NAME__.blend` (+ the label scene) |

## Structural basis (checked numerically at build)

- The structures used, their states, alt-locs and assemblies, and the numbers measured.

## Motion and evidence levels

| Screen time | What moves | Evidence level (also the on-screen tag) |
| --- | --- | --- |
| | | |

## Reproduce

```
python pipeline.py build __NAME__
python pipeline.py render __NAME__ --take take-01
python pipeline.py render __NAME__ --overlay --take labels-01
python pipeline.py deliver __NAME__
```

## Checks

- **Build:** the `RESULT` numbers, and idempotency (no `.001` duplicates).
- **Stills and preview:** the frames viewed, and the contact sheet.
- **Motion:** `pipeline.py motion` (steps above 2× their local median); the seam for loops.
- **Delivery:** codec, frames, duration and size per file (from `encode.py`).
- **Review method:** frames, statistics, decoded deliverables. Say whether the film was watched as playback.

## Known differences and limits

- 
