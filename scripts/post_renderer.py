from __future__ import annotations

import json
import math
import re
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

from engine import engine_tool

W, H = 1080, 1920
LEFT, TOP, BOTTOM, WIDTH = 0, 300, 1920, 1080
SAFE_LEFT, SAFE_RIGHT = 104, 936
SAFE_WIDTH = SAFE_RIGHT - SAFE_LEFT
AVATAR_TOP = 56
CREDIT_TOP = 1740
CAPTION_X, CAPTION_Y = 520, 1530
WATERMARK_SIZE = 46
CAM_X, CAM_Y, CAM_WIDTH, CAM_HEIGHT = 36, 332, 270, 220
BG = (251, 251, 250, 255)


def crop_aspect(rect, ratio, focus_x=0.5, focus_y=0.5):
    x, y, w, h = rect
    ow, oh = w, h
    if w / h > ratio:
        ow = max(2, min(w, round(h * ratio / 2) * 2))
    else:
        oh = max(2, min(h, round(w / ratio / 2) * 2))
    return (x + round((w - ow) * focus_x / 2) * 2, y + round((h - oh) * focus_y / 2) * 2, ow, oh)


def valid_webcam(value, width, height):
    if not value:
        return None
    parts = [int(item) for item in value.split(",")]
    if len(parts) != 4:
        raise ValueError("A webcam deve usar x,y,w,h.")
    x, y, w, h = [item // 2 * 2 for item in parts]
    if min(x, y) < 0 or min(w, h) < 16 or x + w > width or y + h > height:
        raise ValueError("O recorte da webcam sai da imagem original.")
    return x, y, w, h


def probe(probe_bin, source):
    result = subprocess.run(
        [str(probe_bin), "-v", "error", "-show_entries",
         "stream=codec_name,codec_type,width,height,avg_frame_rate:format=duration", "-of", "json", str(source)],
        check=True, capture_output=True, encoding="utf-8",
    )
    return json.loads(result.stdout)


def wrap_title(draw, text, face, max_width):
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and draw.textlength(candidate, font=face) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    return lines + ([current] if current else [])


def write_art(scratch, profile, args, still, cam, game, cam_height, fonts):
    def face(name, size):
        return ImageFont.truetype(str(fonts / name), size)

    mask = Image.new("L", (W, H))
    ImageDraw.Draw(mask).rectangle((LEFT, TOP, LEFT + WIDTH - 1, BOTTOM - 1), fill=255)
    border = Image.new("RGBA", (W, H), BG)
    border.putalpha(ImageChops.invert(mask))
    draw = ImageDraw.Draw(border)
    with Image.open(profile["avatar"]) as picture:
        picture = ImageOps.fit(picture.convert("RGBA"), (94, 94))
        circle = Image.new("L", picture.size)
        ImageDraw.Draw(circle).ellipse((0, 0, 93, 93), fill=255)
        border.paste(picture, (SAFE_LEFT, AVATAR_TOP), circle)
    bold = "Poppins-ExtraBold.ttf"
    regular = "Poppins-SemiBold.ttf"
    name_x = SAFE_LEFT + 112
    size = 44
    badge = getattr(args, "badge", "") or profile.get("badge", "")
    name_right = SAFE_RIGHT - 134 if badge else SAFE_RIGHT
    while size > 12 and draw.textlength(profile["name"], font=face(bold, size)) > name_right - name_x:
        size -= 2
    draw.text((name_x, AVATAR_TOP + 1), profile["name"], font=face(bold, size), fill="#171722")
    draw.text((name_x, AVATAR_TOP + 57), profile["handle"], font=face(regular, 28), fill="#676576")
    if badge:
        badge_face = face(bold, 26)
        while draw.textlength(badge, font=badge_face) > 106:
            badge = badge[:-1]
        draw.rounded_rectangle((SAFE_RIGHT - 122, 68, SAFE_RIGHT, 130), radius=14, fill="#e6dcff")
        draw.text((SAFE_RIGHT - 61, 99), badge, anchor="mm", font=badge_face, fill="#50317b")
    title_size = 46
    while title_size > 28 and len(wrap_title(draw, args.title, face(bold, title_size), SAFE_WIDTH)) > 2:
        title_size -= 2
    title_face = face(bold, title_size)
    lines = wrap_title(draw, args.title, title_face, SAFE_WIDTH)
    for index, line in enumerate(lines[:2]):
        if draw.textlength(line, font=title_face) > SAFE_WIDTH or (index == 1 and len(lines) > 2):
            while draw.textlength(line + "…", font=title_face) > SAFE_WIDTH:
                line = line[:-1]
            line = line.rstrip() + "…"
        draw.text((SAFE_LEFT, 176 + index * (title_size + 7)), line, font=title_face, fill="#171722")
    credit = "@" + args.streamer.lstrip("@")
    credit_size = 31
    while draw.textlength(credit, font=face(regular, credit_size)) > SAFE_WIDTH:
        credit_size -= 1
    draw.text((SAFE_LEFT, CREDIT_TOP), credit, font=face(regular, credit_size), fill="#ffffff",
              stroke_width=2, stroke_fill="#222222")
    if cam:
        draw.rectangle((CAM_X - 2, CAM_Y - 2, CAM_X + CAM_WIDTH + 1, CAM_Y + CAM_HEIGHT + 1),
                       outline=(255, 255, 255, 220), width=2)

    watermark = Image.new("RGBA", (W, H))
    watermark_size = WATERMARK_SIZE
    while draw.textlength(profile["handle"], font=face(bold, watermark_size)) > SAFE_WIDTH:
        watermark_size -= 2
    ImageDraw.Draw(watermark).text((SAFE_RIGHT, TOP + 370), profile["handle"], font=face(bold, watermark_size),
                                  anchor="rm", fill=(255, 255, 255, 38),
                                  stroke_width=1, stroke_fill=(0, 0, 0, 38))
    Image.alpha_composite(border, watermark).save(scratch / "layout.png")
    cover = Image.new("RGBA", (W, H), BG)
    def paste(rect, x, y, w, h):
        x0, y0, w0, h0 = rect
        image = still.crop((x0, y0, x0 + w0, y0 + h0)).resize((w, h), Image.Resampling.LANCZOS)
        cover.paste(image, (x, y))
    paste(game, LEFT, TOP, WIDTH, BOTTOM - TOP)
    if cam:
        paste(cam, CAM_X, CAM_Y, CAM_WIDTH, CAM_HEIGHT)
    cover = Image.alpha_composite(cover, border)
    Image.alpha_composite(cover, watermark).save(scratch / "preview.png")
    cover_draw = ImageDraw.Draw(cover)
    size = 115
    while True:
        label = face("Anton-Regular.ttf", size)
        lines = wrap_title(cover_draw, args.cover_title.upper(), label, 790)
        if len(lines) <= 2 and all(cover_draw.textlength(line, font=label) <= 790 for line in lines):
            break
        size -= 5
        if size < 35:
            raise ValueError("Use uma chamada curta na capa.")
    top = CAM_Y + CAM_HEIGHT + 60 if cam else TOP + 82
    cover_draw.rounded_rectangle((SAFE_LEFT, top, SAFE_RIGHT, top + (size + 22) * len(lines) + 56),
                                 radius=36, fill="#19162e")
    for index, line in enumerate(lines):
        cover_draw.text(((SAFE_LEFT + SAFE_RIGHT) // 2, top + 22 + (size + 22) * index), line, font=label,
                        anchor="mt", fill="#f8ed36" if index == len(lines) - 1 else "#ffffff")
    Image.alpha_composite(cover, watermark).save(scratch / "cover.png")


def ass_time(seconds):
    centis = round(seconds * 100)
    hour, rest = divmod(centis, 360000)
    minute, rest = divmod(rest, 6000)
    sec, rest = divmod(rest, 100)
    return f"{hour}:{minute:02}:{sec:02}.{rest:02}"


ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
WrapStyle: 2
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Pop,Bangers,64,&H0047E3FF,&H0047E3FF,&H003B0F1B,&H003B0F1B,0,0,0,0,100,100,0,0,1,6,2,5,104,144,0,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""


def write_words(path, words_file, duration):
    words = json.loads(words_file.read_text(encoding="utf-8"))
    groups = []
    for word in words:
        start, end = float(word["start"]), float(word["end"])
        if not math.isfinite(start) or not math.isfinite(end) or not 0 <= start < end <= duration:
            raise ValueError("Tempo de legenda inválido. Use segundos relativos ao início do corte.")
        if word.get("language") != "pt":
            continue
        text = str(word["text"]).strip().upper()
        if not text:
            continue
        text = text.translate(str.maketrans({"\\": "＼", "{": "(", "}": ")", "\n": " ", "\r": " "}))
        if (not groups or len(groups[-1]) == 3 or start - groups[-1][-1][2] > 0.55
                or len(text) + sum(len(item[0]) + 1 for item in groups[-1]) > 23):
            groups.append([])
        groups[-1].append((text, start, end))
    events = []
    for group in groups:
        for index, (_, start, end) in enumerate(group):
            if index + 1 < len(group):
                end = group[index + 1][1]
            if end <= start:
                continue
            line = " ".join(r"{\1c&H9A3EFF&\fscx110\fscy110}" + w[0] + r"{\r}" if i == index else w[0]
                            for i, w in enumerate(group))
            events.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Pop,,0,0,0,," +
                          f"{{\\pos({CAPTION_X},{CAPTION_Y})}}" + line)
    path.write_text(ASS_HEADER + "\n".join(events) + "\n", encoding="utf-8")


def video_encoder(ffmpeg):
    nvenc = ("-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", "20", "-b:v", "0")
    test = subprocess.run([str(ffmpeg), "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=s=256x256",
                           "-frames:v", "1", *nvenc, "-f", "null", "-"], capture_output=True)
    return nvenc if test.returncode == 0 else ("-c:v", "libx264", "-preset", "veryfast", "-crf", "19")


def render_post(profile, args):
    source = args.source.resolve(strict=True)
    engine = Path(profile["engine_dir"])
    ffmpeg, ffprobe = (engine_tool(engine, name) for name in ("ffmpeg", "ffprobe"))
    metadata = probe(ffprobe, source)
    video = next((item for item in metadata["streams"] if item["codec_type"] == "video"), None)
    duration = args.duration
    if not video or not 0 <= args.start or not 1 <= duration <= 180 or not 0 <= args.cover_at < duration:
        raise ValueError("Valide o vídeo, os tempos do corte e a posição da capa (relativa ao início).")
    if args.start + duration > float(metadata["format"]["duration"]) + 0.02:
        raise ValueError("O corte ultrapassa o fim do vídeo.")
    if not 0 <= args.focus_x <= 1 or not re.fullmatch(r"@?[A-Za-z0-9_.]{1,40}", args.streamer):
        raise ValueError("Informe um @ do streamer válido e focus-x entre 0 e 1.")
    if not 2 <= len(args.cover_title.split()) <= 5 or not args.title.strip():
        raise ValueError("Informe um título e uma chamada de capa de 2 a 5 palavras.")
    width, height = int(video["width"]) // 2 * 2, int(video["height"]) // 2 * 2
    webcam = valid_webcam(args.webcam, width, height)
    cam_height = CAM_HEIGHT if webcam else 0
    game_height = BOTTOM - TOP
    cam = crop_aspect(webcam, CAM_WIDTH / CAM_HEIGHT, focus_x=0.65, focus_y=0.30) if webcam else None
    game = crop_aspect((0, 0, width, height), WIDTH / game_height, args.focus_x)
    if webcam and game[0] < webcam[0] + webcam[2] <= width - game[2] and webcam[0] < width / 3:
        game = (webcam[0] + webcam[2], game[1], game[2], game[3])
    audio = any(item["codec_type"] == "audio" for item in metadata["streams"])
    rate = 60 if float(Fraction(video["avg_frame_rate"])) >= 50 else 30
    dest = Path(profile["media_dir"]) / source.stem
    dest.mkdir(parents=True, exist_ok=True)
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "", args.title).strip(" .")[:120].rstrip(" .")
    preview = getattr(args, "preview", False)
    target = dest / f"{title or 'Corte'}{'.preview.png' if preview else '.mp4'}"
    if target.exists():
        raise FileExistsError(f"Já existe um corte com esse nome: {target}")
    with tempfile.TemporaryDirectory(dir=dest) as tmp:
        work = Path(tmp)
        subprocess.run([str(ffmpeg), "-nostdin", "-v", "error", "-ss", str(args.start + args.cover_at),
                        "-i", str(source), "-frames:v", "1", "still.png"], cwd=work, check=True)
        fonts = engine / "assets/fonts"
        with Image.open(work / "still.png") as still:
            write_art(work, profile, args, still.convert("RGB"), cam, game, cam_height, fonts)
        if preview:
            (work / "preview.png").rename(target)
            return target
        def geometry(rect, output_w, output_h):
            x, y, w, h = rect
            return f"crop={w}:{h}:{x}:{y},scale={output_w}:{output_h}"
        graph = f"color=c=0xfbfbfa:s={W}x{H}:r={rate}:d={duration}[base];"
        if cam:
            graph += (f"[0:v]fps={rate},split=2[g][c];[g]{geometry(game, WIDTH, game_height)}[game];"
                      f"[base][game]overlay={LEFT}:{TOP}:shortest=1[frame];[c]{geometry(cam, CAM_WIDTH, CAM_HEIGHT)}[cam];"
                      f"[frame][cam]overlay={CAM_X}:{CAM_Y}:shortest=1[body];")
        else:
            graph += (f"[0:v]fps={rate},{geometry(game, WIDTH, game_height)}[game];"
                      f"[base][game]overlay={LEFT}:{TOP}:shortest=1[body];")
        chain = "[body][1:v]overlay=0:0"
        if args.words:
            write_words(work / "captions.ass", args.words, duration)
            (work / "fonts").mkdir()
            (work / "fonts/Bangers-Regular.ttf").write_bytes((fonts / "Bangers-Regular.ttf").read_bytes())
            chain += ",ass=captions.ass:fontsdir=fonts"
        graph += chain + f"[layout];[layout][2:v]overlay=0:0:enable='lt(t,{0.5 / rate})'[out]"
        cmd = [str(ffmpeg), "-nostdin", "-v", "error", "-stats", "-ss", str(args.start), "-i", str(source),
               "-i", "layout.png", "-i", "cover.png", "-filter_complex_threads", "4", "-filter_complex", graph,
               "-map", "[out]", "-map", "0:a:0?", "-t", str(duration), *video_encoder(ffmpeg),
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "clip.mp4"]
        subprocess.run(cmd, cwd=work, check=True)
        result = probe(ffprobe, work / "clip.mp4")
        encoded = next(item for item in result["streams"] if item["codec_type"] == "video")
        if ((encoded["width"], encoded["height"]) != (W, H)
                or abs(float(result["format"]["duration"]) - duration) > 0.12
                or audio != any(item["codec_type"] == "audio" for item in result["streams"])):
            raise RuntimeError("O MP4 de teste não bate com a resolução, duração ou áudio esperados.")
        (work / "clip.mp4").rename(target)
    return target
