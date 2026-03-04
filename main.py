import src as _ # load logging conf

import asyncio

from src.utils import close_event, load_service
from src.sqlite import init_db

SERV_TASKS: list[asyncio.Task] = []

async def main():
    await init_db()
    service_objs = await load_service()

    for obj in service_objs:
        task = asyncio.create_task(obj.run())
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