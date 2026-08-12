"""
Thin GitHub REST API client for reading repo contents.

Uses `requests` directly (not the `gh` CLI) so this works unattended on a
runner where `gh` may not be authenticated, as long as a token with repo
read access is provided via GITHUB_TOKEN / REPO_PAT.
"""
import base64
import requests

API_BASE = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str, timeout: int = 10):
        if not token:
            raise ValueError("GitHubClient requires a token with access to the target repos")
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        self.timeout = timeout
        self.last_error: str | None = None  # human-readable reason for the most recent failed call

    def list_dir(self, repo: str, path: str) -> list[str] | None:
        """Names of entries under `path` in `repo`, or None if the path doesn't exist."""
        url = f"{API_BASE}/repos/{repo}/contents/{path}"
        try:
            r = self._session.get(url, timeout=self.timeout)
        except requests.RequestException as e:
            self.last_error = f"network error calling {url}: {e}"
            return None
        if r.status_code != 200:
            self.last_error = self._describe_failure(repo, r)
            return None
        data = r.json()
        if not isinstance(data, list):
            self.last_error = f"{url} exists but is a file, not a directory"
            return None
        return [item["name"] for item in data]

    def _describe_failure(self, repo: str, r: requests.Response) -> str:
        if r.status_code == 404:
            return (
                f"404 from {r.url} — either the path doesn't exist, or (far more likely for a "
                f"private repo like {repo}) the token doesn't have read access to it. GitHub "
                f"returns 404, not 403, for a private repo the token can't see."
            )
        if r.status_code == 401:
            return f"401 from {r.url} — the token is missing, expired, or malformed."
        if r.status_code == 403:
            return f"403 from {r.url} — token is valid but explicitly forbidden (rate limit or SSO enforcement?)."
        return f"{r.status_code} from {r.url}: {r.text[:200]}"

    def get_raw_file(self, repo: str, path: str) -> str | None:
        """Raw text content of a file in `repo`, or None if missing/unreadable."""
        url = f"{API_BASE}/repos/{repo}/contents/{path}"
        try:
            r = self._session.get(url, timeout=self.timeout)
        except requests.RequestException as e:
            self.last_error = f"network error calling {url}: {e}"
            return None
        if r.status_code != 200:
            self.last_error = self._describe_failure(repo, r)
            return None
        data = r.json()
        if data.get("encoding") != "base64" or "content" not in data:
            return None
        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            return None
