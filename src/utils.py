import logging
import sys
import os

logger = logging.getLogger(__name__)

async def close_event():
    try:
        from .sqlite import get_db
        db = await get_db()
        await db.close()
    except Exception as e:
        logger.error(f'Error closing database: {e}')

def resource_path(relative_path): # 如果未來會用打包工具的話，可以用這個取得路徑
    """取得打包後的資源路徑"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path) # type: ignore
    return os.path.join(os.path.abspath("."), relative_path)