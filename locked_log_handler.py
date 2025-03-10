# file: locked_log_handler.py
import os
import logging
import multiprocessing as mp
import tempfile
import pickle
from logging.handlers import RotatingFileHandler

LOCK_DIR = tempfile.gettempdir()


class FileLockManager:
    """Менеджер блокировок для файлов логов"""

    def __init__(self):
        self.locks = {}

    def get_lock_path(self, file_path):
        """Возвращает путь к файлу блокировки для указанного файла логов"""
        filename = os.path.basename(file_path)
        lock_filename = f"{filename}.lock"
        return os.path.join(LOCK_DIR, lock_filename)

    def get_lock(self, file_path):
        """Получает или создает блокировку для указанного файла логов"""
        if file_path in self.locks:
            return self.locks[file_path]

        lock_path = self.get_lock_path(file_path)

        # Проверяем, существует ли уже файл с сериализованной блокировкой
        if os.path.exists(lock_path):
            try:
                with open(lock_path, 'rb') as f:
                    lock = pickle.load(f)
                self.locks[file_path] = lock
                return lock
            except (pickle.PickleError, EOFError, AttributeError):
                # Если файл поврежден, создаем новую блокировку
                pass

        # Создаем новую блокировку
        lock = mp.Lock()

        # Сохраняем в файл
        with open(lock_path, 'wb') as f:
            pickle.dump(lock, f)

        self.locks[file_path] = lock
        return lock


# Создаем глобальный менеджер блокировок
lock_manager = FileLockManager()


class LockedFileHandler(logging.FileHandler):
    """Обработчик файлов логов с блокировкой"""

    def __init__(self, filename, mode='a', encoding=None, delay=False):
        super().__init__(filename, mode, encoding, delay)
        self.lock = lock_manager.get_lock(filename)

    def emit(self, record):
        """Переопределяет метод emit для использования блокировки"""
        self.lock.acquire()
        try:
            super().emit(record)
        finally:
            self.lock.release()


class LockedRotatingFileHandler(RotatingFileHandler):
    """Обработчик файлов логов с ротацией и блокировкой"""

    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.lock = lock_manager.get_lock(filename)

    def emit(self, record):
        """Переопределяет метод emit для использования блокировки"""
        self.lock.acquire()
        try:
            super().emit(record)
        finally:
            self.lock.release()
