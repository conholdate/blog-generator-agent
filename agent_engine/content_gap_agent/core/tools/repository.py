"""
content_gap_agent/core/tools/repository.py

Repository fetching (git clone/pull OR GitHub zipball) + markdown extraction.

Key goals for GitHub Actions:
- Avoid flaky git authentication by supporting GitHub API zipball downloads.
- Never embed tokens in repo URLs.
- Robust URL normalization (handles trailing slashes, .git suffix, ssh form).
"""

from __future__ import annotations

import base64
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple


class RepositoryAnalyzer:
    """
    Fetches repositories into a local cache directory and extracts markdown files.

    Fetch modes:
      - "zip":  GitHub API zipball (requires token; best for CI/GitHub Actions)
      - "git":  git clone/pull (optionally authenticated via http.extraheader)
      - "auto": prefer zip in GitHub Actions if a token is available; otherwise git

    Token discovery (first found wins):
      - github_token argument
      - env: GITHUB_TOKEN
      - env: GH_TOKEN
      - env: ASPOSE_BLOG_TOKEN  (common in your workflows)

    Fetch mode discovery:
      - fetch_mode argument
      - env: CONTENT_GAP_REPO_FETCH
      - env: BTA_REPO_FETCH
      - default: "auto"
    """

    def __init__(
        self,
        cache_dir: str = "./repo_cache",
        fetch_mode: Optional[str] = None,
        github_token: Optional[str] = None,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        env_mode = (os.getenv("CONTENT_GAP_REPO_FETCH") or os.getenv("BTA_REPO_FETCH") or "").strip()
        self.fetch_mode = (fetch_mode or env_mode or "auto").strip().lower()

        self.github_token = (
            (github_token or "").strip()
            or (os.getenv("GITHUB_TOKEN") or "").strip()
            or (os.getenv("GH_TOKEN") or "").strip()
            or (os.getenv("ASPOSE_BLOG_TOKEN") or "").strip()
        )

    # -------------------------
    # Public API
    # -------------------------

    def clone_or_update_repo(self, repo_url: str, branch: str = "master") -> Path:
        """
        Fetch repository content into cache_dir/<repo_name> and return local path.

        NOTE: branch is treated as a ref:
          - zip mode: passed to /zipball/<ref>
          - git mode: used for checkout/reset to origin/<branch> when possible
        """
        repo_url_norm = self._normalize_repo_url(repo_url)
        repo_name = self._repo_name_from_url(repo_url_norm)
        if not repo_name:
            raise ValueError(f"Could not derive repo name from URL: {repo_url!r}")

        repo_path = self.cache_dir / repo_name

        print(f"Processing repository: {repo_name}")

        if self._should_use_zip():
            print("  Fetch mode: zipball (GitHub API)")
            owner_repo = self._parse_github_owner_repo(repo_url_norm)
            if not owner_repo:
                raise RuntimeError(f"ZIP fetch only supports github.com repos. Got: {repo_url_norm}")
            owner, repo = owner_repo
            zip_path = self._download_github_zip(owner=owner, repo=repo, ref=branch)
            self._extract_zip_to(zip_path=zip_path, dest_dir=repo_path)
        else:
            print("  Fetch mode: git")
            self._git_clone_or_update(repo_url=repo_url_norm, dest_dir=repo_path, branch=branch)

        print(f"  Repository ready at {repo_path}")
        return repo_path

    def extract_markdown_files(self, repo_path: Path, subpath: str = "") -> List[Tuple[Path, str]]:
        """Extract all markdown files from repository (optionally under subpath)."""
        search_path = repo_path / subpath if subpath else repo_path
        md_files: List[Tuple[Path, str]] = []

        for md_file in search_path.rglob("*.md"):
            if ".git" in str(md_file):
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
                md_files.append((md_file, content))
            except Exception as e:
                print(f"  Warning: Could not read {md_file}: {e}")

        print(f"  Found {len(md_files)} markdown files")
        return md_files

    # -------------------------
    # Mode selection / parsing
    # -------------------------

    def _should_use_zip(self) -> bool:
        if self.fetch_mode == "zip":
            return True
        if self.fetch_mode == "git":
            return False

        # auto
        in_actions = (os.getenv("GITHUB_ACTIONS") or "").strip().lower() == "true"
        if in_actions and self.github_token:
            return True
        return False

    @staticmethod
    def _normalize_repo_url(repo_url: str) -> str:
        # Normalize whitespace and strip trailing slashes to avoid repo_name == "".
        return (repo_url or "").strip().rstrip("/")

    @staticmethod
    def _repo_name_from_url(repo_url: str) -> str:
        # Works for https://github.com/OWNER/REPO(.git) and git@github.com:OWNER/REPO(.git)
        u = RepositoryAnalyzer._normalize_repo_url(repo_url)

        if u.startswith("git@github.com:"):
            path = u.split("git@github.com:", 1)[1]
            last = path.split("/")[-1]
        else:
            last = u.split("/")[-1]

        return last.replace(".git", "").strip()

    @staticmethod
    def _parse_github_owner_repo(repo_url: str) -> Optional[tuple[str, str]]:
        """
        Supports:
          - https://github.com/OWNER/REPO(.git)
          - git@github.com:OWNER/REPO(.git)
        """
        u = RepositoryAnalyzer._normalize_repo_url(repo_url)

        if u.startswith("git@github.com:"):
            path = u.split("git@github.com:", 1)[1]
        else:
            parsed = urllib.parse.urlparse(u)
            if parsed.netloc.lower() != "github.com":
                return None
            path = parsed.path.lstrip("/")

        parts = [p for p in path.split("/") if p]
        if len(parts) < 2:
            return None

        owner = parts[0]
        repo = parts[1].replace(".git", "")
        return owner, repo

    # -------------------------
    # ZIP (GitHub API) fetch
    # -------------------------

    def _download_github_zip(self, owner: str, repo: str, ref: str) -> Path:
        if not self.github_token:
            raise RuntimeError("ZIP fetch requires a GitHub token (GITHUB_TOKEN/GH_TOKEN/ASPOSE_BLOG_TOKEN).")

        url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{ref}"
        req = urllib.request.Request(
            url=url,
            headers={
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "content-gap-agent",
            },
            method="GET",
        )

        fd, tmp_path = tempfile.mkstemp(prefix="repo_", suffix=".zip")
        os.close(fd)
        zip_path = Path(tmp_path)

        try:
            with urllib.request.urlopen(req, timeout=120) as resp, zip_path.open("wb") as f:
                shutil.copyfileobj(resp, f)
            return zip_path
        except urllib.error.HTTPError as e:
            # 404 here usually indicates: no repo access with this token (GitHub masks private repos as 404)
            detail = ""
            try:
                detail = e.read(200).decode("utf-8", errors="ignore")
            except Exception:
                pass
            zip_path.unlink(missing_ok=True)
            raise RuntimeError(f"GitHub zipball download failed: HTTP {e.code}. {detail}".strip()) from e
        except Exception:
            zip_path.unlink(missing_ok=True)
            raise

    @staticmethod
    def _extract_zip_to(zip_path: Path, dest_dir: Path) -> None:
        tmp_extract_root = Path(tempfile.mkdtemp(prefix="repo_zip_extract_"))
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp_extract_root)

            # GitHub zipballs extract into a single top-level directory
            children = [p for p in tmp_extract_root.iterdir() if p.is_dir()]
            if not children:
                raise RuntimeError("Zipball extract produced no directory content.")

            extracted_root = children[0]

            if dest_dir.exists():
                shutil.rmtree(dest_dir, ignore_errors=True)
            dest_dir.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(extracted_root), str(dest_dir))
        finally:
            try:
                zip_path.unlink(missing_ok=True)
            except Exception:
                pass
            shutil.rmtree(tmp_extract_root, ignore_errors=True)

    # -------------------------
    # GIT fetch (subprocess)
    # -------------------------

    def _git_clone_or_update(self, repo_url: str, dest_dir: Path, branch: str) -> None:
        """
        Clone/pull with optional header-based auth (token never in URL).

        Implementation uses git subprocess directly for reliability across environments.
        """
        auth_args = self._git_auth_config_args()

        if dest_dir.exists() and (dest_dir / ".git").exists():
            # Update existing clone. Prefer a hard reset to origin/<branch> for deterministic cache state.
            self._git(["-C", str(dest_dir), *auth_args, "fetch", "--prune", "origin"])

            # Try to reset to origin/<branch>. If branch doesn't exist remotely, fall back to plain pull.
            reset_target = f"origin/{branch}"
            if self._git_ok(["-C", str(dest_dir), *auth_args, "rev-parse", "--verify", "--quiet", reset_target]):
                self._git(["-C", str(dest_dir), *auth_args, "checkout", "-f", branch], allow_fail=True)
                self._git(["-C", str(dest_dir), *auth_args, "reset", "--hard", reset_target])
            else:
                # Best-effort pull for current branch
                self._git(["-C", str(dest_dir), *auth_args, "pull", "--ff-only", "origin"], allow_fail=True)
            return

        if dest_dir.exists():
            shutil.rmtree(dest_dir, ignore_errors=True)

        # Shallow clone is sufficient for indexing; faster and smaller.
        self._git(
            [
                *auth_args,
                "clone",
                "--depth",
                "1",
                "--branch",
                branch,
                repo_url,
                str(dest_dir),
            ],
            allow_fail=True,
        )

        # If branch clone failed (branch missing), fall back to default branch clone.
        if not (dest_dir / ".git").exists():
            self._git(
                [
                    *auth_args,
                    "clone",
                    "--depth",
                    "1",
                    repo_url,
                    str(dest_dir),
                ]
            )

    def _git_auth_config_args(self) -> List[str]:
        """
        Build git config args to authenticate without leaking token in URL:
          git -c http.extraheader="AUTHORIZATION: basic <base64(x-access-token:TOKEN)>"
        """
        if not self.github_token:
            return []

        b64 = base64.b64encode(f"x-access-token:{self.github_token}".encode("utf-8")).decode("utf-8")
        header = f"AUTHORIZATION: basic {b64}"
        return ["-c", f"http.extraheader={header}"]

    @staticmethod
    def _git(cmd: List[str], allow_fail: bool = False) -> None:
        full = ["git", *cmd]
        p = subprocess.run(full, text=True, capture_output=True)
        if p.returncode != 0 and not allow_fail:
            # Avoid printing any auth headers/tokens; stderr from git is safe here.
            raise RuntimeError(f"git failed ({p.returncode}): {p.stderr.strip() or p.stdout.strip()}")

    @staticmethod
    def _git_ok(cmd: List[str]) -> bool:
        full = ["git", *cmd]
        p = subprocess.run(full, text=True, capture_output=True)
        return p.returncode == 0
