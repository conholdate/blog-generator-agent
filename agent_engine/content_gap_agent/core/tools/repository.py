"""Repository cloning and content extraction."""

from pathlib import Path
from typing import List, Tuple

from git import Repo


class RepositoryAnalyzer:
    """Handles repository cloning and content extraction."""

    def __init__(self, cache_dir: str = "./repo_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def clone_or_update_repo(self, repo_url: str, branch: str = "master") -> Path:
        """Clone repository or update if it already exists."""
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        repo_path = self.cache_dir / repo_name

        print(f"Processing repository: {repo_name}")

        if repo_path.exists():
            print(f"  Updating existing repository...")
            repo = Repo(repo_path)
            origin = repo.remotes.origin
            origin.pull()
        else:
            print(f"  Cloning repository...")
            Repo.clone_from(repo_url, repo_path, branch=branch)

        print(f"  Repository ready at {repo_path}")
        return repo_path

    def extract_markdown_files(
        self, repo_path: Path, subpath: str = ""
    ) -> List[Tuple[Path, str]]:
        """Extract all markdown files from repository."""
        search_path = repo_path / subpath if subpath else repo_path
        md_files = []

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
