from tweety import TwitterAsync
from tweety.types import Media, Tweet 
from typing import cast, Optional
import logging
from pathlib import Path

from src.config import COOKIES, DATA_DIR, BASE_DIR, DOWNLOAD_DIR
from src.sqlite import insert_tweet_media, is_tweet_media_exists, insert_passed_tweet
from src.queues import download_queue

logger = logging.getLogger(__name__)

client: TwitterAsync | None = None

session_name = str((DATA_DIR / "twitter_session").relative_to(BASE_DIR))
session_path = Path(session_name + 'tw_session')

async def _get_client():
    global client
    if not client:
        client = TwitterAsync(session_name)
        if not client.session.logged_in:
            try:
                await client.connect()
                logger.info('Logged in via session file')
            except Exception as e:
                pass

        # 如果還是沒登入 就載入 cookies
        if not client.session.logged_in:
            await client.load_cookies(COOKIES)
            logger.info('Logged in via cookies')

    return client

class TweetMediaDownloader:
    @staticmethod
    async def get_info(tweet_id: str) -> tuple[dict, Tweet]:
        app = await _get_client()
        
        tweet = await app.tweet_detail(tweet_id)

        replied_info = {
            'text': tweet.text,
            'url': tweet.url,
            'id': tweet.id,
            'author': tweet.author.username if tweet.author else None,
            "media": {
                "len": len(tweet.media),
                "data": [
                    d for d in tweet.media
                ]
            }
        }
        return replied_info, tweet

    @staticmethod
    async def download_media(tweet_id: Optional[str] = None, tweet: Optional[Tweet] = None) -> list[Path]:
        app = await _get_client()
        
        if tweet is None:
            if not tweet_id:
                raise ValueError('tweet_id or tweet is required')

            tweet = await app.tweet_detail(tweet_id)

        tweet_id = str(tweet.id) # 這裡可能會有問題，因為 tweet.id 有可能是 Unknown

        downloaded_list = []
        for m in tweet.media:  
            m = cast(Media, m)
            media_type = m.type

            if await is_tweet_media_exists(tweet_id, m.id):
                logger.info(f'Tweet media {m.id} has been downloaded before, skip')
                continue

            # download
            download_path = None
            if media_type == "photo":  
                download_path = DOWNLOAD_DIR / f"{m.id}.jpg"
            elif media_type in ("video", "animated_gif"):  
                best = await m.best_stream()  
                if best:  
                    download_path = DOWNLOAD_DIR / f"{m.id}.mp4"

            if download_path:
                await m.download(filename=str(download_path.resolve()))  
                logger.info(f'Downloaded media {m.id} to {download_path}')

                downloaded_list.append(download_path)
                await insert_tweet_media(tweet_id, m.id, media_type, str(download_path.resolve()))
                await download_queue.put(download_path)

        await insert_passed_tweet(tweet_id)
        
        return downloaded_list
        