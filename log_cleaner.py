import os
from pathlib import Path
import config.config as config
from datetime import datetime, timedelta
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

MAX_LOG_AGE_DAYS = 2


def clean_logs():
    """
    Удаляет лог-файлы, которые старше MAX_LOG_AGE_DAYS дней.
    Игнорирует текущие лог-файлы (без даты в имени).
    """
    cutoff_date = datetime.now() - timedelta(days=MAX_LOG_AGE_DAYS)
    logging.info(f"Начало очистки логов. Удаляем файлы старше {cutoff_date.strftime('%Y-%m-%d')}")
    
    removed_count = 0
    error_count = 0
    
    for file in Path(config.LOG_DIR).glob('*.log'):
        # Не трогаем текущие файлы
        if '_' not in file.name:
            logging.debug(f"Пропускаем текущий лог-файл: {file}")
            continue

        try:
            # Извлекаем дату из имени файла
            date_str = file.name.split('_')[-1].split('.')[0]
            file_date = datetime.strptime(date_str, "%Y-%m-%d")

            if file_date < cutoff_date:
                os.remove(file)
                logging.info(f"Удален старый лог: {file}")
                removed_count += 1
        except Exception as e:
            logging.error(f"Ошибка при обработке {file}: {e}")
            error_count += 1
    
    logging.info(f"Очистка завершена. Удалено файлов: {removed_count}, ошибок: {error_count}")


if __name__ == "__main__":
    clean_logs()