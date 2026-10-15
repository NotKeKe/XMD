import asyncio
import logging
import random

from twscrape import HttpError, NoAccountError

from src.abc import ServicesABC

from .noti_get import get_noti_tweets

logger = logging.getLogger(__name__)

class TwitterService(ServicesABC):
    async def run(self):
        while True:
            try:
                await get_noti_tweets()
            except NoAccountError as e:
                # twscrape 的帳號池沒有可用帳號（cookies 失效、被限流鎖住、或被判定 banned）
                logger.error(f'No usable X account in the twscrape pool, wait for the next round: {e}')
            except HttpError as e:
                logger.error(f'Failed to get tweets: {e}')
            except Exception:
                logger.exception('Failed to get tweets')

            await asyncio.sleep(60*5 + random.uniform(10, 20)) # 休息至少 5 mins

    async def stop(self):
        # twscrape 沒有長駐的 http session（每個 queue client 用 async with 自行開關），
        # 帳號池也是即開即關的 SQLite 連線，所以這裡沒有需要釋放的資源。
        logger.info('Twitter service stopped')
