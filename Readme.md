# S3 Uploader - Инструмент для загрузки файлов в S3 хранилище

## Описание

Этот Python-скрипт предназначен для рекурсивной обработки файлов в указанной директории и их загрузки в S3-совместимое хранилище с возможностью гибкой настройки через конфигурационный файл.

## Основные возможности

- Рекурсивный обход директорий
- Фильтрация файлов по расширениям
- Гибкая система исключений (по директориям, путям, именам файлов)
- Проверка хеш-сумм файлов (xxHash) для определения необходимости обновления
- Генерация подробного отчета в JSON формате
- Поддержка нескольких режимов работы
- Статистика по типам файлов

## Требования

- Python 3.7+
- Установленные зависимости:
  ```
  pip install boto3 xxhash
  ```

## Конфигурация

Перед использованием необходимо создать конфигурационный файл `config.ini`:

```ini
[S3]
access_key = YOUR_ACCESS_KEY
secret_key = YOUR_SECRET_KEY
endpoint = https://s3.example.com
region = us-east-1
bucket = your-bucket-name

[Directories]
base_dir = /path/to/your/files

[Files]
extensions = .txt,.pdf,.jpg,.png,.docx

[Report]
path = /path/to/report.json

[Exclusions]
dir_exclusions = /path/to/dir_exclusions.json
file_exclusions = /path/to/file_exclusions.json
filename_exclusions = /path/to/filename_exclusions.json
```

### Файлы исключений

1. `dir_exclusions.json` - список директорий для исключения:
```json
["/path/to/exclude/dir1", "/another/excluded/dir"]
```

2. `file_exclusions.json` - список полных путей к файлам для исключения:
```json
["/full/path/to/exclude/file1.txt", "/another/excluded/file.pdf"]
```

3. `filename_exclusions.json` - список имен файлов для исключения (вне зависимости от их расположения):
```json
["dontsendme.txt", "backup.zip"]
```

## Использование

```bash
python s3_uploader.py --config config.ini --mode MODE
```

### Режимы работы (MODE):

1. **Проверка соединения** - проверяет возможность подключения к S3 хранилищу
   ```bash
   python s3_uploader.py --config config.ini --mode 1
   ```

2. **Подготовка отчета** - анализирует файлы и генерирует отчет без загрузки
   ```bash
   python s3_uploader.py --config config.ini --mode 2
   ```

3. **Загрузка файлов** - загружает файлы в S3 и генерирует отчет
   ```bash
   python s3_uploader.py --config config.ini --mode 3
   ```

4. **Загрузка со статистикой** - загружает файлы и выводит статистику по типам файлов
   ```bash
   python s3_uploader.py --config config.ini --mode 4
   ```

5. **Умное обновление** - загружает только измененные файлы (по хешу) с выводом статистики
   ```bash
   python s3_uploader.py --config config.ini --mode 5
   ```

## Формат отчета

Отчет сохраняется в формате JSON по пути, указанному в конфигурации. Каждая запись содержит:

```json
{
  "filePath": "полный путь к файлу",
  "s3code": "ключ файла в S3",
  "hash": "хеш-сумма файла (xxHash)",
  "date": "дата обработки в ISO формате",
  "sent": "флаг успешной загрузки (true/false)"
}
```

## Особенности работы

1. Для расчета хеш-сумм используется алгоритм xxHash
2. В метаданных S3 объекта сохраняется:
   - Хеш-сумма файла
   - Оригинальный путь к файлу
3. При повторном запуске в режиме 5 файлы не перезагружаются, если их хеш-сумма совпадает с уже загруженной версией
4. Статистика по расширениям файлов выводится только в режимах 4 и 5

## Лицензия

Этот проект распространяется под лицензией MIT.