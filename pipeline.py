"""Command-line front end for the film pipeline.

Projects live in examples/<name>/ and projects/<name>/; each has a shots.json describing its shots (script,
blend, fps, frame count, delivered take, encode settings, posters). Shot names are unique across projects.

    python pipeline.py doctor                         check Blender, GPU, ffmpeg, Python packages and structures
    python pipeline.py list                           every shot, and which of blend / takes / delivery exist
    python pipeline.py new <name> --pdb 1EMA [--highlight CRO] [--chains A] [--title T] [--seconds 8] [--fps 24] [--loop]
                                                      scaffold projects/<name>/ from templates/shot
    python pipeline.py pdb 9GO1 9GO2                  download mmCIF files from RCSB into assets/pdb (+ checksums)
    python pipeline.py build <shot>|all               run the shot script headless, print and save its RESULT
    python pipeline.py still <shot> <frame> [--percent 50] [--samples N] [--out PATH] [--overlay]
    python pipeline.py preview <shot> [--step 4] [--percent 25] [--samples 16]   new preview-NN + contact sheet
    python pipeline.py render <shot> --take take-NN [--frames A-B] [--overlay] [--percent P] [--samples N]
    python pipeline.py sheet <frames dir> [--cols 8] [--width 320] [--max 48]
    python pipeline.py motion <frames dir> [--loop COUNT]
    python pipeline.py deliver <shot> [--take take-NN] [--dest DIR]
    python pipeline.py fetch <shot>                   download a shot's published delivery from the GitHub release
    python pipeline.py smoke [<shot> ...]             build each shot and render a small still (quick check)
    python pipeline.py check [<shot> ...]             rebuild, render the first poster frame at delivery settings and
                                                      compare it with the delivered poster (needs `fetch` first)

Blender is found from $BLENDER, then the default install location, then PATH. Every Blender call uses
--factory-startup, so user add-ons and preferences cannot change a build or a render (tools/render.py picks the
GPU itself).
"""
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BLENDER_VERSION = '5.2'
REPO = 'AmadeusBio-ai/Molecular_Animation'
PDB_DIR = ROOT / 'assets' / 'pdb'
SUMS = PDB_DIR / 'SHA256SUMS'
TEMPLATE = ROOT / 'templates' / 'shot'


# ----------------------------------------------------------------------------- shots

def discover():
    """{shot: spec} from examples/*/shots.json and projects/*/shots.json, with paths made absolute."""
    shots = {}
    for manifest in sorted(ROOT.glob('examples/*/shots.json')) + sorted(ROOT.glob('projects/*/shots.json')):
        folder = manifest.parent
        for name, s in json.loads(manifest.read_text(encoding='utf-8'))['shots'].items():
            if name in shots:
                sys.exit(f'shot {name!r} is defined twice ({rel(manifest)})')
            s = dict(s, folder=folder, manifest=manifest)
            for key in ('script', 'blend', 'brief', 'record'):
                if key in s:
                    s[key] = folder / s[key]
            if 'overlay' in s:
                s['overlay'] = dict(s['overlay'], blend=folder / s['overlay']['blend'])
            s['delivery'] = ROOT / s.get('delivery', f'delivery/{name}')
            shots[name] = s
    return shots


SHOTS = discover()


def shot(name):
    if name not in SHOTS:
        sys.exit(f'unknown shot {name!r}; known: {", ".join(SHOTS) or "(none)"}')
    return SHOTS[name]


# ----------------------------------------------------------------------------- helpers

def blender_path():
    env = os.environ.get('BLENDER')
    if env:
        return env
    candidates = {
        'Windows': [rf'C:\Program Files\Blender Foundation\Blender {BLENDER_VERSION}\blender.exe'],
        'Darwin': ['/Applications/Blender.app/Contents/MacOS/Blender'],
    }.get(platform.system(), [])
    for c in candidates:
        if Path(c).exists():
            return c
    found = shutil.which('blender')
    if found:
        return found
    sys.exit('Blender not found: set BLENDER to the blender executable (see docs/setup.md)')


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(ROOT)).replace('\\', '/')
    except ValueError:
        return str(p)


def run_blender(args, log=None, env=None):
    """Run Blender headless; save the output to a log file if given. Returns (returncode, output text)."""
    cmd = [blender_path(), '-b', '--factory-startup', '--python-exit-code', '1', *args]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace',
                          env={**os.environ, **(env or {})})
    out = proc.stdout + proc.stderr
    if log:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        Path(log).write_text(out, encoding='utf-8')
    return proc.returncode, out


def render_py(blend, extra, log):
    code, out = run_blender([str(blend), '--python', str(ROOT / 'tools' / 'render.py'), '--', *extra], log)
    device = next((line for line in out.splitlines() if line.startswith('RENDER_DEVICE')), 'RENDER_DEVICE ?')
    if code:
        print(out[-3000:])
        sys.exit(f'render failed ({code}); log: {rel(log)}')
    return device


def frames_in(folder):
    return sorted(p for p in Path(folder).glob('*.png') if re.fullmatch(r'\d{4}', p.stem))


def next_dir(parent, stem):
    n = 1
    while (parent / f'{stem}-{n:02d}').exists():
        n += 1
    return parent / f'{stem}-{n:02d}'


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read_sums():
    if not SUMS.exists():
        return {}
    return {line.split()[1]: line.split()[0] for line in SUMS.read_text().splitlines() if line.strip()}


def fetch_pdb(ids):
    PDB_DIR.mkdir(parents=True, exist_ok=True)
    sums = read_sums()
    for pdb_id in ids:
        name = f'{pdb_id.upper()}.cif'
        path = PDB_DIR / name
        if not path.exists():
            url = f'https://files.rcsb.org/download/{name}'
            print('download', url)
            with urllib.request.urlopen(url, timeout=60) as r:
                path.write_bytes(r.read())
        digest = sha256(path)
        if name in sums and sums[name] != digest:
            print(f'  {name}: checksum differs from SHA256SUMS (RCSB may have remediated the entry); '
                  'shots were checked against the recorded file')
        else:
            sums[name] = digest
            print(f'  {name}: {digest[:16]}...')
    SUMS.write_text(''.join(f'{d}  {n}\n' for n, d in sorted(sums.items())), newline='\n')


# ----------------------------------------------------------------------------- commands

def cmd_doctor(a):
    ok = True

    def report(label, good, detail=''):
        nonlocal ok
        ok &= bool(good)
        print(f"  [{'ok' if good else '!!'}] {label}{': ' + detail if detail else ''}")

    print('Python')
    report('python >= 3.10', sys.version_info >= (3, 10), sys.version.split()[0])
    for mod in ('numpy', 'PIL'):
        try:
            m = __import__(mod)
            report(f'{mod}', True, getattr(m, '__version__', ''))
        except ImportError:
            report(f'{mod}', False, 'pip install -r requirements.txt')

    print('Blender')
    exe = blender_path()
    probe = ("import bpy, json; p = bpy.context.preferences.addons['cycles'].preferences; found = {}\n"
             "for kind in ('OPTIX', 'CUDA', 'HIP', 'METAL', 'ONEAPI'):\n"
             "    try:\n"
             "        p.compute_device_type = kind; p.get_devices()\n"
             "        found[kind] = [d.name for d in p.devices if d.type == kind]\n"
             "    except TypeError:\n"
             "        pass\n"
             "print('DOCTOR', json.dumps({'version': bpy.app.version_string, 'devices': found}))")
    code, out = run_blender(['--python-expr', probe])
    line = next((l for l in out.splitlines() if l.startswith('DOCTOR ')), None)
    if code or not line:
        report(exe, False, 'could not run Blender headless')
    else:
        info = json.loads(line[7:])
        report(exe, info['version'].startswith(BLENDER_VERSION), f"{info['version']} (want {BLENDER_VERSION}.x)")
        gpus = {k: v for k, v in info['devices'].items() if v}
        report('Cycles GPU', bool(gpus), json.dumps(gpus) if gpus else 'none found; Cycles will be very slow on CPU')

    print('ffmpeg')
    for tool in ('ffmpeg', 'ffprobe'):
        report(tool, shutil.which(tool), shutil.which(tool) or 'not on PATH')
    if shutil.which('ffmpeg'):
        enc = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], capture_output=True, text=True).stdout
        for codec in ('libx264', 'libvpx-vp9'):
            report(f'encoder {codec}', codec in enc)

    print('Structures')
    for name, digest in sorted(read_sums().items()):
        path = PDB_DIR / name
        report(f'assets/pdb/{name}', path.exists() and sha256(path) == digest,
               'checksum ok' if path.exists() else 'missing: python pipeline.py pdb ' + Path(name).stem)

    print('Optional')
    print(f"  [{'ok' if shutil.which('gh') else '--'}] gh (GitHub CLI)")
    print('  [--] Blender MCP: open Blender with the MCP add-on running, then `claude mcp get blender` (docs/setup.md)')
    print('\nall required checks passed' if ok else '\nsome checks failed (see docs/setup.md)')
    return 0 if ok else 1


def cmd_list(a):
    for name, s in SHOTS.items():
        base = ROOT / 'renders' / name
        takes = sorted(p.name for p in base.glob('take-*') if p.is_dir()) if base.exists() else []
        blend = '+' if s['blend'].exists() else '-'
        outputs = s.get('outputs', [])
        delivered = all((s['delivery'] / f"{o['name']}.mp4").exists() for o in outputs) if outputs else False
        print(f"{name:24} {rel(s['folder']):34} blend {blend}  takes {','.join(takes) or '-':18} "
              f"delivered {'+' if delivered else '-'}  {s.get('title', '')}")


def cmd_new(a):
    name = a.name.lower()
    if not re.fullmatch(r'[a-z][a-z0-9-]*', name):
        sys.exit('name: lower-case letters, digits and dashes, starting with a letter (e.g. gfp-chromophore)')
    if name in SHOTS:
        sys.exit(f'shot {name!r} already exists in {rel(SHOTS[name]["folder"])}')
    dest = ROOT / 'projects' / name
    if dest.exists():
        sys.exit(f'{rel(dest)} already exists')
    fetch_pdb([a.pdb])
    snake = name.replace('-', '_')
    words = name.split('-')
    frames = round(a.seconds * a.fps)
    values = {
        '__NAME__': name, '__SCRIPT__': snake, '__SCENE__': ''.join(w.capitalize() for w in words),
        '__PREFIX__': ''.join(w[0] for w in words).upper()[:4] + '_', '__PDB__': a.pdb.upper(),
        '__TITLE__': a.title or f'{a.pdb.upper()}', '__FPS__': str(a.fps), '__FRAMES__': str(frames),
        '__LOOP__': 'True' if a.loop else 'False', '__RENDER__': f'1-{frames + 1}' if a.loop else f'1-{frames}',
        '__LOOPJSON__': 'true' if a.loop else 'false',
        '__CHAINS__': repr(a.chains.split(',')) if a.chains else 'None',
        '__HIGHLIGHT__': repr(a.highlight.split(',')) if a.highlight else 'None',
        '__DATE__': time.strftime('%Y-%m-%d'),
    }
    dest.mkdir(parents=True)
    for src in TEMPLATE.iterdir():
        target = dest / src.name.replace('shot.py', f'{snake}.py')
        text = src.read_text(encoding='utf-8')
        for k, v in values.items():
            text = text.replace(k, v)
        target.write_text(text, encoding='utf-8')
    (dest / 'sources').mkdir()
    print(f'created {rel(dest)}/ ({", ".join(sorted(p.name for p in dest.iterdir()))})')
    print(f'next:  python pipeline.py build {name}   then   python pipeline.py still {name} <frame> --percent 50')


def cmd_pdb(a):
    fetch_pdb(a.ids)


def build(name):
    s = shot(name)
    log = ROOT / 'renders' / name / 'build.log'
    expr = ("import json, os, runpy\n"
            "r = runpy.run_path(os.environ['PIPELINE_SCRIPT'], run_name='__main__').get('RESULT')\n"
            "print('PIPELINE_RESULT ' + json.dumps(r, default=str))")
    t0 = time.time()
    code, out = run_blender(['--python-expr', expr], log, env={'PIPELINE_SCRIPT': str(s['script'])})
    line = next((l for l in out.splitlines() if l.startswith('PIPELINE_RESULT ')), None)
    if code or line is None:
        print(out[-4000:])
        sys.exit(f'build of {name} failed; log: {rel(log)}')
    result = json.loads(line[len('PIPELINE_RESULT '):])
    (log.parent / 'build-result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result, time.time() - t0


def cmd_build(a):
    names = list(SHOTS) if a.shot == ['all'] else a.shot
    done = set()
    for name in names:
        script = shot(name)['script']
        if script in done:          # one script may write several blends
            continue
        done.add(script)
        result, seconds = build(name)
        text = json.dumps(result, indent=2)
        print(f'== {name}: {rel(script)} built in {seconds:.0f} s; RESULT saved to renders/{name}/build-result.json')
        print(text if len(text) < 4000 else text[:4000] + '\n  ... (truncated)')


def cmd_still(a):
    s = shot(a.shot)
    blend = s['overlay']['blend'] if a.overlay else s['blend']
    out = Path(a.out) if a.out else ROOT / 'renders' / a.shot / 'dev' / f"{'labels-' if a.overlay else ''}f{a.frame:04d}.png"
    extra = ['--still', str(a.frame), '--out', str(out)]
    extra += ['--percent', str(a.percent)] if a.percent else []
    extra += ['--samples', str(a.samples)] if a.samples else []
    t0 = time.time()
    device = render_py(blend, extra, ROOT / 'renders' / a.shot / 'dev' / 'still.log')
    print(f'{rel(out)}  ({time.time() - t0:.0f} s, {device})')


def cmd_render(a):
    s = shot(a.shot)
    blend = s['overlay']['blend'] if a.overlay else s['blend']
    if not re.fullmatch(r'(take|labels|preview)-\d{2}', a.take):
        sys.exit('--take must look like take-NN (or labels-NN for the overlay pass)')
    out = ROOT / 'renders' / a.shot / a.take
    existing = frames_in(out) if out.exists() else []
    if existing and blend.stat().st_mtime > min(p.stat().st_mtime for p in existing) and not a.force:
        sys.exit(f'{rel(blend)} changed after {a.take} started. Start a new take (never mix takes), '
                 'or pass --force if only the build date changed.')
    extra = ['--out', str(out), '--frames', a.frames or s['render']]
    extra += s.get('render_args', []) if not a.overlay and not a.samples else []
    extra += ['--percent', str(a.percent)] if a.percent else []
    extra += ['--samples', str(a.samples)] if a.samples else []
    extra += ['--step', str(a.step)] if a.step else []
    t0 = time.time()
    device = render_py(blend, extra, out.parent / f'{a.take}.log')
    print(f'{rel(out)}: {len(frames_in(out))} frames  ({(time.time() - t0) / 60:.1f} min, {device})')


def cmd_preview(a):
    s = shot(a.shot)
    out = next_dir(ROOT / 'renders' / a.shot, 'preview')
    extra = ['--out', str(out), '--frames', s['render'], '--step', str(a.step), '--percent', str(a.percent),
             '--samples', str(a.samples)]
    t0 = time.time()
    device = render_py(s['blend'], extra, out.parent / f'{out.name}.log')
    print(f'{rel(out)}: {len(frames_in(out))} frames ({(time.time() - t0) / 60:.1f} min, {device})')
    contact_sheet(out, cols=8, width=320, limit=64)


def contact_sheet(folder, cols, width, limit):
    from PIL import Image, ImageDraw
    frames = frames_in(folder)
    if not frames:
        sys.exit(f'no NNNN.png frames in {folder}')
    pick = frames[::max(1, -(-len(frames) // limit))]
    first = Image.open(pick[0])
    height = round(width * first.height / first.width)
    rows = -(-len(pick) // cols)
    sheet = Image.new('RGB', (cols * width, rows * (height + 18)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    for k, p in enumerate(pick):
        im = Image.open(p).convert('RGBA')
        bg = Image.new('RGBA', im.size, (128, 128, 128, 255))     # overlay passes show on mid grey
        im = Image.alpha_composite(bg, im).convert('RGB').resize((width, height), Image.LANCZOS)
        x, y = (k % cols) * width, (k // cols) * (height + 18)
        sheet.paste(im, (x, y + 18))
        draw.text((x + 4, y + 3), p.stem, fill=(220, 220, 220))
    target = Path(folder).parent / f'{Path(folder).name}-sheet.png'
    sheet.save(target)
    print(f'contact sheet: {rel(target)} ({len(pick)} of {len(frames)} frames)')


def cmd_sheet(a):
    contact_sheet(Path(a.folder), a.cols, a.width, a.max)


def cmd_motion(a):
    """Mean |difference| between consecutive frames (0-255, at 480 px wide): finds jumps, pauses and seams."""
    import numpy as np
    from PIL import Image
    frames = frames_in(a.folder)
    if len(frames) < 3:
        sys.exit('need at least 3 frames')

    def load(p):
        im = Image.open(p).convert('RGB')
        return np.asarray(im.resize((480, round(480 * im.height / im.width)), Image.BILINEAR), np.float32)

    prev, steps = load(frames[0]), []
    for p in frames[1:]:
        cur = load(p)
        steps.append(float(np.abs(cur - prev).mean()))
        prev = cur
    steps = np.array(steps)
    print(f'{len(frames)} frames; step median {np.median(steps):.2f}, p95 {np.percentile(steps, 95):.2f}, '
          f'max {steps.max():.2f} at {frames[int(steps.argmax()) + 1].stem}')
    flagged = []
    for k in range(len(steps)):
        local = np.median(steps[max(0, k - 4):k + 5])
        if steps[k] > 2 * max(local, 0.05):
            flagged.append(f'{frames[k].stem}->{frames[k + 1].stem}: {steps[k]:.2f} (local median {local:.2f})')
    print('steps above 2x their local median:' if flagged else 'no step above 2x its local median')
    for f in flagged[:40]:
        print('  ' + f)
    if a.loop:
        first, last = load(frames[0]), load(frames[a.loop - 1])
        seam = float(np.abs(first - last).mean())
        print(f'loop seam: frame {a.loop:04d} -> 0001 step {seam:.2f} (typical {np.median(steps):.2f})')
        after = Path(a.folder) / f'{a.loop + 1:04d}.png'
        if after.exists():
            same = np.abs(load(after) - first)
            print(f'seam check: frame {a.loop + 1:04d} vs 0001 mean {same.mean():.3f}, max {same.max():.0f}')


def cmd_deliver(a):
    s = shot(a.shot)
    take = ROOT / 'renders' / a.shot / (a.take or s['take'])
    dest = Path(a.dest) if a.dest else s['delivery']
    dest.mkdir(parents=True, exist_ok=True)
    for o in s['outputs']:
        cmd = [sys.executable, str(ROOT / 'tools' / 'encode.py'), str(take), str(dest / o['name']),
               '--fps', str(s['fps']), '--count', str(s['count']),
               '--crf-mp4', str(s['crf'][0]), '--crf-webm', str(s['crf'][1])]
        if o.get('overlay'):
            cmd += ['--overlay', str(ROOT / 'renders' / a.shot / s['overlay']['take'])]
        print('encode', o['name'])
        subprocess.run(cmd, check=True)
    for poster, frame in s.get('posters', {}).items():
        shutil.copyfile(take / f'{frame:04d}.png', dest / poster)
        print(f'poster {poster} = {rel(take)}/{frame:04d}.png')


def cmd_fetch(a):
    s = shot(a.shot)
    info = s.get('release')
    if not info:
        sys.exit(f'{a.shot} has no published delivery ("release" in {rel(s["manifest"])})')
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / info['asset']
        url = f"https://github.com/{REPO}/releases/download/{info['tag']}/{info['asset']}"
        print('download', url)
        urllib.request.urlretrieve(url, target)
        with zipfile.ZipFile(target) as z:
            for member in z.namelist():         # members are repo-relative paths; refuse anything else
                if member.startswith(('/', '\\')) or '..' in Path(member).parts:
                    sys.exit(f'unsafe path in {info["asset"]}: {member}')
            z.extractall(ROOT)
            print(f"{info['asset']}: {len(z.namelist())} files restored")


def cmd_smoke(a):
    """Build every shot from its script and render one small still each."""
    names = a.shot or list(SHOTS)
    out_dir = ROOT / 'renders' / '_smoke'
    out_dir.mkdir(parents=True, exist_ok=True)
    built, rows = set(), []
    for name in names:
        s = shot(name)
        t0 = time.time()
        if s['script'] not in built:
            build(name)
            built.add(s['script'])
        tb = time.time() - t0
        frame = next(iter(s['posters'].values())) if s.get('posters') else max(1, s['count'] // 2)
        out = out_dir / f'{name}.png'
        t1 = time.time()
        render_py(s['blend'], ['--still', str(frame), '--out', str(out), '--percent', str(a.percent),
                               '--samples', str(a.samples)], out_dir / f'{name}.log')
        rows.append((name, out.exists()))
        print(f'{name:24} build {tb:5.0f} s   still f{frame} {time.time() - t1:5.0f} s   {rel(out)}')
    failed = [n for n, ok in rows if not ok]
    print('smoke test passed' if not failed else f'missing stills: {failed}')
    return 1 if failed else 0


def cmd_check(a):
    """Rebuild each shot, render its first poster frame at delivery settings and compare it with the delivered
    poster: the strongest test that the scripts still make the delivered picture."""
    import numpy as np
    from PIL import Image
    names = a.shot or [n for n, s in SHOTS.items() if s.get('posters')]
    out_dir = ROOT / 'renders' / '_check'
    built, failed = set(), []
    for name in names:
        s = shot(name)
        poster, frame = next(iter(s['posters'].items()))
        ref = s['delivery'] / poster
        if not ref.exists():
            sys.exit(f'{rel(ref)} missing: python pipeline.py fetch {name}')
        if not a.no_build and s['script'] not in built:
            build(name)
            built.add(s['script'])
        out = out_dir / f'{name}-f{frame:04d}.png'
        t0 = time.time()
        render_py(s['blend'], ['--still', str(frame), '--out', str(out), *s.get('render_args', [])],
                  out_dir / f'{name}.log')
        got = np.asarray(Image.open(out).convert('RGB'), np.float32)
        want = np.asarray(Image.open(ref).convert('RGB'), np.float32)
        if got.shape != want.shape:
            failed.append(name)
            print(f'{name:24} size {got.shape[1]}x{got.shape[0]} != delivered {want.shape[1]}x{want.shape[0]}')
            continue
        d = np.abs(got - want)
        ok = d.mean() <= a.tolerance
        failed += [] if ok else [name]
        print(f"{name:24} f{frame:<4} mean {d.mean():.3f}  p99.9 {np.percentile(d, 99.9):5.1f}  max {d.max():5.0f}  "
              f"{time.time() - t0:5.0f} s  {'ok' if ok else 'DIFFERS'}")
    print('all match the delivered posters' if not failed else f'differ: {failed}')
    return 1 if failed else 0


# ----------------------------------------------------------------------------- CLI

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('doctor')
    sub.add_parser('list')
    q = sub.add_parser('new')
    q.add_argument('name')
    q.add_argument('--pdb', required=True, help='PDB ID of the main structure')
    q.add_argument('--highlight', help='comma-separated residues to feature: names (RET), numbers (296) or chain:number (A:296); '
                                       'default: the largest ligand')
    q.add_argument('--chains', help='comma-separated chains to include (default: all)')
    q.add_argument('--title')
    q.add_argument('--seconds', type=float, default=8.0)
    q.add_argument('--fps', type=int, default=24)
    q.add_argument('--loop', action='store_true', help='seamless orbit loop instead of a narrative dive')
    q = sub.add_parser('pdb')
    q.add_argument('ids', nargs='+')
    q = sub.add_parser('build')
    q.add_argument('shot', nargs='+')
    q = sub.add_parser('still')
    q.add_argument('shot')
    q.add_argument('frame', type=int)
    q.add_argument('--percent', type=int)
    q.add_argument('--samples', type=int)
    q.add_argument('--out')
    q.add_argument('--overlay', action='store_true', help='render the overlay (label) pass instead')
    q = sub.add_parser('render')
    q.add_argument('shot')
    q.add_argument('--take', required=True)
    q.add_argument('--frames')
    q.add_argument('--step', type=int)
    q.add_argument('--percent', type=int)
    q.add_argument('--samples', type=int)
    q.add_argument('--overlay', action='store_true', help='render the overlay (label) pass instead')
    q.add_argument('--force', action='store_true')
    q = sub.add_parser('preview')
    q.add_argument('shot')
    q.add_argument('--step', type=int, default=4)
    q.add_argument('--percent', type=int, default=25)
    q.add_argument('--samples', type=int, default=16)
    q = sub.add_parser('sheet')
    q.add_argument('folder')
    q.add_argument('--cols', type=int, default=8)
    q.add_argument('--width', type=int, default=320)
    q.add_argument('--max', type=int, default=48)
    q = sub.add_parser('motion')
    q.add_argument('folder')
    q.add_argument('--loop', type=int, help='loop length in frames: also report the seam')
    q = sub.add_parser('deliver')
    q.add_argument('shot')
    q.add_argument('--take')
    q.add_argument('--dest')
    q = sub.add_parser('fetch')
    q.add_argument('shot')
    q = sub.add_parser('smoke')
    q.add_argument('shot', nargs='*')
    q.add_argument('--percent', type=int, default=25)
    q.add_argument('--samples', type=int, default=16)
    q = sub.add_parser('check')
    q.add_argument('shot', nargs='*')
    q.add_argument('--no-build', action='store_true', help='use the existing .blend files')
    q.add_argument('--tolerance', type=float, default=1.0, help='largest mean |difference| (0-255) that passes')
    a = p.parse_args()
    sys.exit(globals()['cmd_' + a.cmd](a) or 0)


if __name__ == '__main__':
    main()
