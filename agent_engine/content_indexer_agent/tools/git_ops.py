from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Iterable, Optional, Sequence

log = logging.getLogger(__name__)


# -----------------------------
# Exceptions
# -----------------------------
@dataclass(frozen=True)
class CommandError(RuntimeError):
    cmd: Sequence[str]
    returncode: int
    stdout: str
    stderr: str

    def __str__(self) -> str:
        return (
            f"Command failed ({self.returncode}): {' '.join(self.cmd)}\n"
            f"STDOUT:\n{self.stdout}\n"
            f"STDERR:\n{self.stderr}"
        )


class GitNetworkError(RuntimeError):
    """Raised when git fails due to network/DNS/proxy/TLS issues."""


class GitTimeoutError(RuntimeError):
    """Raised when a git command exceeds the configured timeout."""


# -----------------------------
# Public API
# -----------------------------
def ensure_repo_cloned(repo_url: str, branch: str, dest_dir: Path) -> Path:
    """
    Ensure a git repo exists at dest_dir.
    - If repo already exists: fetch + checkout + pull.
    - Else: clone shallow.
    Raises GitNetworkError with actionable guidance for common network issues.
    """
    dest_dir.parent.mkdir(parents=True, exist_ok=True)

    if _has_healthy_repo(dest_dir):
        log.info("Updating repo: %s", dest_dir)
        _run(["git", "-C", str(dest_dir), "fetch", "--all", "--prune"], timeout_s=300)
        _run(["git", "-C", str(dest_dir), "checkout", branch], timeout_s=120)
        _run(["git", "-C", str(dest_dir), "pull", "--ff-only"], timeout_s=300)
    else:
        if dest_dir.exists():
            log.warning("Removing incomplete repo clone before retry: %s", dest_dir)
            _remove_incomplete_repo(dest_dir)
        log.info("Cloning repo: %s -> %s", repo_url, dest_dir)
        _run(
            ["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(dest_dir)],
            timeout_s=600,
        )

    return dest_dir


def get_head_commit(repo_dir: Path) -> str:
    p = subprocess.run(
        ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        env=_git_env(),
    )
    return p.stdout.strip() if p.returncode == 0 else ""


# -----------------------------
# Internals
# -----------------------------
def _run(cmd: list[str], *, timeout_s: int) -> None:
    log.info("Running git command: %s", " ".join(cmd))
    t0 = perf_counter()

    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=_git_env(),
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed_ms = (perf_counter() - t0) * 1000.0
        raise GitTimeoutError(
            f"Git command timed out after {timeout_s}s ({elapsed_ms:.0f} ms): {' '.join(cmd)}"
        ) from exc

    if p.returncode == 0:
        log.info("Git command completed in %.0f ms: %s", (perf_counter() - t0) * 1000.0, " ".join(cmd))
        return

    err = CommandError(
        cmd=cmd,
        returncode=p.returncode,
        stdout=p.stdout or "",
        stderr=p.stderr or "",
    )

    # Improve operator experience: detect network-ish failures and raise a targeted message.
    category = _classify_git_failure(err.stderr)
    if category is not None:
        raise GitNetworkError(_format_git_network_guidance(err, category)) from err

    raise err


def _has_healthy_repo(dest_dir: Path) -> bool:
    git_dir = dest_dir / ".git"
    if not dest_dir.exists() or not git_dir.exists():
        return False
    if (git_dir / "shallow.lock").exists():
        return False

    head = _git_stdout(["git", "-C", str(dest_dir), "rev-parse", "HEAD"])
    if not head:
        return False

    is_work_tree = _git_stdout(["git", "-C", str(dest_dir), "rev-parse", "--is-inside-work-tree"])
    if is_work_tree.strip().lower() != "true":
        return False

    return True


def _git_stdout(cmd: list[str]) -> str:
    p = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=_git_env(),
    )
    if p.returncode != 0:
        return ""
    return (p.stdout or "").strip()


def _remove_incomplete_repo(dest_dir: Path) -> None:
    if not dest_dir.exists():
        return
    shutil.rmtree(dest_dir)


def _git_env() -> dict[str, str]:
    """
    Provide a controlled environment for git.
    - Respects existing process env.
    - Optionally supports proxy env vars if set (common in CI/corp networks).
    - Forces non-interactive behavior so indexing jobs fail fast instead of
      hanging on credential-manager or askpass flows.
    - Skips Git LFS smudge downloads since the indexer only needs the repo
      contents on disk, not hydrated large binary assets during clone.
    """
    env = dict(os.environ)
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    env.setdefault("GCM_INTERACTIVE", "Never")
    env.setdefault("GIT_ASKPASS", "")
    env.setdefault("SSH_ASKPASS", "")
    env.setdefault("GIT_LFS_SKIP_SMUDGE", "1")

    # If callers set these env vars, git/curl will use them automatically.
    # Examples:
    #   HTTPS_PROXY=http://proxy.company.com:8080
    #   HTTP_PROXY=http://proxy.company.com:8080
    #   NO_PROXY=localhost,127.0.0.1
    # We do not invent values here; we simply pass through.
    return env


def _classify_git_failure(stderr: str) -> Optional[str]:
    """
    Return one of: dns | proxy | tls | timeout | network
    or None if not recognized as a network issue.
    """
    s = (stderr or "").lower()

    # DNS resolution errors
    if "could not resolve host" in s or "name or service not known" in s:
        return "dns"

    # Proxy / proxy auth errors
    if "proxy" in s and (
        "tunnel" in s
        or "connect" in s
        or "407" in s
        or "proxy authentication required" in s
        or "received http code 407" in s
    ):
        return "proxy"

    # TLS / cert errors
    if any(x in s for x in ["ssl", "tls", "certificate", "schannel", "x509"]):
        return "tls"

    # Timeouts / connect failures
    if "timed out" in s or "timeout" in s:
        return "timeout"
    if "failed to connect" in s or "connection refused" in s or "connection reset" in s:
        return "network"

    return None


def _format_git_network_guidance(err: CommandError, category: str) -> str:
    """
    Build a concise, actionable error message.
    """
    base = str(err).rstrip()

    if category == "dns":
        return (
            f"{base}\n\n"
            "Diagnosis: DNS resolution failure. The host (e.g., github.com) cannot be resolved from this environment.\n"
            "Actions:\n"
            "- Run: nslookup github.com\n"
            "- Run: curl -I https://github.com (or equivalent) to confirm outbound HTTPS.\n"
            "- If behind a corporate proxy, set HTTPS_PROXY/HTTP_PROXY env vars or configure git proxy:\n"
            "  git config --global http.proxy  http://<proxy>:<port>\n"
            "  git config --global https.proxy http://<proxy>:<port>\n"
            "- If outbound internet is blocked, use an internal mirror or pre-cloned local repositories."
        )

    if category == "proxy":
        return (
            f"{base}\n\n"
            "Diagnosis: Proxy connectivity/authentication issue.\n"
            "Actions:\n"
            "- Set proxy env vars (preferred in CI):\n"
            "  HTTPS_PROXY=http://<proxy>:<port>\n"
            "  HTTP_PROXY=http://<proxy>:<port>\n"
            "  NO_PROXY=localhost,127.0.0.1\n"
            "- Or configure git proxy:\n"
            "  git config --global http.proxy  http://<proxy>:<port>\n"
            "  git config --global https.proxy http://<proxy>:<port>\n"
            "- If your proxy requires auth, include credentials as required by your org policy."
        )

    if category == "tls":
        return (
            f"{base}\n\n"
            "Diagnosis: TLS/certificate validation failure (often caused by TLS inspection or missing corporate root CA).\n"
            "Actions:\n"
            "- Ensure the corporate root CA is installed in the OS trust store.\n"
            "- If a proxy is required, configure HTTPS_PROXY/HTTP_PROXY or git proxy settings.\n"
            "- Avoid disabling SSL verification except as a last-resort diagnostic step."
        )

    if category == "timeout":
        return (
            f"{base}\n\n"
            "Diagnosis: Network timeout.\n"
            "Actions:\n"
            "- Confirm you can reach GitHub: curl -I https://github.com\n"
            "- Check firewall rules and proxy requirements.\n"
            "- If running in CI, verify the runner has outbound internet access."
        )

    # category == "network"
    return (
        f"{base}\n\n"
        "Diagnosis: Network connectivity failure.\n"
        "Actions:\n"
        "- Confirm general internet access from this environment.\n"
        "- Check firewall/proxy configuration.\n"
        "- If outbound internet is blocked, use an internal mirror or local repo cache."
    )
