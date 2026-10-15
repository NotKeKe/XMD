"""twscrape 模型與 API 的契約測試。

這些測試把「我們的程式碼依賴 twscrape 哪些欄位／方法」寫成斷言，
將來 twscrape 若改名或移除這些欄位，這裡會先壞掉，而不是等到 runtime 才炸。
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest
from twscrape import (
    API,
    Media,
    MediaAnimated,
    MediaPhoto,
    MediaVideo,
    MediaVideoVariant,
    Tweet,
    User,
)


def _field_names(cls) -> set[str]:
    return {f.name for f in dataclasses.fields(cls)}


@pytest.mark.parametrize(
    "cls, expected",
    [
        (Tweet, {"id", "id_str", "url", "rawContent", "user", "media", "inReplyToTweetId"}),
        (Media, {"photos", "videos", "animated"}),
        (MediaPhoto, {"url"}),
        (MediaVideo, {"thumbnailUrl", "variants", "duration"}),
        (MediaVideoVariant, {"contentType", "bitrate", "url"}),
        (MediaAnimated, {"thumbnailUrl", "videoUrl"}),
        (User, {"id", "username"}),
    ],
)
def test_model_exposes_expected_fields(cls, expected):
    missing = expected - _field_names(cls)
    assert not missing, f"{cls.__name__} 缺少欄位: {sorted(missing)}"


def test_api_exposes_expected_methods():
    # search() 是 async generator function（裡面有 yield），tweet_details() 是普通 coroutine
    assert inspect.isasyncgenfunction(API.search), "API.search 應該是 async generator function"
    assert inspect.iscoroutinefunction(API.tweet_details), "API.tweet_details 應該是 coroutine function"


def test_api_search_accepts_limit_keyword():
    params = inspect.signature(API.search).parameters
    assert "limit" in params
    assert "kv" in params


def test_api_constructor_accepts_pool_db_and_wait_options():
    params = inspect.signature(API.__init__).parameters
    for name in ("pool", "raise_when_no_account", "wait_timeout"):
        assert name in params, f"API.__init__ 缺少參數 {name}"


def test_api_pool_supports_cookie_login():
    from twscrape import AccountsPool

    assert inspect.iscoroutinefunction(AccountsPool.add_account_cookies)
    assert inspect.iscoroutinefunction(AccountsPool.accounts_info)

    params = inspect.signature(AccountsPool.add_account_cookies).parameters
    assert list(params)[:2] == ["self", "username"]


def test_models_are_exported_from_package_root():
    import twscrape

    for name in ("API", "AccountsPool", "NoAccountError", "HttpError", "gather", "Tweet", "Media"):
        assert hasattr(twscrape, name), f"twscrape 應該要匯出 {name}"
