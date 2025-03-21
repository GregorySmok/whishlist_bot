import logging
import time
from pathlib import Path
import config


class AtomicFileHandler(logging.Handler):
    def __init__(self, log_dir, base_name):
        super().__init__()
        self.log_dir = log_dir
        self.base_name = base_name
        self.current_file = None
        self.current_day = None

    def get_file(self):
        today = time.strftime("%Y-%m-%d")
        if today != self.current_day:
            self.current_day = today
            new_file = self.log_dir / f"{self.base_name}_{today}.log"
            if self.current_file:
                self.current_file.close()
            self.current_file = open(new_file, 'a', encoding='utf-8')
        return self.current_file

    def emit(self, record):
        try:
            file = self.get_file()
            msg = self.format(record)
            file.write(msg + '\n')
            file.flush()
        except Exception as e:
            print(f"Error writing log: {e}")


def setup_logging():
    # Основной логгер
    main_logger = logging.getLogger('main')
    main_logger.setLevel(logging.INFO)
    main_handler = AtomicFileHandler(config.LOG_DIR, 'main')
    main_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"))
    main_logger.addHandler(main_handler)

    # Логгер действий пользователя
    user_logger = logging.getLogger('user_actions')
    user_logger.setLevel(logging.INFO)
    user_handler = AtomicFileHandler(config.LOG_DIR, 'user_actions')
    user_handler.setFormatter(logging.Formatter(
        "%(asctime)s - USER:%(user_id)s/%(username)s - ACTION:%(action)s - %(details)s"))
    user_logger.addHandler(user_handler)

    # Логгер ошибок
    error_logger = logging.getLogger('errors')
    error_logger.setLevel(logging.ERROR)
    error_handler = AtomicFileHandler(config.LOG_DIR, 'errors')
    error_handler.setFormatter(logging.Formatter(
        "%(asctime)s - ERROR:%(error)s - USER:%(user_id)s - TRACEBACK:%(traceback)s"))
    error_logger.addHandler(error_handler)

    return main_logger, user_logger, error_logger


# Инициализация логгеров
main_logger, user_logger, error_logger = setup_logging()


def log_user_action(user_id, username, action, details=""):
    user_logger.info("", extra={
        'user_id': user_id,
        'username': username,
        'action': action,
        'details': details
    })


def log_error(user_id, error, error_traceback=""):
    error_logger.error("", extra={
        'user_id': user_id,
        'error': str(error),
        'traceback': error_traceback
    })
