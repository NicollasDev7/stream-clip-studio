"""Portable technical renderer. Requires FFmpeg/ffprobe; never publishes."""
import argparse
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path


def rect(value, width, height):
    if len(value) != 4 or any(type(n) is not int for n in value):
        raise ValueError('Crop must contain four integer pixels: x,y,w,h')
    x, y, w, h = value
    if min(x, y) < 0 or min(w, h) < 2 or x + w > width or y + h > height:
        raise ValueError('Crop outside source geometry')
    return f'crop={w}:{h}:{x}:{y}'


def probe(exe, file):
    return json.loads(subprocess.check_output(
        [exe, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(file)], text=True))


def render(job):
    source = Path(job['source']).resolve(strict=True)
    target = Path(job['output']).resolve()
    if target.suffix.lower() != '.mp4' or target.exists():
        raise ValueError('Output must be a new .mp4 file; existing files are preserved')
    start, duration = float(job.get('start', 0)), float(job['duration'])
    if not all(map(math.isfinite, (start, duration))) or start < 0 or not 0 < duration <= 90:
        raise ValueError('Invalid start or duration (maximum 90 seconds)')
    ffmpeg, ffprobe = str(job.get('ffmpeg', 'ffmpeg')), str(job.get('ffprobe', 'ffprobe'))
    original = probe(ffprobe, source)
    video = next(s for s in original['streams'] if s['codec_type'] == 'video')
    if start + duration > float(original['format']['duration']) + .05:
        raise ValueError('Requested interval exceeds source')
    if not any(s['codec_type'] == 'audio' for s in original['streams']):
        raise ValueError('Source has no audio')
    width, height = video['width'], video['height']
    game = rect(job['game'], width, height)
    camera = job.get('camera')
    if camera:
        cam = rect(camera, width, height)
        graph = (f'[0:v]fps=30,split=2[c][g];[c]{cam},'
                 'scale=720:560:force_original_aspect_ratio=increase,crop=720:560,setsar=1[cam];'
                 f'[g]{game},scale=720:720:force_original_aspect_ratio=increase,'
                 'crop=720:720,setsar=1[game];[cam][game]vstack=inputs=2[body]')
    else:
        graph = (f'[0:v]fps=30,{game},scale=720:1280:force_original_aspect_ratio=increase,'
                 'crop=720:1280,setsar=1[body]')
    target.parent.mkdir(parents=True, exist_ok=True)
    args = [ffmpeg, '-v', 'error', '-nostdin', '-ss', str(start), '-i', str(source)]
    label = 'body'
    watermark = job.get('watermark_png')
    if watermark:
        args += ['-i', str(Path(watermark).resolve(strict=True))]
        graph += ';[1:v]scale=720:1280,format=rgba[mark];[body][mark]overlay=0:0[marked]'
        label = 'marked'
    captions = job.get('captions_ass')
    if captions:
        # Controlled basename avoids filtergraph escaping of arbitrary user paths.
        staged = target.with_suffix('.captions.ass')
        shutil.copyfile(Path(captions).resolve(strict=True), staged)
        # Restrict output basename used as filter input to avoid FFmpeg syntax injection.
        if not all(c.isalnum() or c in '._-' for c in staged.name):
            raise ValueError('Use letters, numbers, dot, underscore or hyphen for output basename')
        graph += f';[{label}]ass=filename={staged.name}[captioned]'
        label = 'captioned'
    args += ['-filter_complex_threads', '2', '-filter_complex', graph, '-map', f'[{label}]',
             '-map', '0:a:0', '-t', str(duration), '-c:v', 'libx264', '-threads', '2',
             '-preset', 'veryfast', '-crf', '21', '-profile:v', 'baseline', '-level:v', '3.1',
             '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '128k',
             '-movflags', '+faststart', '-n', str(target)]
    with target.with_suffix('.render.log').open('w', encoding='utf-8') as log:
        subprocess.run(args, cwd=target.parent, stdout=log, stderr=subprocess.STDOUT, check=True)
    result = probe(ffprobe, target)
    v = next(s for s in result['streams'] if s['codec_type'] == 'video')
    a = next(s for s in result['streams'] if s['codec_type'] == 'audio')
    if ((v['width'], v['height']) != (720, 1280) or v['codec_name'] != 'h264'
            or v['pix_fmt'] != 'yuv420p' or v.get('sample_aspect_ratio') != '1:1'
            or a['codec_name'] != 'aac' or abs(float(result['format']['duration']) - duration) > .15):
        raise ValueError('Output failed technical validation')
    subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(target), '-f', 'null', '-'],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    with target.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    record = dict(file=str(target), sha256=digest, source=str(source), source_start=start,
                  duration=duration, technical_validation='passed', visual_review='pending',
                  audio_review='pending', platforms={})
    target.with_suffix('.validated.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job', type=Path)
    args = parser.parse_args()
    print(json.dumps(render(json.loads(args.job.read_text(encoding='utf-8-sig')))))
