import logging
from logging.handlers import RotatingFileHandler
from ivr.config.settings import settings

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger