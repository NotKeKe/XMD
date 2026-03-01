from tweety import TwitterAsync
from tweety.types import Media, Tweet, Community, User
from tweety.exceptions import UserProtected
from typing import cast, Optional, Any
import logging
from pathlib import Path
from urllib.parse import urlparse


from src.config import COOKIES, DATA_DIR, BASE_DIR, DOWNLOAD_DIR
from src.sqlite import insert_tweet_media, is_tweet_media_exists, insert_passed_tweet
from src.queues import download_queue

logger = logging.getLogger(__name__)

client: TwitterAsync | None = None

session_name = str((DATA_DIR / "twitter_session").relative_to(BASE_DIR))
session_path = Path(session_name + 'tw_session')

# deepwiki did this, to ignore UserProtected exception
class SafeUserDataTwitter(TwitterAsync):  
    def __init__(self, *args, **kwargs):  
        super().__init__(*args, **kwargs)  
        self._patch_community_methods()  
      
    def _patch_community_methods(self):  
        """修改 Community 類，實現嘗試抓取邏輯"""  
          
        def safe_get_admin(self):  
            try:  
                admin_data = self._community.get('admin_results')  
                if admin_data:  
                    return User(self._client, admin_data)  
                return None  
            except UserProtected:  
                # 用戶被暫停或其他保護狀態，返回 None  
                return None  
          
        def safe_get_creator(self):  
            try:  
                creator_data = self._community.get('creator_results')  
                if creator_data:  
                    return User(self._client, creator_data)  
                return None  
            except UserProtected:  
                # 用戶被暫停或其他保護狀態，返回 None  
                return None  
          
        # 應用修改  
        Community._get_admin = safe_get_admin  
        Community._get_creator = safe_get_creator  

async def _get_client():
    global client
    if not client:  
        client = SafeUserDataTwitter(session_name)  
          
        # 先嘗試載入現有會話  
        if client.session.logged_in:  
            try:  
                await client.connect()  
                logger.info(f'Logged in via session file')  
                return client  
            except Exception as e:  
                logger.warning(f'Session file login failed: {e}')  
          
        # 嘗試使用 cookies 登入  
        try:  
            await client.load_cookies(COOKIES)  
            logger.info(f'Logged in via cookies')  
        except Exception as e:  
            logger.error(f'Cookie login failed: {e}')  
            raise

    return client

def get_tweet_id(url: str) -> str:
    parsed_url = urlparse(url)
    path = parsed_url.path
    _id = path.split('/')[-1]
    if not _id.isdigit():
        raise ValueError('Invalid tweet url')
    return _id

class TweetMediaDownloader:
    @staticmethod
    async def get_info(tweet_id: str) -> tuple[dict[str, Any], Tweet]:
        app = await _get_client()
        
        tweet = await app.tweet_detail(tweet_id)

        urls: list[tuple[str, str]] = [] # (url, type)
        for m in tweet.media:  
            m = cast(Media, m)
            stream = await m.best_stream()
            if stream: urls.append((stream.direct_url, m.type))

        replied_info = {
            'text': tweet.text,
            'url': tweet.url,
            'id': tweet.id,
            'author': tweet.author.username if tweet.author else None,
            "media": {
                "len": len(tweet.media),
                "urls": urls
            }
        }
        return replied_info, tweet

    @staticmethod
    async def download_media_raw(tweet: Tweet, download_idx: int) -> Path:
        if download_idx < 0 or download_idx >= len(tweet.media):
            raise ValueError('Invalid download index')

        m = cast(Media, tweet.media[download_idx])
        media_type = m.type

        # 取得下載路徑
        match media_type:
            case "photo":
                download_path = DOWNLOAD_DIR / f"{tweet.id}_{m.id}.jpg"
            case "video" | "animated_gif":
                download_path = DOWNLOAD_DIR / f"{tweet.id}_{m.id}.mp4"
            case _:
                raise ValueError('Invalid media type')

        await m.download(filename=str(download_path.resolve()))
        return download_path

    @staticmethod
    async def download_media(tweet_id: Optional[str] = None, tweet: Optional[Tweet] = None) -> list[Path]:        
        if tweet is None:
            if not tweet_id:
                raise ValueError('tweet_id or tweet is required')

            app = await _get_client()
            tweet = await app.tweet_detail(tweet_id)

        tweet_id = str(tweet.id) # 這裡可能會有問題，因為 tweet.id 有可能是 Unknown

        downloaded_list = []
        for m in tweet.media:  
            m = cast(Media, m)
            media_type = m.type

            # 取得下載路徑
            match media_type:
                case "photo":
                    download_path = DOWNLOAD_DIR / f"{tweet_id}_{m.id}.jpg"
                case "video" | "animated_gif":
                    download_path = DOWNLOAD_DIR / f"{tweet_id}_{m.id}.mp4"
                case _:
                    continue

            # 檢查是否已下載，無則下載
            if await is_tweet_media_exists(tweet_id, m.id):
                logger.info(f'Tweet media {m.id} has been downloaded before, skip run download')
            else:
                await m.download(filename=str(download_path.resolve()))  
                logger.info(f'Downloaded media {m.id} to {download_path}')
                await insert_tweet_media(tweet_id, m.id, media_type, str(download_path.resolve()))
                await download_queue.put(download_path)

            downloaded_list.append(download_path)

        await insert_passed_tweet(tweet_id)
        
        return downloaded_list
        