import logging
import asyncio
import random
from tweety.exceptions import TwitterError

from src.abc import ServicesABC
from .noti_get import get_noti_tweets
from .utils import client

logger = logging.getLogger(__name__)

class TwitterService(ServicesABC):
    async def run(self):
        while True:
            try:
                await get_noti_tweets()
            except TwitterError as e:
                logger.error(f'Failed to get tweets: {e}')
            except Exception as e:
                logger.error('Failed to get tweets', exc_info=True)

            await asyncio.sleep(60*5 + random.uniform(10, 20)) # 休息至少 5 mins

    async def stop(self):
        if client:
            await client.http.session.aclose()
            logger.info('Success close twitter client')