"""確認遷移沒有留下 tweety 的痕跡，且 config 暴露了 twscrape 需要的設定。"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TWEETY_IMPORT = re.compile(r"^\s*(?:from|import)\s+tweety(?:_ns)?\b", re.MULTILINE)


def test_no_tweety_imports_remain_in_python():
    offenders = []
    for root in ("src", "test"):
        for path in (REPO_ROOT / root).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if TWEETY_IMPORT.search(text):
                offenders.append(str(path.relative_to(REPO_ROOT)))

    assert not offenders, f"仍殘留 tweety import: {offenders}"


def test_dependencies_swapped():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")

    assert "twscrape" in pyproject
    assert "tweety" not in pyproject.lower()
    assert "twscrape" in requirements
    assert "tweety" not in requirements.lower()


def test_config_exposes_twscrape_settings():
    from src import config

    assert config.ACCOUNTS_DB.name == "accounts.db"
    assert config.X_ACCOUNT_NAME
    assert config.X_SEARCH_LIMIT > 0
    assert config.X_WAIT_TIMEOUT > 0
    assert config.COOKIES.get("auth_token")
    assert config.COOKIES.get("ct0")
