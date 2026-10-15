"""媒體攤平與檔名推導的單元測試（不使用網路、不碰 X API）。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from src.services.twitter.utils import (
    ANIMATED_GIF,
    PHOTO,
    VIDEO,
    _media_filename,
    get_media_items,
)


def make_tweet(media) -> Any:
    return SimpleNamespace(id=123, id_str="123", media=media)


def make_video(thumbnail="https://pbs.twimg.com/amplify_video_thumb/9/img/thumbA.jpg", variants=()):
    return SimpleNamespace(thumbnailUrl=thumbnail, variants=list(variants))


def make_variant(url, bitrate, content_type="video/mp4"):
    return SimpleNamespace(url=url, bitrate=bitrate, contentType=content_type)


def test_no_media_returns_empty_list():
    assert get_media_items(make_tweet(None)) == []
    assert get_media_items(make_tweet(SimpleNamespace(photos=[], videos=[], animated=[]))) == []


def test_photo_uses_original_size_url_and_url_basename():
    tweet = make_tweet(
        SimpleNamespace(
            photos=[SimpleNamespace(url="https://pbs.twimg.com/media/GXy1.jpg")],
            videos=[],
            animated=[],
        )
    )

    items = get_media_items(tweet)

    assert len(items) == 1
    item = items[0]
    assert item.type == PHOTO
    assert item.media_id == "GXy1"
    assert item.direct_url == "https://pbs.twimg.com/media/GXy1.jpg?name=orig"
    assert item.thumbnail == "https://pbs.twimg.com/media/GXy1.jpg"


def test_photo_preserves_format_param_when_forcing_orig():
    tweet = make_tweet(
        SimpleNamespace(
            photos=[SimpleNamespace(url="https://pbs.twimg.com/media/GXy1?format=jpg&name=small")],
            videos=[],
            animated=[],
        )
    )

    item = get_media_items(tweet)[0]

    assert item.direct_url == "https://pbs.twimg.com/media/GXy1?format=jpg&name=orig"
    assert item.media_id == "GXy1"


def test_video_picks_highest_bitrate_mp4():
    tweet = make_tweet(
        SimpleNamespace(
            photos=[],
            videos=[
                make_video(
                    variants=[
                        make_variant("https://video.twimg.com/a.mp4", 256000),
                        make_variant("https://video.twimg.com/b.mp4", 2176000),
                        make_variant("https://video.twimg.com/c.mp4", 832000),
                    ]
                )
            ],
            animated=[],
        )
    )

    item = get_media_items(tweet)[0]

    assert item.type == VIDEO
    assert item.direct_url == "https://video.twimg.com/b.mp4"
    assert item.media_id == "thumbA"
    assert item.thumbnail == "https://pbs.twimg.com/amplify_video_thumb/9/img/thumbA.jpg"


def test_video_prefers_mp4_over_higher_bitrate_non_mp4():
    tweet = make_tweet(
        SimpleNamespace(
            photos=[],
            videos=[
                make_video(
                    variants=[
                        make_variant(
                            "https://video.twimg.com/hls.m3u8",
                            9999999,
                            content_type="application/x-mpegURL",
                        ),
                        make_variant("https://video.twimg.com/a.mp4", 256000),
                    ]
                )
            ],
            animated=[],
        )
    )

    assert get_media_items(tweet)[0].direct_url == "https://video.twimg.com/a.mp4"


def test_video_without_variants_is_skipped():
    tweet = make_tweet(
        SimpleNamespace(photos=[], videos=[make_video(variants=[])], animated=[])
    )

    assert get_media_items(tweet) == []


def test_animated_gif_uses_video_url():
    tweet = make_tweet(
        SimpleNamespace(
            photos=[],
            videos=[],
            animated=[
                SimpleNamespace(
                    thumbnailUrl="https://pbs.twimg.com/tweet_video_thumb/GXy9.jpg",
                    videoUrl="https://video.twimg.com/tweet_video/GXy9.mp4",
                )
            ],
        )
    )

    item = get_media_items(tweet)[0]

    assert item.type == ANIMATED_GIF
    assert item.media_id == "GXy9"
    assert item.direct_url == "https://video.twimg.com/tweet_video/GXy9.mp4"
    assert item.thumbnail.endswith("GXy9.jpg")


def test_media_order_is_photos_then_videos_then_animated():
    """indices / data-index 的語意依賴這個順序，改動會破壞前端的對應。"""
    tweet = make_tweet(
        SimpleNamespace(
            photos=[SimpleNamespace(url="https://pbs.twimg.com/media/P1.jpg")],
            videos=[make_video(variants=[make_variant("https://video.twimg.com/v.mp4", 1)])],
            animated=[
                SimpleNamespace(
                    thumbnailUrl="https://pbs.twimg.com/tweet_video_thumb/A1.jpg",
                    videoUrl="https://video.twimg.com/a1.mp4",
                )
            ],
        )
    )

    assert [item.type for item in get_media_items(tweet)] == [PHOTO, VIDEO, ANIMATED_GIF]


def test_media_filename_extensions():
    tweet = make_tweet(
        SimpleNamespace(
            photos=[SimpleNamespace(url="https://pbs.twimg.com/media/P1.png")],
            videos=[],
            animated=[
                SimpleNamespace(
                    thumbnailUrl="https://pbs.twimg.com/tweet_video_thumb/A1.jpg",
                    videoUrl="https://video.twimg.com/a1.mp4",
                )
            ],
        )
    )

    items = get_media_items(tweet)
    assert _media_filename("555", items[0]) == "555_P1.jpg"
    assert _media_filename("555", items[1]) == "555_A1.mp4"
