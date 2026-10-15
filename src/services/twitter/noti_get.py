import logging

from twscrape import Tweet, gather

from src.config import X_BOT_ID, X_ONLY_WATCH_USER, X_SEARCH_LIMIT, X_USER_ID
from src.queues import noti_queue
from src.sqlite import is_passed_tweet_exists

from .utils import TweetMediaDownloader, get_api, get_tweet

logger = logging.getLogger(__name__)


def should_process_parent(
    parent: Tweet,
    *,
    only_watch_user: bool = X_ONLY_WATCH_USER,
    watch_user_id: str = X_USER_ID,
) -> bool:
    """檢查父推文是不是我們要處理的對象。

    `watch_user_id` 兩邊都轉成字串再比：config 讀進來是 str，而 twscrape 的 `User.id` 是 int。
    （遷移前是 `parent.author.id != X_USER_ID`，int 與 str 永遠不相等，
    導致 `x_only_you = true` 時所有通知都被跳過。）
    """
    if not only_watch_user:
        return True

    if not parent.user:
        return False

    return str(parent.user.id) == str(watch_user_id)


async def _handle_notification(tweet: Tweet) -> None:
    # twscrape 沒有 is_reply，也沒有 tweet.get_reply_to()，改用 inReplyToTweetId 自己抓父推文。
    if tweet.inReplyToTweetId is None:
        return

    parent = await get_tweet(tweet.inReplyToTweetId)

    if not should_process_parent(parent):
        logger.info(f'Tweet {parent.id_str} is not from user {X_USER_ID}, skip')
        return

    if await is_passed_tweet_exists(parent.id_str):
        logger.info(f'Tweet {parent.id_str} has been seen before, skip')
        return

    # 先將推文放入 noti_queue
    await noti_queue.put(parent)

    paths = await TweetMediaDownloader.download_media(tweet=parent)
    logger.info(f'Downloaded {len(paths)} media files from tweet {parent.id_str}')


async def get_noti_tweets():
    client = await get_api()

    # twscrape 內部會自己做 rate-limit 鎖定與帳號輪替，所以不需要外層重試迴圈。
    # limit 一定要給，否則 twscrape 會無限翻頁。
    tweets = await gather(client.search(X_BOT_ID, limit=X_SEARCH_LIMIT))

    for tweet in tweets:
        # 單一推文的失敗（例如父推文已被刪除）不應該中斷整輪輪詢。
        try:
            await _handle_notification(tweet)
        except Exception:
            logger.exception(f'Failed to handle notification from tweet {tweet.id_str}')
