"""`get_info()` 的前端契約與 `download_media()` 的錄庫／去重行為。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.services.twitter import utils


def make_tweet():
    return SimpleNamespace(
        id=2027639682520256545,
        id_str="2027639682520256545",
        url="https://x.com/user/status/2027639682520256545",
        rawContent="hello world",
        user=SimpleNamespace(id=703877871256731678, username="someone"),
        media=SimpleNamespace(
            photos=[SimpleNamespace(url="https://pbs.twimg.com/media/GXy1.jpg")],
            videos=[],
            animated=[],
        ),
    )


async def test_get_info_matches_frontend_contract(monkeypatch):
    async def fake_get_tweet(tweet_id):
        return make_tweet()

    monkeypatch.setattr(utils, "get_tweet", fake_get_tweet)

    info, tweet = await utils.TweetMediaDownloader.get_info("2027639682520256545")

    assert set(info) == {"text", "url", "id", "author", "media"}
    assert info["text"] == "hello world"
    assert info["url"] == "https://x.com/user/status/2027639682520256545"
    assert info["id"] == "2027639682520256545"
    assert info["author"] == "someone"
    assert set(info["media"]) == {"len", "urls"}
    assert info["media"]["len"] == 1
    assert info["media"]["urls"][0] == {
        "url": "https://pbs.twimg.com/media/GXy1.jpg?name=orig",
        "thumbnail": "https://pbs.twimg.com/media/GXy1.jpg",
        "type": "photo",
    }
    assert tweet is not None


async def test_get_info_author_is_none_without_user(monkeypatch):
    tweet = make_tweet()
    tweet.user = None

    async def fake_get_tweet(tweet_id):
        return tweet

    monkeypatch.setattr(utils, "get_tweet", fake_get_tweet)

    info, _ = await utils.TweetMediaDownloader.get_info("1")
    assert info["author"] is None


def test_get_direct_url_index_bounds():
    tweet = make_tweet()

    assert (
        utils.TweetMediaDownloader.get_direct_url(tweet, 0)
        == "https://pbs.twimg.com/media/GXy1.jpg?name=orig"
    )
    with pytest.raises(ValueError):
        utils.TweetMediaDownloader.get_direct_url(tweet, 1)
    with pytest.raises(ValueError):
        utils.TweetMediaDownloader.get_direct_url(tweet, -1)


async def test_download_media_skips_existing_and_never_downloads(monkeypatch, tmp_path):
    tweet = make_tweet()

    recorded = []
    downloaded = []

    class FakeQueue:
        def __init__(self):
            self.items = []

        async def put(self, item):
            self.items.append(item)

    queue = FakeQueue()

    async def fake_is_exists(tweet_id, media_id):
        return True

    async def fake_insert_media(*args):
        recorded.append(args)

    async def fake_insert_passed(tweet_id):
        recorded.append(("passed", tweet_id))

    async def fake_download(url, dest):
        downloaded.append(url)

    monkeypatch.setattr(utils, "DOWNLOAD_DIR", tmp_path)
    monkeypatch.setattr(utils, "is_tweet_media_exists", fake_is_exists)
    monkeypatch.setattr(utils, "insert_tweet_media", fake_insert_media)
    monkeypatch.setattr(utils, "insert_passed_tweet", fake_insert_passed)
    monkeypatch.setattr(utils, "_download_file", fake_download)
    monkeypatch.setattr(utils, "download_queue", queue)

    paths = await utils.TweetMediaDownloader.download_media(tweet=tweet)

    assert downloaded == []
    assert queue.items == []
    assert recorded == [("passed", "2027639682520256545")]
    assert paths == [tmp_path / "2027639682520256545_GXy1.jpg"]


async def test_download_media_downloads_and_records_new_media(monkeypatch, tmp_path):
    tweet = make_tweet()

    recorded = []
    downloaded = []

    class FakeQueue:
        def __init__(self):
            self.items = []

        async def put(self, item):
            self.items.append(item)

    queue = FakeQueue()

    async def fake_is_exists(tweet_id, media_id):
        return False

    async def fake_insert_media(*args):
        recorded.append(args)

    async def fake_insert_passed(tweet_id):
        recorded.append(("passed", tweet_id))

    async def fake_download(url, dest):
        downloaded.append(url)

    monkeypatch.setattr(utils, "DOWNLOAD_DIR", tmp_path)
    monkeypatch.setattr(utils, "is_tweet_media_exists", fake_is_exists)
    monkeypatch.setattr(utils, "insert_tweet_media", fake_insert_media)
    monkeypatch.setattr(utils, "insert_passed_tweet", fake_insert_passed)
    monkeypatch.setattr(utils, "_download_file", fake_download)
    monkeypatch.setattr(utils, "download_queue", queue)

    paths = await utils.TweetMediaDownloader.download_media(tweet=tweet)

    assert downloaded == ["https://pbs.twimg.com/media/GXy1.jpg?name=orig"]
    assert queue.items == [tmp_path / "2027639682520256545_GXy1.jpg"]
    assert recorded == [
        (
            "2027639682520256545",
            "GXy1",
            "photo",
            str((tmp_path / "2027639682520256545_GXy1.jpg").resolve()),
        ),
        ("passed", "2027639682520256545"),
    ]
    assert paths == [tmp_path / "2027639682520256545_GXy1.jpg"]
