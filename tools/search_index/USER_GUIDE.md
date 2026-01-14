# Руководство пользователя - Search Index Uploader

Утилита для создания поисковых индексов Yandex Cloud из файлов.

## Быстрый старт

### 1. Установка

```bash
pip install yandex-cloud-ml-sdk click
```

### 2. Настройка аутентификации

```bash
export YC_API_KEY="your-api-key"
export YC_FOLDER_ID="your-folder-id"
```

### 3. Способы запуска

```bash
python -m tools.search_index local --directory ./docs -v
```

```bash
python tools/search_index/main.py local --directory ./docs -v
```

```bash
cd tools/search_index
./main.py local --directory ../../docs -v
```

```bash
python -m tools.search_index local \
  --directory ./docs \
  -v
```

**Результат:**
```
Search index created successfully!
Search Index ID: fvt3h07ivlh83a3sn38m
Name: docs
```

## Базовые примеры

### Пример 1: Индексация markdown файлов

```bash
python -m tools.search_index.cli local \
  --directory ./documentation \
  --pattern "**/*.md" \
  --index-name "Markdown Docs" \
  -v
```

**Что делает:**
- Сканирует директорию `./documentation`
- Находит все `.md` файлы (включая вложенные папки)
- Загружает их в Yandex Cloud
- Создает поисковый индекс с именем "Markdown Docs"

### Пример 2: Индексация с исключениями

```bash
python -m tools.search_index.cli local \
  --directory ./project \
  --exclude-pattern "*/node_modules/*" \
  --exclude-pattern "*/venv/*" \
  --exclude-pattern "*.pyc" \
  -v
```

**Что делает:**
- Сканирует всю директорию `./project`
- Пропускает `node_modules`, `venv` и `.pyc` файлы
- Индексирует все остальные файлы

### Пример 3: Временные файлы с автоудалением

```bash
python -m tools.search_index.cli local \
  --directory ./temp-upload \
  --file-ttl-days 7 \
  --file-expiration-policy static \
  --delete-files \
  -v
```

**Что делает:**
- Загружает файлы с TTL 7 дней
- Файлы автоматически удалятся через 7 дней
- После создания индекса удаляет загруженные файлы из облака
- Локальные файлы остаются нетронутыми

### Пример 4: Гибридный поиск с метками

```bash
python -m tools.search_index.cli local \
  --directory ./knowledge-base \
  --index-type hybrid \
  --index-label project=ai \
  --index-label env=prod \
  --file-label source=kb \
  -v
```

**Что делает:**
- Создает гибридный индекс (текстовый + векторный поиск)
- Добавляет метки к индексу для организации
- Добавляет метки к файлам для отслеживания

## Параметры командной строки

### Основные параметры

#### `--directory`, `-d` (обязательный)
Путь к директории с файлами для индексации.

```bash
--directory ./docs
-d /path/to/files
```

#### `--pattern`
Glob-паттерн для фильтрации файлов. По умолчанию: `**/*` (все файлы).

```bash
--pattern "*.txt"           # Только .txt файлы в корне
--pattern "**/*.pdf"        # Все PDF файлы везде
--pattern "**/*.{md,txt}"   # Markdown и текстовые файлы
```

#### `--exclude-pattern`
Исключить файлы по паттерну. Можно указать несколько раз.

```bash
--exclude-pattern "*.log" \
--exclude-pattern "*/temp/*" \
--exclude-pattern "*/cache/*"
```

#### `--max-file-size`
Максимальный размер файла в байтах. Большие файлы будут пропущены.

```bash
--max-file-size 10485760    # 10 МБ
--max-file-size 1048576     # 1 МБ
```

### Параметры индекса

#### `--index-name`
Имя индекса. По умолчанию: имя директории.

```bash
--index-name "Корпоративная база знаний"
```

#### `--index-description`
Описание индекса.

```bash
--index-description "Техническая документация версии 2.0"
```

#### `--index-type`
Тип индекса: `text`, `vector` или `hybrid`. По умолчанию: `text`.

```bash
--index-type text      # Полнотекстовый поиск
--index-type vector    # Семантический поиск
--index-type hybrid    # Комбинированный поиск
```

**Когда что использовать:**
- `text` - для точного поиска по ключевым словам
- `vector` - для семантического поиска по смыслу
- `hybrid` - лучший выбор для большинства случаев

#### `--index-label`
Метки для индекса в формате `KEY=VALUE`. Можно указать несколько.

```bash
--index-label env=prod \
--index-label team=ml \
--index-label version=2.0
```

#### `--index-ttl-days` и `--index-expiration-policy`
Время жизни индекса. Оба параметра должны быть указаны вместе.

```bash
# Индекс удалится через 30 дней с момента создания
--index-ttl-days 30 \
--index-expiration-policy static

# Индекс удалится через 30 дней после последнего использования
--index-ttl-days 30 \
--index-expiration-policy since_last_active
```

#### `--max-chunk-size-tokens` и `--chunk-overlap-tokens`
Настройки разбиения документов на чанки.

```bash
--max-chunk-size-tokens 700     # Размер чанка (по умолчанию)
--chunk-overlap-tokens 300      # Перекрытие (по умолчанию)
```

### Параметры файлов

#### `--file-ttl-days` и `--file-expiration-policy`
Время жизни загруженных файлов.

```bash
--file-ttl-days 7 \
--file-expiration-policy static
```

#### `--file-label`
Метки для файлов.

```bash
--file-label source=local \
--file-label uploaded_by=bot
```

#### `--delete-files`
Удалить загруженные файлы после создания индекса.

```bash
--delete-files
```

**Внимание:** Это удаляет файлы из Yandex Cloud, не локальные файлы!

### Параметры производительности

#### `--batch-size`
Количество файлов в одном батче. По умолчанию: 50.

```bash
--batch-size 100
```

#### `--max-workers`
Количество параллельных потоков загрузки. По умолчанию: 4.

```bash
--max-workers 8    # Быстрее, но больше нагрузка
--max-workers 2    # Медленнее, но меньше нагрузка
```

#### `--skip-on-error`
Пропускать файлы с ошибками вместо остановки. По умолчанию: включено.

```bash
# Отключить (остановиться при первой ошибке)
--no-skip-on-error
```

### Логирование

#### `-v` (INFO)
Показывает основные этапы работы.

```bash
python -m tools.search_index.cli local -d ./docs -v
```

**Вывод:**
```
2026-01-14 14:39:27 - INFO - Estimated files to process: 5
2026-01-14 14:39:28 - INFO - Uploaded file README.md (1/5)
2026-01-14 14:39:28 - INFO - Uploaded file guide.md (2/5)
...
```

#### `-vv` (DEBUG)
Максимально подробные логи.

```bash
python -m tools.search_index.cli local -d ./docs -vv
```

**Вывод:**
```
2026-01-14 14:39:27 - DEBUG - Found file: docs/README.md (size: 1024, mime: text/markdown)
2026-01-14 14:39:27 - DEBUG - Reading file: docs/README.md
2026-01-14 14:39:28 - DEBUG - Successfully uploaded file: README.md (id: fvt1a...)
...
```
