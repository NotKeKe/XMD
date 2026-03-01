def init_me():
    import logging
    import logging.handlers
    import sys

    from .config import LOG_DIR

    log_dir = LOG_DIR

    # formatter
    log_format = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # root
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # console handler
    console_handler = logging.StreamHandler(sys.__stderr__)
    console_handler.setFormatter(log_format)

    # file handler
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / "app.log",  # 主要日誌檔的名稱
        when='D',                     # 'D' 代表按天 (Day) 輪替
        interval=1,                   # 間隔為 1 天
        backupCount=10,               # 保留 10 個舊的日誌檔案 (等於保留10天的紀錄)
        encoding="utf-8",
    )
    # --------------------------

    file_handler.setFormatter(log_format)

    # avoid to add handler twice
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    class StreamToLogger:
        def __init__(self, logger, level):
            self.logger = logger
            self.level = level

        def write(self, message):
            if message.rstrip() != "" and message.rstrip() != '^':
                self.logger.log(self.level, message.rstrip())

        def flush(self):
            pass

        def isatty(self):
            return False

    sys.stdout = StreamToLogger(logging.getLogger("stdout"), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger("stderr"), logging.ERROR)

init_me()