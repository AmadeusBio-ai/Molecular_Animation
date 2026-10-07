# Setup

The pipeline was built and tested on Windows 11 with an NVIDIA RTX 5060 Ti. The headless pipeline (`pipeline.py`) is plain Python plus Blender and ffmpeg, so it should also work on macOS and Linux, but it hasn't been tested there. Reports and fixes are welcome (`CONTRIBUTING.md`).

## 1. Requirements

| Tool | Version used | Needed for | Install |
| --- | --- | --- | --- |
| Blender | 5.2.2 LTS | everything | <https://www.blender.org/download/lts/>. Windows default path: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`; otherwise set `BLENDER` to the executable |
| GPU | NVIDIA with OptiX (CUDA, HIP, Metal and oneAPI also work) | Cycles renders in reasonable time | current driver |
| ffmpeg + ffprobe | recent build with `libx264` and `libvpx-vp9` | encoding and verifying deliveries | Windows: `winget install Gyan.FFmpeg`; macOS: `brew install ffmpeg`; Linux: your package manager |
| Python | 3.10 or newer | `pipeline.py`, `tools/encode.py`, tests | python.org or your package manager |
| numpy, Pillow | see `requirements.txt` | `molanim` outside Blender, contact sheets, motion statistics | `pip install -r requirements.txt` |
| Claude Code + Blender MCP | blmcp 1.0.3 | interactive, agent-driven work (section 4) | optional for headless use |

Blender bundles its own Python with numpy. Shot scripts need nothing else.

## 2. Get the repo

```
git clone https://github.com/AmadeusBio-ai/Molecular_Animation.git
cd Molecular_Animation
pip install -r requirements.txt
python pipeline.py doctor
```

`doctor` checks:
- Blender's version and the GPU devices it finds;
- ffmpeg and its encoders;
- numpy and Pillow;
- the checksums of the structures in `assets/pdb/`.

## 3. Check that it reproduces

```
python -m pytest tests                     # framework and case-study science (no Blender needed)
python pipeline.py smoke                   # builds every shot, renders one small still each (~1 min)
python pipeline.py fetch channelrhodopsin  # the delivered case-study films and posters (release v0.1.0)
python pipeline.py check channelrhodopsin  # rebuild, render frame 70 at delivery settings, compare with the poster
```

`check` should report a mean difference of about 0.000 and a max of 1 or 2 levels (denoiser noise). A different GPU or driver can add slightly more noise, but not a different picture.

To reproduce the whole film, render its take and deliver it. This takes about 2.7 h on an RTX 5060 Ti.

```
python pipeline.py render channelrhodopsin --take take-01
python pipeline.py render channelrhodopsin --overlay --take labels-01
python pipeline.py deliver channelrhodopsin --take take-01
```

`deliver` reads the label take from `shots.json` (`labels-03` in the original production), so point it at your own label take first. Encoding an existing take reproduces the delivered MP4 byte for byte. The WebM's decoded frames are identical, but its container IDs differ on every encode.

## 4. Blender MCP (interactive work with Claude Code)

The official Blender Lab MCP server lets an agent drive an open Blender: run scripts, inspect the scene, take screenshots and search the bundled API docs.

```
Claude Code ⇐ MCP/stdio ⇒ blender-mcp (blmcp 1.0.3) ⇐ TCP localhost:9876 ⇒ Blender add-on "MCP" 1.0.3
```

1. **Add-on.** Download `mcp-1.0.3.zip` from the releases of <https://projects.blender.org/lab/blender_mcp>, then install it:
   ```
   "<blender>" -c extension install-file -r user_default -e mcp-1.0.3.zip
   ```
   In Blender, turn on **Edit → Preferences → System → Network → Allow Online Access**; the add-on won't start without it. In the add-on's preferences, enable auto-start (host `localhost`, port `9876`).
2. **Server.** Install it with uv:
   ```
   uv tool install "blender-mcp @ git+https://projects.blender.org/lab/blender_mcp.git@v1.0.3#subdirectory=mcp"
   ```
3. **Register it with Claude Code.**
   - **On macOS or Linux:**
     ```
     claude mcp add-json --scope user blender '{"type":"stdio","command":"blender-mcp","env":{"BLENDER_PATH":"<blender>"}}'
     ```
   - **On Windows, use the launcher in `tools/blender_mcp_launch.py`.** blmcp's headless `*_for_cli` tools start `blender --background` without redirecting stdin. The child process then inherits the server's MCP stdio pipe, and on Windows the server's pending read holds that pipe's lock, so Blender blocks during startup and every call times out after 120 s. The launcher defaults stdin to `DEVNULL` and then starts the unmodified server, so `uv tool upgrade blender-mcp` keeps the fix.

     Copy the launcher somewhere stable, such as `~/.claude/mcp/`, and register it:
     ```
     claude mcp add-json --scope user blender "{\"type\":\"stdio\",\"command\":\"<uv tool dir>\\blender-mcp\\Scripts\\python.exe\",\"args\":[\"<home>\\.claude\\mcp\\blender_mcp_launch.py\"],\"env\":{\"BLENDER_PATH\":\"C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe\"}}"
     ```
     `uv tool dir` prints `<uv tool dir>`. Once upstream passes stdin itself, point `command` back at `blender-mcp.exe` and delete the launcher.
4. **Check.** Open Blender, start a new Claude Code session, and run `claude mcp get blender`. Then ask Claude to run `tools/mcp_smoke_test.py` through `execute_blender_code`. It builds scene `MCP_Smoke_Test` and writes `renders/mcp-smoke-test/still.png`, a red oxygen with two white hydrogens.

Caveats:
- The add-on runs any code it receives with your user permissions. It listens on localhost only, and Allow Online Access is a global Blender preference.
- Live calls block Blender's UI and time out after 300 s, so render with `pipeline.py`.
- If port 9876 is taken, change it in the add-on preferences and set `BLENDER_MCP_PORT` in the server's `env`.

## 5. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Blender not found` | Set `BLENDER` to the executable's full path. |
| `doctor` reports no Cycles GPU | Update the GPU driver. Cycles falls back to the CPU, which is very slow at 128 samples. |
| A build fails | Read `renders/<shot>/build.log`. Scripts need Blender 5.2's API (see `docs/blender-5.md`). |
| A checksum differs after `pipeline.py pdb` | RCSB has remediated the entry. Shots were checked against the recorded file, so restore that file from git. |
| `render` refuses to continue a take | The blend changed after the take started. Render into a new `take-NN`, or pass `--force` if only the build date changed. |
| The MCP tools are missing in Claude Code | Open Blender first, then start a new session; servers load at session start. |
