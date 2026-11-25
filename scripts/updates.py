from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPOSITORY = "NicollasDev7/stream-clip-studio"
BRANCH = "main"
GITHUB_URL = f"https://github.com/{REPOSITORY}"
SHA = re.compile(r"^[0-9a-f]{40}$")


def github_get(path: str):
    endpoint = f"repos/{REPOSITORY}/{path}"
    gh = shutil.which("gh")
    if gh:
        try:
            result = subprocess.run(
                [gh, "api", "--hostname", "github.com", endpoint],
                capture_output=True, encoding="utf-8", timeout=6, check=True,
                env={**os.environ, "GH_PROMPT_DISABLED": "1"},
            )
            return json.loads(result.stdout)
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    request = urllib.request.Request(
        f"https://api.github.com/{endpoint}",
        headers={"User-Agent": "stream-clip-studio", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def git_output(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          timeout=4, check=True).stdout.strip()


def installed_revision(root: Path) -> str | None:
    marker = root / ".studio-revision"
    if marker.is_file():
        value = marker.read_text(encoding="ascii").strip()
        if SHA.fullmatch(value):
            return value
    if (root / ".git").exists():
        top = Path(git_output(root, "rev-parse", "--show-toplevel")).resolve()
        if top == root.resolve():
            value = git_output(root, "rev-parse", "HEAD")
            if SHA.fullmatch(value):
                return value
    return None


def blob_id(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data, usedforsecurity=False).hexdigest()


def content_matches(root: Path, tree: dict) -> bool:
    if tree.get("truncated") or not isinstance(tree.get("tree"), list):
        raise ValueError("A lista de arquivos do GitHub está incompleta.")
    blobs = [item for item in tree["tree"] if item["type"] == "blob"]
    if not blobs:
        raise ValueError("A árvore do GitHub não contém arquivos.")
    for item in blobs:
        file = (root / item["path"]).resolve()
        if not file.is_relative_to(root.resolve()) or not file.is_file():
            return False
        data = file.read_bytes()
        if blob_id(data) != item["sha"] and blob_id(data.replace(b"\r\n", b"\n")) != item["sha"]:
            return False
    return True


def check_update(root: Path, *, verbose: bool = False) -> int:
    try:
        commit = github_get(f"commits/{BRANCH}")
        latest = commit["sha"]
        if not SHA.fullmatch(latest):
            raise ValueError("Revisão do GitHub inválida.")
        installed = installed_revision(root)
        if installed == latest:
            current = True
        elif installed:
            comparison = github_get(f"compare/{installed}...{latest}")
            state = comparison["status"]
            if state in {"diverged", "behind"}:
                if verbose:
                    print("A cópia local está adiantada ou divergiu do GitHub; revise antes de substituir.")
                return 0
            current = state == "identical"
        else:
            tree = commit["commit"]["tree"]["sha"]
            if not SHA.fullmatch(tree):
                raise ValueError("Árvore do GitHub inválida.")
            current = content_matches(root, github_get(f"git/trees/{tree}?recursive=1"))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        if verbose:
            print(f"Não foi possível conferir atualizações: {error}", file=sys.stderr)
            print("Para um repositório privado, autentique o GitHub CLI com gh auth login.", file=sys.stderr)
        return 1
    if not current:
        print(f"Stream Clip Studio: atualização disponível ({latest[:8]}). "
              f"Veja {GITHUB_URL}/commit/{latest}.", file=sys.stderr)
        print("Use git pull em um clone, ou reinstale a skill com os arquivos mais recentes.", file=sys.stderr)
    elif verbose:
        print(f"Stream Clip Studio está atualizado ({latest[:8]}).")
    return 0
