@AGENTS.md

# Claude Code notes

- **Brief to film.** `/new-film <brief or source document>` runs the workflow in `docs/workflow.md` (skill in `.claude/skills/new-film/`).
- **Blender MCP.** Tools appear as `mcp__blender__*`.
  - Live tools need Blender open with the MCP add-on running.
  - The `*_for_cli` tools start their own background Blender.
  - MCP servers load at session start. If the tools are missing, open Blender and start a new session (`docs/setup.md`).
- **Long renders.** Final Cycles takes run for hours. Start `python pipeline.py render ...` with Bash `run_in_background` and keep working; you are notified when it exits. Never render a sequence through MCP.
- **Looking at results.** The Read tool displays PNGs. Read look-dev stills, contact sheets (`renders/<shot>/*-sheet.png`) and frames decoded from the delivered films.
- **Windows shell.** In Git Bash, heredocs can collapse `\\` to `\`, so write multi-line Python helpers with the Write tool. Pass Windows Python forward-slash paths (`cygpath -m`), not `/c/...`.
- **Blender executable.** `$BLENDER`, otherwise the default install path (`pipeline.py doctor` shows which one is used).
