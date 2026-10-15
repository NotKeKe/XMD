"""測試環境前置準備。

`src/config.py` 在 import 時就會：
  - 若 `config.toml` 不存在，從 `config.toml.example` 生成後直接 `exit()`
  - 讀 `data/cookies.json`，讀不到就 raise
所以必須在任何 `src.*` import 之前把這些檔案準備好。

另外，`src/__init__.py` 會在 import 時設定 logging 並替換 stdout/stderr，
這是專案本身的既有行為；單元測試不會因此失敗，只是輸出會進 `logs/app.log`。
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _ensure_runtime_files() -> None:
    config_toml = REPO_ROOT / "config.toml"
    if not config_toml.exists():
        config_toml.write_text(
            (REPO_ROOT / "config.toml.example").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    cookies = REPO_ROOT / "data" / "cookies.json"
    if not cookies.exists():
        cookies.parent.mkdir(parents=True, exist_ok=True)
        # 只為了通過 config.py 的驗證；單元測試不會真的打 X API。
        cookies.write_text(
            json.dumps({"auth_token": "test-auth-token", "ct0": "test-ct0"}),
            encoding="utf-8",
        )


_ensure_runtime_files()
