from datetime import datetime, timedelta
from time import sleep
import os


def clean_log_file(log_file_path):
    while True:
        try:
            now = datetime.now()
            two_days_ago = now - timedelta(days=2)
            temp_file_path = log_file_path + '.tmp'

            with open(log_file_path, 'r') as log_file, open(temp_file_path, 'w') as temp_file:
                for line in log_file:
                    log_time_str = line.split(' - ')[0]
                    log_time = datetime.strptime(
                        log_time_str, '%Y-%m-%d %H:%M:%S,%f')
                    if log_time >= two_days_ago:
                        temp_file.write(line)

            os.replace(temp_file_path, log_file_path)
            break  # Выход из цикла, если очистка прошла успешно
        except Exception as e:
            print(
                f"Ошибка при очистке файла логов: {e}. Повторная попытка через 5 секунд...")
            sleep(5)
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)


if __name__ == "__main__":
    log_file_path = 'data/logs/user_actions.log'
    clean_log_file(log_file_path)
