import logging
import sys
import os
import importlib
import inspect
from pathlib import Path

logger = logging.getLogger(__name__)

async def close_event():
    try:
        from .sqlite import get_db
        db = await get_db()
        await db.close()
    except Exception as e:
        logger.error(f'Error closing database: {e}')

async def load_service():
    from .config import services_open, BASE_DIR
    from .abc import ServicesABC
    
    service_objs = []
    services_dir = Path(__file__).parent / "services"
    
    # 遍歷 services/ 目錄
    for entry in services_dir.iterdir():
        if not entry.is_dir():
            continue
            
        main_path = entry / "main.py"
        if not main_path.exists():
            continue
            
        try:
            # 動態導入
            # 使用 pathlib 取得相對路徑並轉為模組路徑格式 (例如 src.services.discord.main)
            module_path = ".".join(main_path.with_suffix("").relative_to(BASE_DIR).parts)
            module = importlib.import_module(module_path)
            
            # 尋找繼承 ServicesABC 的 class
            for class_name, cls in inspect.getmembers(module, inspect.isclass):
                # 排除 ServicesABC 本身，只檢查其子類
                if issubclass(cls, ServicesABC) and cls is not ServicesABC:
                    parts = class_name.lower().split("service")
                    service_key = parts[0] # 取得第一項 (例如 discord)
                    
                    # 比對 config 中的 service_open，預設開啟
                    # twitter 是必載入的
                    if service_key == "twitter" or services_open.get(service_key, True):
                        service_objs.append(cls())
                        logger.info(f"Successfully loaded service: {class_name}")
                        
        except Exception as e:
            logger.error(f"Failed to load service from {entry.name}: {e}")
            
    return service_objs