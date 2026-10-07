"""Start the Blender Lab MCP server (blmcp) with a Windows stdin fix.

blmcp's headless *_for_cli tools run `blender --background` through subprocess.run
without redirecting stdin, so the child inherits the server's MCP stdio pipe. On
Windows the server's pending read holds that synchronous pipe's lock, the child
blocks during startup, and every *_for_cli call times out after 120 s.

Defaulting stdin to DEVNULL fixes it. Remove this wrapper (and point the MCP config
back at blender-mcp.exe) once upstream passes stdin itself:
https://projects.blender.org/lab/blender_mcp  (tools_helpers/blender_cli.py)
"""
import subprocess
import sys

_run = subprocess.run


def _run_without_inherited_stdin(*args, **kwargs):
    if 'input' not in kwargs:
        kwargs.setdefault('stdin', subprocess.DEVNULL)
    return _run(*args, **kwargs)


subprocess.run = _run_without_inherited_stdin

from blmcp import main  # noqa: E402  (import after the patch)

sys.exit(main())
