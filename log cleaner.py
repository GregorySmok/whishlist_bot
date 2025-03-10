from datetime import datetime, timedelta
import time
import os


def clean_log_file(log_file_path):
    while True:
        try:
            # Определяем временную границу (2 дня назад)
            cutoff_time = datetime.now() - timedelta(days=2)

            # Читаем все строки из исходного файла
            with open(log_file_path, 'r') as f:
                lines = f.readlines()

            # Фильтруем строки
            filtered_lines = []
            for line in lines:
                try:
                    log_time_str = line.split(' - ')[0]
                    log_time = datetime.strptime(
                        log_time_str, '%Y-%m-%d %H:%M:%S,%f')
                    if log_time >= cutoff_time:
                        filtered_lines.append(line)
                except:
                    continue  # Пропускаем некорректные записи

            # Перезаписываем исходный файл
            with open(log_file_path, 'w') as f:
                f.writelines(filtered_lines)

            # Сохраняем метаданные (права и владельца)
            stat = os.stat(log_file_path)
            os.chown(log_file_path, stat.st_uid, stat.st_gid)
            os.chmod(log_file_path, stat.st_mode)

        except Exception as e:
            print(f"Ошибка: {e}. Повтор через 5 секунд...")
            time.sleep(5)  # 5 минут перед повторной попыткой
            continue


if __name__ == "__main__":
    clean_log_file('/opt/whishlist_bot/data/logs/user_actions.log')
