from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from PIL import Image, ImageOps

from engine import engine_tool, install_engine, locate_bun
from updates import check_update

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "stream-clip-studio"


def read_profile(state: Path) -> dict:
    try:
        return json.loads((state / "profile.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError("Configure o perfil com setup.ps1 primeiro.") from None


def save_profile(state: Path, *, name: str, handle: str, avatar: Path, media_dir: Path, engine: Path):
    handle = handle.strip().lstrip("@")
    name = name.strip()
    if not name or len(name) > 60 or any(ord(char) < 32 for char in name):
        raise ValueError("Use um nome de exibição de 1 a 60 caracteres.")
    if not re.fullmatch(r"[A-Za-z0-9_.]{1,24}", handle):
        raise ValueError("Informe um @ de 1 a 24 caracteres com letras, números, pontos ou sublinhados.")
    state.mkdir(parents=True, exist_ok=True)
    media_dir = media_dir.expanduser().resolve()
    media_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(avatar.expanduser()) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((512, 512), Image.Resampling.LANCZOS)
        image.save(state / "avatar.png")
    profile = {"name": name, "handle": "@" + handle, "avatar": str(state / "avatar.png"),
               "media_dir": str(media_dir), "engine_dir": str(engine.resolve())}
    temporary = state / "profile.json.tmp"
    temporary.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(state / "profile.json")
    return profile


def prompt_path(label: str) -> Path:
    answer = input(label).strip().strip('"').strip("'")
    if not answer:
        raise ValueError("O caminho não pode ficar vazio.")
    return Path(answer)


def scheduler(state: Path, arguments: list[str]) -> None:
    subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scheduler/scripts/main.py"),
                    "--state", str(state / "tiktok"), *arguments], check=True)


def default_schedule(state: Path, profile: dict) -> Path:
    config = state / "schedule.yaml"
    if not config.exists():
        data = {
            "folder": str(Path(profile["media_dir"]) / "SELECIONE_A_SUBPASTA_DOS_CORTES"),
            "recursive": False, "start_date": "tomorrow",
            "timezone": "America/Sao_Paulo", "per_day": 3, "times": ["12:00", "16:00", "20:00"],
            "order": "name", "caption": "{stem}", "privacy": "public", "max_per_run": 3,
            "ffprobe": str(engine_tool(Path(profile["engine_dir"]), "ffprobe")),
            "browser": {"locale": "en-US", "allow_unfiltered_content": True,
                        "selectors": {"scheduled_tab": [], "scheduled_row": ['[data-tt="components_PostTable_Absolute"]']}},
        }
        config.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return config


def local_original(path: Path, profile: dict) -> Path:
    path = path.expanduser().resolve(strict=True)
    if not path.is_file():
        raise ValueError("Informe um arquivo de vídeo.")
    dest = Path(profile["media_dir"]) / path.name
    if path == dest:
        return path
    if dest.exists():
        raise FileExistsError(f"Já há um original com esse nome: {dest}")
    with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
        staging = Path(tmp) / dest.name
        shutil.copy2(path, staging)
        staging.rename(dest)
    return dest


def import_url(url: str, profile: dict) -> Path:
    from urllib.parse import urlsplit
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}:
        raise ValueError("Use o link HTTPS de um vídeo individual do YouTube.")
    if parsed.path != "/watch" and not (parsed.hostname == "youtu.be" and parsed.path.count("/") == 1) and not any(
        parsed.path.startswith(prefix) and parsed.path.count("/") == 2 for prefix in ("/live/", "/shorts/")
    ):
        raise ValueError("Informe o link direto da gravação.")
    engine = Path(profile["engine_dir"])
    tool = engine_tool(engine, "yt-dlp")
    result = subprocess.run(
        [str(tool), "--ignore-config", "--no-playlist", "--no-overwrites", "--windows-filenames",
         "--ffmpeg-location", str(engine_tool(engine, "ffmpeg").parent), "--paths", profile["media_dir"],
         "-o", "%(title).140B [%(id)s].%(ext)s", "-f", "bv[ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
         "--merge-output-format", "mp4", "--print", "after_move:%(filepath)s", "--progress", "--", url],
        check=True, stdout=subprocess.PIPE, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip() and not line.startswith("[")]
    if not lines:
        raise ValueError("yt-dlp não retornou o caminho do vídeo original.")
    return Path(lines[-1]).resolve(strict=True)


def engine_cli(profile: dict, state: Path, args: list[str]):
    engine = Path(profile["engine_dir"])
    env = {**os.environ, "GCLIP_WORKSPACE": str(state / "gaming-workspace"),
           "FFMPEG_BIN": str(engine_tool(engine, "ffmpeg")), "FFPROBE_BIN": str(engine_tool(engine, "ffprobe")),
           "LLM_COMMAND": "", "LLM_MODEL": "", "LLM_API_KEY": ""}
    subprocess.run([str(locate_bun(engine, state)), "src/cli.ts", *args], cwd=engine, env=env, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download, corte e agendamento no Windows.")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check-update", help="Confere a revisão publicada no GitHub")
    setup = commands.add_parser("onboard")
    setup.add_argument("--existing-engine", type=Path)
    setup.add_argument("--no-login", action="store_true")
    setup.add_argument("--name")
    setup.add_argument("--avatar", type=Path)
    setup.add_argument("--handle")
    setup.add_argument("--media-dir", type=Path)
    engine_setup = commands.add_parser("install-engine")
    engine_setup.add_argument("--existing-engine", type=Path)
    commands.add_parser("login")
    source = commands.add_parser("import")
    source.add_argument("source")
    analyze = commands.add_parser("analyze")
    analyze.add_argument("source", type=Path)
    analyze.add_argument("--lang", default="auto")
    analyze.add_argument("--min", type=int, default=60)
    analyze.add_argument("--max", type=int, default=120)
    analyze.add_argument("--clips", default="auto")
    cli = commands.add_parser("gaming")
    cli.add_argument("arguments", nargs=argparse.REMAINDER)
    render = commands.add_parser("render")
    render.add_argument("source", type=Path)
    render.add_argument("--start", type=float, required=True)
    render.add_argument("--duration", type=float, required=True)
    render.add_argument("--title", required=True)
    render.add_argument("--streamer", required=True)
    render.add_argument("--webcam", help="x,y,w,h em pixels; omita se não houver webcam")
    render.add_argument("--focus-x", type=float, default=0.5)
    render.add_argument("--badge", default="", help="Selo curto opcional no cabeçalho, por exemplo GTA 6")
    render.add_argument("--preview", action="store_true", help="Salva somente uma prévia PNG do layout, sem renderizar o MP4")
    render.add_argument("--cover-title", required=True)
    render.add_argument("--cover-at", type=float, required=True, help="Segundos relativos ao começo do corte")
    render.add_argument("--words", type=Path, help="JSON de palavras em português com tempos relativos")
    schedule = commands.add_parser("schedule")
    schedule.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command == "check-update":
        sys.exit(check_update(ROOT, verbose=True))
    check_update(ROOT)
    state = args.state.expanduser().resolve()
    state.mkdir(parents=True, exist_ok=True)
    if args.command == "onboard":
        name = getattr(args, "name", None) or input("Nome de exibição: ")
        avatar = getattr(args, "avatar", None) or prompt_path("Caminho da foto de perfil: ")
        handle = getattr(args, "handle", None) or input("@ do perfil: ")
        media_dir = getattr(args, "media_dir", None) or prompt_path("Pasta para originais e cortes: ")
        engine_dir = install_engine(state, getattr(args, "existing_engine", None))
        profile = save_profile(state, name=name, handle=handle, avatar=avatar, media_dir=media_dir, engine=engine_dir)
        config = default_schedule(state, profile)
        print(f"Perfil configurado. Originais e cortes: {profile['media_dir']}", flush=True)
        if not getattr(args, "no_login", False):
            scheduler(state, ["login", "--config", str(config)])
        return
    if args.command == "install-engine":
        engine_dir = install_engine(state, args.existing_engine)
        print(engine_dir)
        return
    profile = read_profile(state)
    if args.command == "login":
        scheduler(state, ["login", "--config", str(default_schedule(state, profile))])
    elif args.command == "import":
        print(import_url(args.source, profile) if args.source.startswith("https://")
              else local_original(Path(args.source), profile))
    elif args.command == "analyze":
        engine_cli(profile, state, ["new", str(args.source.resolve(strict=True)), "--lang", args.lang,
                                    "--min", str(args.min), "--max", str(args.max), "--clips", args.clips])
    elif args.command == "gaming":
        engine_cli(profile, state, args.arguments)
    elif args.command == "render":
        from post_renderer import render_post
        print(render_post(profile, args))
    elif args.command == "schedule":
        arguments = args.arguments
        if not arguments:
            raise ValueError("Informe plan, run, pending, report, resume-plan ou reconcile.")
        if arguments[0] in {"plan", "resume-plan", "reconcile", "login"} and "--config" not in arguments:
            arguments += ["--config", str(default_schedule(state, profile))]
        scheduler(state, arguments)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as failure:
        sys.exit(failure.returncode or 1)
    except (OSError, ValueError, KeyboardInterrupt) as failure:
        print(f"Erro: {failure}", file=sys.stderr)
        sys.exit(1)
