# file: log_cleaner.py
import os
import time
import datetime
import re
from pathlib import Path
from file_lock_handler import FileLock
import logging
import config
from datetime import datetime, timedelta

# Определение директории скрипта
SCRIPT_DIR = config.LOG_DIR

# Настройки для очистки
MAX_LOG_AGE_DAYS = 2  # Очищаем записи старше 2 дней

# Логи, которые нужно очищать
LOG_FILES = [
    SCRIPT_DIR / "start.log",
    SCRIPT_DIR / "user_actions.log",
    SCRIPT_DIR / "errors.log"
]

# Настраиваем логгер для очистки
cleaner_logger = logging.getLogger("log_cleaner")
cleaner_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"))
cleaner_logger.addHandler(console_handler)


def parse_log_date(line, log_path):
    """
    Извлекает дату из строки лога.
    Возвращает объект datetime или None, если дату извлечь не удалось.
    """
    # Различные форматы для разных типов логов
    date_patterns = [
        # Стандартный формат для start.log
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})',
        # Формат для user_actions.log и errors.log
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
    ]

    for pattern in date_patterns:
        match = re.search(pattern, line)
        if match:
            date_str = match.group(1)
            try:
                # Если есть миллисекунды
                if ',' in date_str:
                    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S,%f')
                # Без миллисекунд
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                cleaner_logger.warning(
                    f"Не удалось распознать дату в строке: {line}")

    # Если не смогли распознать дату, предполагаем, что запись новая (сохраняем её)
    cleaner_logger.warning(
        f"Не удалось извлечь дату из строки лога в файле {log_path}")
    return None


def clean_log_by_date(log_path):
    """Очищает лог-файл, удаляя записи старше MAX_LOG_AGE_DAYS дней"""
    if not os.path.exists(log_path):
        cleaner_logger.info(f"Лог-файл {log_path} не существует.")
        return

    # Вычисляем пороговую дату (текущая дата минус MAX_LOG_AGE_DAYS)
    threshold_date = datetime.now() - timedelta(days=MAX_LOG_AGE_DAYS)
    cleaner_logger.info(
        f"Очистка лог-файла {log_path}. Удаляем записи старше {threshold_date}")

    # Используем FileLock вместо старого lock_manager
    with FileLock(log_path):
        try:
            # Читаем содержимое файла
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Подсчитываем исходное количество строк
            original_count = len(lines)

            # Фильтруем строки по дате
            filtered_lines = []
            removed_count = 0

            for line in lines:
                if not line.strip():  # Пропускаем пустые строки
                    filtered_lines.append(line)
                    continue

                log_date = parse_log_date(line, log_path)

                # Если не смогли распознать дату или дата новее пороговой, сохраняем строку
                if log_date is None or log_date >= threshold_date:
                    filtered_lines.append(line)
                else:
                    removed_count += 1

            # Если были удалены записи, переписываем файл
            if removed_count > 0:
                # Пишем в новый временный файл
                temp_path = f"{log_path}.temp"
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.writelines(filtered_lines)

                # Заменяем старый файл новым
                os.replace(temp_path, log_path)

                cleaner_logger.info(
                    f"Лог-файл {log_path} очищен. Удалено строк: {removed_count} из {original_count}")
            else:
                cleaner_logger.info(
                    f"В лог-файле {log_path} нет записей старше {MAX_LOG_AGE_DAYS} дней.")

        except Exception as e:
            cleaner_logger.error(
                f"Ошибка при очистке лог-файла {log_path}: {str(e)}")


def clean_old_rotated_logs():
    """Удаляет ротированные логи старше MAX_LOG_AGE_DAYS"""
    now = time.time()

    for log_path in LOG_FILES:
        log_dir = log_path.parent
        log_name = log_path.name

        # Ищем ротированные логи (обычно имеют формат filename.log.1, filename.log.2 и т.д.)
        for file in log_dir.glob(f"{log_name}.*"):
            # Исключаем файлы блокировок (.lock)
            if str(file).endswith('.lock'):
                continue

            # Проверяем возраст файла
            file_age_days = (now - os.path.getmtime(file)) / (24 * 60 * 60)

            if file_age_days > MAX_LOG_AGE_DAYS:
                cleaner_logger.info(
                    f"Удаление старого лог-файла {file} (возраст: {file_age_days:.1f} дней)")
                try:
                    os.remove(file)
                except OSError as e:
                    cleaner_logger.error(
                        f"Ошибка при удалении файла {file}: {e}")


def run_cleaner():
    """Запускает процесс очистки логов"""
    cleaner_logger.info("Запуск программы очистки логов...")

    # Очищаем старые ротированные логи
    clean_old_rotated_logs()

    # Очищаем текущие логи, удаляя записи старше 2 дней
    for log_path in LOG_FILES:
        clean_log_by_date(log_path)

    cleaner_logger.info("Программа очистки логов завершена.")


if __name__ == "__main__":
    run_cleaner()
