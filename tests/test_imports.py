"""確保所有服務模組都能被 import。

這是為了堵住「移除傳遞依賴後某個模組 import 失敗」的回歸：
例如遷移時移除 tweety-ns 連帶移除了 aiofiles，而 discord 的 translator 仍在用。
只要有任一模組 import 失敗，這個測試就會立刻紅掉。
"""

from __future__ import annotations

import importlib

MODULES = [
    "src.queues",
    "src.sqlite",
    "src.services.twitter.utils",
    "src.services.twitter.noti_get",
    "src.services.twitter.main",
    "src.services.fastapi.api",
    "src.services.fastapi.app",
    "src.services.discord.cmds.command",
    "src.services.discord.cmds.channel",
    "src.services.discord.main",
]


def test_all_service_modules_import():
    errors = []
    for name in MODULES:
        try:
            importlib.import_module(name)
        except Exception as e:  # noqa: BLE001 - 我們要把每一個 import 失敗都報出來
            errors.append(f"{name}: {type(e).__name__}: {e}")

    assert not errors, "以下模組 import 失敗:\n" + "\n".join(errors)
