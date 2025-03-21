# file: logging_setup.py
import logging
import config
from file_lock_handler import LockedFileHandler, LockedRotatingFileHandler

# Определение директории скрипта
SCRIPT_DIR = config.LOG_DIR


def setup_logging():
    """Настраивает логгирование с использованием обработчиков с блокировкой"""

    # Основной логгер
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Очищаем существующие обработчики (если есть)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Используем LockedFileHandler вместо FileHandler
    handler = LockedFileHandler(SCRIPT_DIR / "start.log", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Настройка уровня логгирования для aiogram
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)

    # Логгер для действий пользователя
    user_logger = logging.getLogger("user_actions")
    user_logger.setLevel(logging.INFO)

    # Очищаем существующие обработчики (если есть)
    if user_logger.hasHandlers():
        user_logger.handlers.clear()

    # Используем LockedRotatingFileHandler для автоматической ротации логов
    user_handler = LockedRotatingFileHandler(
        SCRIPT_DIR / "user_actions.log",
        encoding="utf-8",
        maxBytes=50*1024,  # 10 MB
        backupCount=30
    )
    user_formatter = logging.Formatter(
        "%(asctime)s - USER_ID: %(user_id)s - USERNAME: %(username)s - ACTION: %(action)s - DETAILS: %(details)s"
    )
    user_handler.setFormatter(user_formatter)
    user_logger.addHandler(user_handler)

    # Логгер для ошибок
    error_logger = logging.getLogger("error_log")
    error_logger.setLevel(logging.ERROR)

    # Очищаем существующие обработчики (если есть)
    if error_logger.hasHandlers():
        error_logger.handlers.clear()

    # Используем LockedFileHandler для ошибок
    error_handler = LockedRotatingFileHandler(  # Меняем на Rotating
        SCRIPT_DIR / "errors.log",
        encoding="utf-8",
        maxBytes=20*1024,  # 20 KB
        backupCount=60
    )
    error_formatter = logging.Formatter(
        "%(asctime)s - USER_ID: %(user_id)s - ERROR: %(error)s - TRACEBACK: %(traceback)s"
    )
    error_handler.setFormatter(error_formatter)
    error_logger.addHandler(error_handler)

    return logger, user_logger, error_logger


# Получаем настроенные логгеры
logger, user_logger, error_logger = setup_logging()


def log_user_action(user_id, username, action, details=""):
    """Логирует действия пользователя"""
    user_logger.info(
        "",
        extra={
            "user_id": user_id,
            "username": username,
            "action": action,
            "details": details,
        },
    )


def log_error(user_id, error, error_traceback=""):
    """Логирует ошибки с идентификатором пользователя"""
    error_logger.error(
        "",
        extra={
            "user_id": user_id,
            "error": str(error),
            "traceback": error_traceback
        },
    )
