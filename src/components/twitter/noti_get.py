from tweety.filters import SearchFilters
from tweety.types import Tweet
from tweety.exceptions import RateLimitReached
from typing import cast
import logging
import asyncio
import random

from src.config import X_USER_ID, X_BOT_ID, ONLY_WATCH_USER
from src.sqlite import is_passed_tweet_exists
from src.queues import noti_queue

from .utils import _get_client, TweetMediaDownloader

logger = logging.getLogger(__name__)

async def get_noti_tweets():
    app = await _get_client()
    
    # search
    try:
        for attempt in range(3):  
            try:  
                results = await app.search(X_BOT_ID, filter_=SearchFilters.Latest, wait_time=10)  
            except RateLimitReached as e:  
                if attempt < 3 - 1:  
                    await asyncio.sleep((e.retry_after or 120) + random.randint(10, 20))
                else:  
                    raise

    except Exception as e:
        logger.error('Failed to search tweets')
        raise

    for tweet in results.results:  
        tweet = cast(Tweet, tweet)
        if not (hasattr(tweet, "is_reply") and tweet.is_reply):  
            continue  
  
        parent = await tweet.get_reply_to()  
        if not parent:  
            continue  

        if ONLY_WATCH_USER:
            if parent.author and parent.author.id != X_USER_ID:
                logger.info(f'Tweet {parent.id} is not from user {X_USER_ID}, skip')
                continue

        if await is_passed_tweet_exists(parent.id):
            logger.info(f'Tweet {parent.id} has been seen before, skip')
            continue

        parent = cast(Tweet, parent)
        # 先將推文放入 noti_queue
        await noti_queue.put(parent)

        results = await TweetMediaDownloader.download_media(tweet_id=parent.id)
        logger.info(f'Downloaded {len(results)} media files from tweet {parent.id}')
  


