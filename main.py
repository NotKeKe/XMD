import src as _ # load logging conf

import asyncio

from src.services.discord.main import DiscordService
from src.services.fastapi.main import FastAPIService
from src.services.twitter.main import TwitterService

from src.utils import close_event

SERV_TASKS: list[asyncio.Task] = []

async def main():
    services = [
        # DiscordService,
        FastAPIService,
        TwitterService,
    ]

    service_objs = []

    for serv in services:
        obj = serv()
        task = asyncio.create_task(obj.run())

        service_objs.append(obj)
        SERV_TASKS.append(task)

    try:
        await asyncio.gather(*SERV_TASKS)
    except asyncio.CancelledError:
        pass
    finally:
        for serv in service_objs:
            try:
                await serv.stop()
            except Exception as e:
                print(f'Failed to stop service {serv.__class__.__name__}: {e}')
        await close_event()
            
        for task in SERV_TASKS:
            task.cancel()

        await asyncio.gather(*SERV_TASKS, return_exceptions=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Closing program...')