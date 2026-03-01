import aiosqlite
from typing import Optional
from .config import DB_PATH

db_conn = None
_db_init = False

async def get_db():
    global db_conn
    if db_conn is None:
        db_conn = await aiosqlite.connect(DB_PATH)
        await db_conn.execute("PRAGMA journal_mode=WAL")
        await db_conn.execute("PRAGMA synchronous=NORMAL")
        db_conn.row_factory = aiosqlite.Row

        if not _db_init:
            await init_db()
    return db_conn

async def init_db():
    global _db_init
    db = await get_db()
    
    await db.execute("""
    CREATE TABLE IF NOT EXISTS passed_tweets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tweet_id TEXT UNIQUE, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 建立複合唯一索引
    await db.execute("""
    CREATE TABLE IF NOT EXISTS tweets_media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tweet_id TEXT,
        media_id TEXT,
        media_type TEXT,
        download_path TEXT,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(tweet_id, media_id) 
    )
    """)
    # 針對 tweet_id 單獨建立索引
    await db.execute("CREATE INDEX IF NOT EXISTS idx_media_tweet_id ON tweets_media (tweet_id)")

    await db.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id TEXT,
        enable BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    await db.commit()
    _db_init = True

async def insert_passed_tweet(tweet_id: str):
    db = await get_db()
    # INSERT OR IGNORE，若 tweet_id 已存在則不執行，不會報錯
    await db.execute(
        "INSERT OR IGNORE INTO passed_tweets (tweet_id) VALUES (?)", 
        (tweet_id,)
    )
    await db.commit()

async def is_passed_tweet_exists(tweet_id: str) -> bool:
    db = await get_db()
    # 只查詢常數 1，且使用 LIMIT 1 找到即停止
    async with db.execute(
        "SELECT 1 FROM passed_tweets WHERE tweet_id = ? LIMIT 1", 
        (tweet_id,)
    ) as cursor:
        return await cursor.fetchone() is not None

async def insert_tweet_media(tweet_id: str, media_id: str, media_type: str, download_path: str):
    db = await get_db()
    await db.execute(
        "INSERT OR IGNORE INTO tweets_media (tweet_id, media_id, media_type, download_path) VALUES (?, ?, ?, ?)", 
        (tweet_id, media_id, media_type, download_path)
    )
    await db.commit()

async def is_tweet_media_exists(tweet_id: str, media_id: str) -> bool:
    db = await get_db()
    # 利用複合索引進行快速查詢
    async with db.execute(
        "SELECT 1 FROM tweets_media WHERE tweet_id = ? AND media_id = ? LIMIT 1", 
        (tweet_id, media_id)
    ) as cursor:
        return await cursor.fetchone() is not None

async def update_dc_channel(channel_id: str, enable: bool):
    db = await get_db()
    await db.execute(
        "INSERT OR REPLACE INTO channels (channel_id, enable) VALUES (?, ?)", 
        (channel_id, enable)
    )
    await db.commit()

async def get_dc_channel_enable(channel_id: str) -> bool:
    db = await get_db()
    async with db.execute(
        "SELECT enable FROM channels WHERE channel_id = ? LIMIT 1", 
        (channel_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return row['enable'] if row else False

async def get_dc_channel(channel_id: str) -> Optional[dict]:
    db = await get_db()
    async with db.execute(
        "SELECT * FROM channels WHERE channel_id = ? LIMIT 1", 
        (channel_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_all_dc_channels() -> list[dict]:
    db = await get_db()
    async with db.execute(
        "SELECT * FROM channels", 
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
