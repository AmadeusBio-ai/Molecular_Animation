# Projects

Your films live here, one folder per project. Create one with:

```
python pipeline.py new <name> --pdb <ID> [--highlight RES] [--chains A,B] [--title "..."] [--seconds 8] [--fps 24] [--loop]
```

This copies `templates/shot/` into `projects/<name>/`:

| File | Purpose |
| --- | --- |
| `<name>.py` | The shot script: a working studio shot of the structure, to be made your own |
| `shots.json` | How the shot is rendered and delivered (read by `pipeline.py`) |
| `brief.md` | What was asked, and how you interpret it |
| `record.md` | What was built and checked (fill in as you go) |
| `sources/` | Source documents as given (e.g. the brief you were handed) |

The workflow from brief to delivered film is in `docs/workflow.md`. A finished example is `examples/channelrhodopsin/`. `pipeline.py` finds every `projects/*/shots.json` automatically.

Whether to commit projects is your choice. In a fork, committing them keeps your films reproducible.
