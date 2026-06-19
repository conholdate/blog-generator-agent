from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import make_repo


@pytest.fixture
def sample_hugo_repo(tmp_path: Path) -> Path:
    return make_repo(tmp_path)
