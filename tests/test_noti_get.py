"""通知輪詢的過濾邏輯。

`should_process_parent` 是修掉「int vs str 永遠不相等」這個 bug 之後的判斷式，
這裡的測試會鎖住它的行為（含回歸保護）。
"""

from __future__ import annotations

from types import SimpleNamespace

from src.services.twitter import noti_get

WATCH_ID = "703877871256731678"


def test_should_process_parent_matches_int_user_id_to_string_config():
    parent = SimpleNamespace(user=SimpleNamespace(id=703877871256731678))

    assert (
        noti_get.should_process_parent(parent, only_watch_user=True, watch_user_id=WATCH_ID)
        is True
    )


def test_should_process_parent_rejects_different_user():
    parent = SimpleNamespace(user=SimpleNamespace(id=123))

    assert (
        noti_get.should_process_parent(parent, only_watch_user=True, watch_user_id=WATCH_ID)
        is False
    )


def test_should_process_parent_rejects_missing_user():
    parent = SimpleNamespace(user=None)

    assert (
        noti_get.should_process_parent(parent, only_watch_user=True, watch_user_id=WATCH_ID)
        is False
    )


def test_should_process_parent_ignores_user_when_not_watching():
    parent = SimpleNamespace(user=None)

    assert (
        noti_get.should_process_parent(parent, only_watch_user=False, watch_user_id=WATCH_ID)
        is True
    )


async def test_handle_notification_ignores_non_reply(monkeypatch):
    tweet = SimpleNamespace(id_str="1", inReplyToTweetId=None)

    async def fake_get_tweet(tweet_id):
        raise AssertionError("非回覆推文不應該去抓父推文")

    monkeypatch.setattr(noti_get, "get_tweet", fake_get_tweet)

    await noti_get._handle_notification(tweet)


async def test_handle_notification_skips_parent_from_other_user(monkeypatch):
    tweet = SimpleNamespace(id_str="1", inReplyToTweetId=999)
    parent = SimpleNamespace(id_str="999", user=SimpleNamespace(id=1))

    async def fake_get_tweet(tweet_id):
        return parent

    async def fake_is_passed(tweet_id):
        raise AssertionError("被過濾掉的父推文不應該查 passed 表")

    monkeypatch.setattr(noti_get, "get_tweet", fake_get_tweet)
    monkeypatch.setattr(noti_get, "should_process_parent", lambda parent, **kw: False)
    monkeypatch.setattr(noti_get, "is_passed_tweet_exists", fake_is_passed)

    await noti_get._handle_notification(tweet)


async def test_handle_notification_skips_already_passed(monkeypatch):
    tweet = SimpleNamespace(id_str="1", inReplyToTweetId=999)
    parent = SimpleNamespace(id_str="999", user=SimpleNamespace(id=1))

    async def fake_get_tweet(tweet_id):
        return parent

    async def fake_is_passed(tweet_id):
        return True

    monkeypatch.setattr(noti_get, "get_tweet", fake_get_tweet)
    monkeypatch.setattr(noti_get, "should_process_parent", lambda parent, **kw: True)
    monkeypatch.setattr(noti_get, "is_passed_tweet_exists", fake_is_passed)

    await noti_get._handle_notification(tweet)


async def test_handle_notification_queues_parent_and_downloads(monkeypatch):
    tweet = SimpleNamespace(id_str="1", inReplyToTweetId=999)
    parent = SimpleNamespace(id_str="999", user=SimpleNamespace(id=703877871256731678))

    class FakeQueue:
        def __init__(self):
            self.items = []

        async def put(self, item):
            self.items.append(item)

    queue = FakeQueue()
    downloaded = []

    class FakeDownloader:
        @staticmethod
        async def download_media(tweet=None, tweet_id=None):
            downloaded.append(tweet)
            return ["/tmp/x.jpg"]

    async def fake_get_tweet(tweet_id):
        return parent

    async def fake_is_passed(tweet_id):
        return False

    monkeypatch.setattr(noti_get, "get_tweet", fake_get_tweet)
    monkeypatch.setattr(noti_get, "should_process_parent", lambda parent, **kw: True)
    monkeypatch.setattr(noti_get, "is_passed_tweet_exists", fake_is_passed)
    monkeypatch.setattr(noti_get, "noti_queue", queue)
    monkeypatch.setattr(noti_get, "TweetMediaDownloader", FakeDownloader)

    await noti_get._handle_notification(tweet)

    assert queue.items == [parent]
    assert downloaded == [parent]
