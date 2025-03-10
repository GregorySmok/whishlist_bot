# file: file_lock_handler.py
import os
import logging
import time
import random
import errno
from logging.handlers import RotatingFileHandler
from pathlib import Path


class FileLock:
    """Блокировка на основе файловой системы"""

    def __init__(self, file_path, timeout=10, delay=0.05):
        """
        Инициализирует блокировку для указанного файла

        Args:
            file_path: Путь к файлу, который нужно заблокировать
            timeout: Максимальное время ожидания блокировки в секундах
            delay: Интервал между попытками получить блокировку
        """
        self.file_path = str(
            file_path)  # Преобразуем Path в строку, если необходимо
        self.lockfile = f"{self.file_path}.lock"
        self.timeout = timeout
        self.delay = delay
        self.is_locked = False

    def acquire(self):
        """Пытается получить блокировку"""
        start_time = time.time()

        while True:
            try:
                # Пытаемся создать файл блокировки
                fd = os.open(self.lockfile, os.O_CREAT |
                             os.O_EXCL | os.O_WRONLY)
                # Записываем PID в файл блокировки
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                self.is_locked = True
                break
            except OSError as e:
                # Если файл уже существует
                if e.errno != errno.EEXIST:
                    raise

                # Проверяем, не истекло ли время ожидания
                if time.time() - start_time >= self.timeout:
                    raise TimeoutError(
                        f"Не удалось получить блокировку для {self.file_path} за {self.timeout} секунд")

                # Проверяем, не является ли файл блокировки осиротевшим
                if os.path.exists(self.lockfile) and time.time() - os.path.getmtime(self.lockfile) > 60:
                    try:
                        os.remove(self.lockfile)
                        continue  # Пытаемся снова получить блокировку
                    except OSError:
                        pass  # Если не удалось удалить, продолжаем ждать

                # Ждем случайное время перед следующей попыткой
                # (добавляем немного рандомизации, чтобы уменьшить вероятность конфликтов)
                time.sleep(self.delay + random.uniform(0, 0.1))

    def release(self):
        """Освобождает блокировку"""
        if self.is_locked:
            try:
                os.remove(self.lockfile)
                self.is_locked = False
            except OSError:
                pass  # Игнорируем ошибки при удалении файла блокировки

    def __enter__(self):
        """Поддержка контекстного менеджера"""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Освобождение блокировки при выходе из контекста"""
        self.release()

    def __del__(self):
        """Освобождение блокировки при удалении объекта"""
        self.release()


class LockedFileHandler(logging.FileHandler):
    """Обработчик файлов логов с блокировкой на основе файловой системы"""

    def __init__(self, filename, mode='a', encoding=None, delay=False):
        super().__init__(filename, mode, encoding, delay)
        self.lock_instance = FileLock(filename)

    def emit(self, record):
        """Переопределяет метод emit для использования блокировки"""
        with self.lock_instance:
            super().emit(record)


class LockedRotatingFileHandler(RotatingFileHandler):
    """Обработчик файлов логов с ротацией и блокировкой на основе файловой системы"""

    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.lock_instance = FileLock(filename)

    def emit(self, record):
        """Переопределяет метод emit для использования блокировки"""
        with self.lock_instance:
            super().emit(record)

    def doRollover(self):
        """Переопределяет метод doRollover для использования блокировки при ротации"""
        with self.lock_instance:
            super().doRollover()
