"""twscrape 客戶端封裝與媒體下載層。

這個模組是整個專案唯一直接接觸 X API 的地方：

- `get_api()` 建立 twscrape 的 `API`（帳號池放在 `data/accounts.db`），並把
  `data/cookies.json` 的 cookie 灌進帳號池。
- `get_tweet()` / `get_media_items()` 把 twscrape 的模型轉成本專案要的形狀。
- `TweetMediaDownloader` 負責挑出可下載的 URL 並真的下載（twscrape 沒有內建下載）。

對外介面（`get_tweet_id`、`TweetMediaDownloader.get_info` / `download_media_raw` / `download_media`）
的名稱、簽章與回傳形狀都刻意與遷移前（tweety 版本）保持一致，
所以 FastAPI 與 Discord 端不需要跟著改。
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from twscrape import API, MediaAnimated, MediaPhoto, MediaVideo, MediaVideoVariant, Tweet

from src.config import (
    ACCOUNTS_DB,
    COOKIES,
    DOWNLOAD_DIR,
    X_ACCOUNT_NAME,
    X_WAIT_TIMEOUT,
)
from src.queues import download_queue
from src.sqlite import insert_passed_tweet, insert_tweet_media, is_tweet_media_exists

logger = logging.getLogger(__name__)

# 媒體種類字串：刻意沿用遷移前 tweety 的值域，
# 前端 (download.ts / overview.ts 的篩選器) 與資料庫的 media_type 都依賴這組字串。
PHOTO = "photo"
VIDEO = "video"
ANIMATED_GIF = "animated_gif"

# 下載媒體時用的 User-Agent，避免 CDN 直接擋掉預設的 python-httpx。
DOWNLOAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
}
DOWNLOAD_TIMEOUT = 60.0
DOWNLOAD_CHUNK_SIZE = 64 * 1024

api: API | None = None


def _bridge_twscrape_logging() -> None:
    """把 twscrape 的 loguru 日誌轉送到本專案的 stdlib logging。

    twscrape 在 import 時會 `loguru.logger.remove()` 然後加一個 stderr sink，
    那會繞過本專案在 `src/__init__.py` 設定的 handler，日誌就不會進 `logs/app.log`。
    這裡改成接到 `logging.getLogger("twscrape")`，讓日誌跟其他服務一樣落地。

    這是盡力而為的橋接：loguru 是 twscrape 的依賴，但若它不在就沿用 twscrape 的預設行為。
    """
    try:
        from loguru import logger as loguru_logger
    except ImportError:  # pragma: no cover - 正常情況 twscrape 會帶著 loguru
        return

    levels = {
        "TRACE": logging.DEBUG,
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "SUCCESS": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    target = logging.getLogger("twscrape")

    def sink(message: Any) -> None:
        record = message.record
        # 用 record["message"] 而不是 str(message)，避免把 loguru 已格式化的整行
        # （含它自己的時間戳/等級）再包進 stdlib logging 造成重複。
        target.log(levels.get(record["level"].name, logging.INFO), record["message"].rstrip())

    loguru_logger.remove()
    loguru_logger.add(sink, level=os.getenv("TWS_LOG_LEVEL", "INFO"))


_bridge_twscrape_logging()


async def _load_cookies_into_pool(client: API) -> None:
    """把 `data/cookies.json` 的 cookie 寫進 twscrape 帳號池。

    `add_account_cookies` 是 UPSERT：會換掉 cookies、把帳號設回 active、
    清掉 error_msg。這與遷移前「每次啟動都用 cookies.json 重新登入」的行為一致，
    也讓「重啟即復原」成立（帳號被鎖或被標記 inactive 時，重啟會把它救回來）。
    """
    await client.pool.add_account_cookies(X_ACCOUNT_NAME, json.dumps(COOKIES))

    accounts = await client.pool.accounts_info()
    active = [account["username"] for account in accounts if account["active"]]
    if not active:
        logger.error(
            "twscrape 帳號池 (%s) 裡沒有可用的帳號，請確認 cookies 檔的 auth_token / ct0 是否有效。",
            ACCOUNTS_DB,
        )
    else:
        logger.info("twscrape 帳號池就緒: %s", active)


async def get_api() -> API:
    """取得（並在第一次呼叫時初始化）twscrape 的 API 實例。"""
    global api
    if api is None:
        api = API(
            str(ACCOUNTS_DB),
            # 沒有可用帳號時丟 NoAccountError，而不是無限期等待
            raise_when_no_account=True,
            # 所有帳號都被限流鎖住時最多等這麼久
            wait_timeout=X_WAIT_TIMEOUT,
        )
        await _load_cookies_into_pool(api)
    return api


async def get_tweet(tweet_id: str | int) -> Tweet:
    """依 tweet id 取得推文，取不到就 raise ValueError。

    twscrape 的 `tweet_details()` 內部用 `Tweet.id`（int）跟傳進去的值比對，
    傳字串進去會讓 `parse_tweet()` 永遠對不上而回傳 None，
    所以這裡（也只有在這裡）統一轉成 int。
    """
    client = await get_api()
    twid = int(tweet_id)
    tweet = await client.tweet_details(twid)
    if tweet is None:
        raise ValueError(f"Tweet {twid} not found (deleted, protected, or unavailable)")
    return tweet


def get_tweet_id(url: str) -> str:
    parsed_url = urlparse(url)
    path = parsed_url.path
    _id = path.split('/')[-1]
    if not _id.isdigit():
        raise ValueError('Invalid tweet url')
    return _id


@dataclass(frozen=True)
class MediaItem:
    """單一可下載的媒體。

    twscrape 的 `Media` 沒有 id 欄位，所以 `media_id` 由媒體 URL 推導
    （見 `_basename_key`），用途是檔名 `{tweet_id}_{media_id}.{ext}`
    與 `tweets_media` 表的 `UNIQUE(tweet_id, media_id)`。
    """

    type: str  # PHOTO / VIDEO / ANIMATED_GIF
    media_id: str
    direct_url: str  # 實際下載用的 URL
    thumbnail: str


def _basename_key(url: str | None) -> str | None:
    """從媒體 URL 取檔名主體，例如 `.../media/GXy1.jpg?name=small` -> `GXy1`。"""
    if not url:
        return None

    name = Path(urlparse(url).path).name
    if not name:
        return None

    stem = name.rsplit(".", 1)[0] if "." in name else name
    return stem or None


def _photo_direct_url(url: str) -> str:
    """照片取原始尺寸：保留原本的 query 參數，只把 name 換成 orig。"""
    base, _, query = url.partition("?")
    params = [p for p in query.split("&") if p and not p.startswith("name=")]
    params.append("name=orig")
    return f"{base}?{'&'.join(params)}"


def _best_video_url(video: MediaVideo) -> str | None:
    """挑 bitrate 最高的 mp4 變體；沒有 mp4 就退回 bitrate 最高的變體。"""
    variants: list[MediaVideoVariant] = [v for v in (video.variants or []) if v.url]
    if not variants:
        return None

    mp4 = [v for v in variants if v.contentType == "video/mp4"]
    if mp4:
        return max(mp4, key=lambda v: v.bitrate).url

    logger.warning("影片沒有 mp4 變體，改用 bitrate 最高的變體（可能是 HLS 清單）")
    return max(variants, key=lambda v: v.bitrate).url


def get_media_items(tweet: Tweet) -> list[MediaItem]:
    """把 twscrape 的 `Media` 攤平成可下載的清單。

    順序固定為 photos -> videos -> animated。twscrape 的模型把三種媒體分成三個 list，
    原始的交錯順序已經不見了，所以 `indices`（前端 data-index、API 的 indices）的語意
    就是這個串接後的索引；`get_info()` 回傳的順序與這裡完全同源。
    """
    media = getattr(tweet, "media", None)
    if media is None:
        return []

    items: list[MediaItem] = []

    for index, photo in enumerate(media.photos or []):
        items.append(
            MediaItem(
                type=PHOTO,
                media_id=_basename_key(photo.url) or f"{PHOTO}{index}",
                direct_url=_photo_direct_url(photo.url),
                thumbnail=photo.url,
            )
        )

    for index, video in enumerate(media.videos or []):
        direct_url = _best_video_url(video)
        if direct_url is None:
            logger.warning("Tweet %s 的第 %d 個影片沒有可下載的變體，跳過", tweet.id_str, index)
            continue

        items.append(
            MediaItem(
                type=VIDEO,
                media_id=_basename_key(video.thumbnailUrl) or f"{VIDEO}{index}",
                direct_url=direct_url,
                thumbnail=video.thumbnailUrl,
            )
        )

    for index, animated in enumerate(media.animated or []):
        items.append(
            MediaItem(
                type=ANIMATED_GIF,
                media_id=_basename_key(animated.thumbnailUrl) or f"{ANIMATED_GIF}{index}",
                direct_url=animated.videoUrl,
                thumbnail=animated.thumbnailUrl,
            )
        )

    return items


def _media_filename(tweet_id: str, item: MediaItem) -> str:
    extension = "jpg" if item.type == PHOTO else "mp4"
    return f"{tweet_id}_{item.media_id}.{extension}"


async def _download_file(url: str, dest: Path) -> None:
    """串流下載單一檔案（twscrape 沒有內建下載）。"""
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=DOWNLOAD_TIMEOUT,
        headers=DOWNLOAD_HEADERS,
    ) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(dest, "wb") as f:
                async for chunk in response.aiter_bytes(DOWNLOAD_CHUNK_SIZE):
                    f.write(chunk)


class TweetMediaDownloader:
    @staticmethod
    async def get_info(tweet_id: str) -> tuple[dict[str, Any], Tweet]:
        """回傳 `(info, tweet)`，`info` 的形狀是前端 `MediaInfo` 的契約，不可隨意更動。"""
        try:
            tweet = await get_tweet(tweet_id)
        except Exception as e:
            logger.error(f'Failed to get tweet info {tweet_id}: {e}')
            raise

        items = get_media_items(tweet)
        urls = [
            {"url": item.direct_url, "thumbnail": item.thumbnail, "type": item.type}
            for item in items
        ]

        replied_info = {
            'text': tweet.rawContent,
            'url': tweet.url,
            'id': str(tweet.id),
            'author': tweet.user.username if tweet.user else None,
            "media": {
                "len": len(items),
                "urls": urls
            }
        }
        return replied_info, tweet

    @staticmethod
    def get_direct_url(tweet: Tweet, download_idx: int) -> str:
        """取得第 `download_idx` 個媒體的直接連結（Discord 檔案過大時的替代方案）。"""
        items = get_media_items(tweet)
        if download_idx < 0 or download_idx >= len(items):
            raise ValueError('Invalid download index')
        return items[download_idx].direct_url

    @staticmethod
    async def download_media_raw(tweet: Tweet, download_idx: int) -> Path:
        items = get_media_items(tweet)
        if download_idx < 0 or download_idx >= len(items):
            raise ValueError('Invalid download index')

        item = items[download_idx]
        download_path = DOWNLOAD_DIR / _media_filename(str(tweet.id), item)
        await _download_file(item.direct_url, download_path)
        return download_path

    @staticmethod
    async def download_media(tweet_id: Optional[str] = None, tweet: Optional[Tweet] = None) -> list[Path]:
        if tweet is None:
            if not tweet_id:
                raise ValueError('tweet_id or tweet is required')

            tweet = await get_tweet(tweet_id)

        tweet_id = str(tweet.id)

        downloaded_list: list[Path] = []
        for item in get_media_items(tweet):
            download_path = DOWNLOAD_DIR / _media_filename(tweet_id, item)

            # 檢查是否已下載，無則下載
            if await is_tweet_media_exists(tweet_id, item.media_id):
                logger.info(f'Tweet media {item.media_id} has been downloaded before, skip run download')
            else:
                await _download_file(item.direct_url, download_path)
                logger.info(f'Downloaded media {item.media_id} to {download_path}')
                await insert_tweet_media(tweet_id, item.media_id, item.type, str(download_path.resolve()))
                await download_queue.put(download_path)

            downloaded_list.append(download_path)

        await insert_passed_tweet(tweet_id)

        return downloaded_list
