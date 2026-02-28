from asyncio import Queue
from tweety.types import Tweet

download_queue = Queue() # 下載了推文
noti_queue: Queue[Tweet] = Queue() # 接收到推文tag通知