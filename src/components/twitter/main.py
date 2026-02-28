import logging
import asyncio
import random

from src.abc import ServicesABC
from .noti_get import get_noti_tweets
from .utils import client

logger = logging.getLogger(__name__)

class TwitterService(ServicesABC):
    async def run(self):
        while True:
            try:
                await get_noti_tweets()
            except Exception as e:
                logger.error('Failed to get tweets', exc_info=True)

            await asyncio.sleep(random.uniform(110, 130))

    async def stop(self):
        if client:
            await client.http.session.aclose()
            logger.info('Success close twitter client')