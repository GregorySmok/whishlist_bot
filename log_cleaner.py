import time
import os
from pathlib import Path
import config
from datetime import datetime, timedelta

MAX_LOG_AGE_DAYS = 2


def clean_logs():
    now = time.time()
    cutoff = now - (MAX_LOG_AGE_DAYS * 86400)

    for file in Path(config.LOG_DIR).glob('*.log'):
        # Не трогаем текущие файлы
        if '_' not in file.name:
            continue

        try:
            # Извлекаем дату из имени файла
            date_str = file.name.split('_')[-1].split('.')[0]
            file_date = datetime.strptime(date_str, "%Y-%m-%d")

            if file_date < (datetime.now() - timedelta(days=MAX_LOG_AGE_DAYS)):
                os.remove(file)
                print(f"Removed old log: {file}")
        except Exception as e:
            print(f"Error processing {file}: {e}")


if __name__ == "__main__":
    clean_logs()
