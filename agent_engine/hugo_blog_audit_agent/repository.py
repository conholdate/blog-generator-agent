from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def _safe_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        netloc = parsed.hostname or ""
        if parsed.port:
            netloc += f":{parsed.port}"
        return parsed._replace(netloc=netloc).geturl()
    return url


def prepare_repository(repo_url: str, branch: str | None, workdir: Path, keep_workdir: bool = False) -> Path:
    source = Path(repo_url)
    workdir.mkdir(parents=True, exist_ok=True)
    if source.exists():
        return source.resolve()

    repo_name = Path(urlparse(repo_url).path).stem or "repo"
    target = workdir / repo_name
    if target.exists() and not keep_workdir:
        shutil.rmtree(target)
    if not target.exists():
        cmd = ["git", "clone", "--depth", "1"]
        if branch:
            cmd += ["--branch", branch]
        cmd += [repo_url, str(target)]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Git clone failed for {_safe_url(repo_url)}: {exc.stderr.strip()}") from exc
    return target.resolve()
