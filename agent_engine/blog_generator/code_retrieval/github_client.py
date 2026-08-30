"""
Minimal GitHub REST client for the Example-Agent repos (org/agentic-*-examples).

Kept self-contained rather than reusing mcp-servers/product-reconciler's
GitHubClient: that client's get_raw_file() returns None for any file over
GitHub's 1MB contents-API inline-content limit, which index.json regularly
exceeds (e.g. aspose-cells' is 1.4MB) - a different fetch strategy
(raw.githubusercontent.com) is required for those, alongside the contents
API for directory listings and small files. The two clients also belong to
separately deployed tools (a GitHub Action vs. this app), so duplicating
~80 lines beats a cross-package import between them.
"""
import base64
from typing import Optional

import requests

API_BASE = "https://api.github.com"
RAW_BASE = "https://raw.githubusercontent.com"


class GitHubClient:
    def __init__(self, token: str = "", timeout: int = 15):
        self._session = requests.Session()
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._session.headers.update(headers)
        self.timeout = timeout
        self.last_error: Optional[str] = None

    def repo_exists(self, repo: str) -> bool:
        """repo is 'org/name'."""
        try:
            r = self._session.get(f"{API_BASE}/repos/{repo}", timeout=self.timeout)
        except requests.RequestException as e:
            self.last_error = f"network error checking {repo}: {e}"
            return False
        if r.status_code != 200:
            self.last_error = f"{r.status_code} checking {repo}"
            return False
        return True

    def get_tree(self, repo: str, ref: str = "main") -> Optional[list[str]]:
        """All file paths in `repo` at `ref`, in one call (git trees API, recursive).
        Preferred over per-category list_dir(): a category-name-only pre-filter
        misses files sitting in a genuinely-matching file but a generically-named
        folder (e.g. "manage-presentation-media-files" for an SVG-to-EMF example) -
        confirmed against real repos, up to ~2,300 files, well under GitHub's
        truncation limit for this call."""
        url = f"{API_BASE}/repos/{repo}/git/trees/{ref}"
        try:
            r = self._session.get(url, params={"recursive": "1"}, timeout=self.timeout)
        except requests.RequestException as e:
            self.last_error = f"network error fetching tree for {repo}: {e}"
            return None
        if r.status_code != 200:
            self.last_error = f"{r.status_code} fetching tree for {repo}"
            return None
        data = r.json()
        if data.get("truncated"):
            self.last_error = f"{repo}'s tree was truncated by GitHub - results are incomplete"
        return [item["path"] for item in data.get("tree", []) if item.get("type") == "blob"]

    def list_dir(self, repo: str, path: str, ref: str = "main") -> Optional[list[str]]:
        """Filenames directly under `path` in `repo`, or None if unreachable/not a directory."""
        url = f"{API_BASE}/repos/{repo}/contents/{path}"
        try:
            r = self._session.get(url, params={"ref": ref}, timeout=self.timeout)
        except requests.RequestException as e:
            self.last_error = f"network error listing {repo}/{path}: {e}"
            return None
        if r.status_code != 200:
            self.last_error = f"{r.status_code} listing {repo}/{path}"
            return None
        data = r.json()
        if not isinstance(data, list):
            self.last_error = f"{repo}/{path} is a file, not a directory"
            return None
        return [item["name"] for item in data]

    def get_small_file(self, repo: str, path: str, ref: str = "main") -> Optional[str]:
        """Contents-API fetch for files comfortably under the 1MB inline limit (e.g. a single .cs example)."""
        url = f"{API_BASE}/repos/{repo}/contents/{path}"
        try:
            r = self._session.get(url, params={"ref": ref}, timeout=self.timeout)
        except requests.RequestException as e:
            self.last_error = f"network error fetching {repo}/{path}: {e}"
            return None
        if r.status_code != 200:
            self.last_error = f"{r.status_code} fetching {repo}/{path}"
            return None
        data = r.json()
        if data.get("encoding") != "base64" or "content" not in data:
            self.last_error = f"{repo}/{path} has no inline content (likely over the 1MB limit)"
            return None
        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception as e:
            self.last_error = f"failed to decode {repo}/{path}: {e}"
            return None

    def get_raw_text(self, repo: str, path: str, ref: str = "main") -> Optional[str]:
        """Fetch via raw.githubusercontent.com - handles files of any size (e.g. index.json)."""
        url = f"{RAW_BASE}/{repo}/{ref}/{path}"
        try:
            r = self._session.get(url, timeout=self.timeout)
        except requests.RequestException as e:
            self.last_error = f"network error fetching raw {repo}/{path}: {e}"
            return None
        if r.status_code != 200:
            self.last_error = f"{r.status_code} fetching raw {repo}/{path}"
            return None
        return r.text
