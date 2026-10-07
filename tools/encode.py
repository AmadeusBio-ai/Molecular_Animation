"""Encode a rendered PNG sequence to MP4 (H.264) and WebM (VP9), then verify the outputs.

    python tools/encode.py renders/<shot>/take-NN delivery/<shot>/<name> [--fps 24] [--count 120]
                         [--crf-mp4 16] [--crf-webm 24]   (raise the CRFs for lighter web files)
                         [--overlay renders/<shot>/take-NN-labels]   (RGBA frames laid on top, same numbering)

Writes <out>.mp4 and <out>.webm. Checks each output decodes, and reports its size, frame count and
duration. Fails if a frame is missing or the counts disagree. Needs ffmpeg/ffprobe on PATH.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('frames')
parser.add_argument('out')
parser.add_argument('--fps', type=int, default=24)
parser.add_argument('--frames-expected', '--count', dest='count', type=int, default=120)
parser.add_argument('--start', type=int, default=1)
parser.add_argument('--crf-mp4', type=int, default=16)
parser.add_argument('--crf-webm', type=int, default=24)
parser.add_argument('--overlay', help='folder of RGBA PNG frames (e.g. a label pass) laid over the picture')
args = parser.parse_args()

frames = Path(args.frames)
names = [frames / f'{n:04d}.png' for n in range(args.start, args.start + args.count)]
if args.overlay:
    names += [Path(args.overlay) / f'{n:04d}.png' for n in range(args.start, args.start + args.count)]
missing = [str(p) for p in names if not p.exists()]
if missing:
    sys.exit(f'missing {len(missing)} frames, first: {missing[:5]}')

out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
src = ['-framerate', str(args.fps), '-start_number', str(args.start), '-i', str(frames / '%04d.png')]
if args.overlay:
    src += ['-framerate', str(args.fps), '-start_number', str(args.start), '-i', str(Path(args.overlay) / '%04d.png'),
            '-filter_complex', '[0:v][1:v]overlay=format=auto[v]', '-map', '[v]']
src += ['-frames:v', str(args.count)]
jobs = {
    '.mp4': ['-c:v', 'libx264', '-preset', 'slow', '-crf', str(args.crf_mp4), '-pix_fmt', 'yuv420p', '-movflags', '+faststart'],
    '.webm': ['-c:v', 'libvpx-vp9', '-crf', str(args.crf_webm), '-b:v', '0', '-row-mt', '1', '-pix_fmt', 'yuv420p'],
}
report = {}
for ext, codec in jobs.items():
    target = out.with_suffix(ext)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *src, *codec, str(target)], check=True)
    probe = json.loads(subprocess.run(
        ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
         'stream=codec_name,width,height,r_frame_rate,nb_read_frames:format=duration', '-of', 'json', str(target)],
        check=True, capture_output=True, text=True).stdout)
    stream = probe['streams'][0]
    report[target.name] = {'codec': stream['codec_name'], 'size': f"{stream['width']}x{stream['height']}",
                           'fps': stream['r_frame_rate'], 'frames': int(stream['nb_read_frames']),
                           'duration_s': round(float(probe['format']['duration']), 3),
                           'bytes': target.stat().st_size}
    if int(stream['nb_read_frames']) != args.count:
        sys.exit(f'{target.name}: decoded {stream["nb_read_frames"]} frames, expected {args.count}')
print(json.dumps(report, indent=2))
