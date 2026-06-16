# Безопасность файлов

## Назначение

`file_guard` — единый изолированный сервис, который проверяет пользовательские файлы до того, как backend сохранит их в MinIO/S3 и создаст связь в базе данных.

Основной поток данных не меняется:

```text
frontend -> backend -> file_guard -> verdict -> backend persistence
```

## Почему проверка вынесена из backend

* Backend остаётся оркестратором и не дублирует глубокий разбор файлов.
* Один сервис проверки обеспечивает единые правила загрузки для заявок, КП, чатов и нормативных документов.
* Поведение fail-closed централизовано: если `file_guard` не может завершить обязательную проверку, backend не сохраняет файл.

## Модель контейнера

`file_guard` — один выделенный внутренний контейнер в сети `project_net`.

Внутри того же контейнера:

* FastAPI отдаёт `/scan` и `/health`
* валидаторы форматов проверяют PDF, DOCX, XLSX, PNG и JPEG
* локальный ClamAV (`clamd`) выполняет антивирусную проверку через Unix socket

Отдельного сервиса `clamav` в runtime-стеке нет.

Базы сигнатур ClamAV хранятся в постоянном Docker volume (`clamav_data`, смонтирован в `/var/lib/clamav`), поэтому пересоздание контейнера не вынуждает заново скачивать все базы.

## Разрешённые типы файлов

Разрешённые расширения:

* `.pdf`
* `.docx`
* `.xlsx`
* `.jpg`
* `.jpeg`
* `.png`

Всё остальное отклоняется с `reason_code=file_type_not_allowed`.

## Этапы проверки

Каждая загрузка проходит эти шаги до сохранения в backend:

1. Безопасность имени файла
2. Проверка пустого файла и размера
3. Allowlist / denylist расширений
4. Проверка MIME и сигнатуры
5. Глубокая структурная проверка формата
6. Антивирусное сканирование

Примеры глубокой проверки:

* PDF: читаемость, отсутствие шифрования, отсутствие опасного активного содержимого
* DOCX/XLSX: обязательные OpenXML entry, защита от zip-slip, макросов, zip-bomb и resource abuse, скриптов и активного содержимого
* PNG/JPEG: декодируемое изображение с безопасными размерами

## Проверка Office-документов на скрипты и активное содержимое

Файлы DOCX и XLSX — это ZIP-контейнеры. `file_guard` блокирует их, если внутри архива найдено:

* скриптовые файлы (`.js`, `.vbs`, `.ps1`, `.bat`, `.sh`, `.py`, `.php` и аналогичные)
* HTML/SVG-вложения
* признаки OLE/ActiveX (`oleObject`, `activeX`, `embed`, вложения `.bin`)
* артефакты макросов (`vbaProject`, `macroEnabled`, `application/vnd.ms-office.vbaProject`)
* подозрительные external-цели в `.rels` (`javascript:`, `vbscript:`, `file:`, `cmd`, `powershell`, `ms-its:`)
* content type с поддержкой макросов
* небезопасные пути entry (`\`, `..`, абсолютные пути, управляющие символы, слишком длинные имена)
* слишком большие XML entry, которые нужно анализировать по содержимому

Типичные коды блокировки:

* `invalid_office_document` — нарушение структуры или политики содержимого внутри DOCX/XLSX
* `malware_detected` — ClamAV обнаружил угрозу

## Правила fail-closed

Файл блокируется, если:

* `file_guard` не может завершить обязательную проверку
* ClamAV недоступен или истёк таймаут
* MIME/сигнатура не соответствует расширению
* структура файла повреждена или выглядит подозрительно
* обнаружено вредоносное содержимое

Backend также блокирует сохранение, если сам `file_guard` недоступен.

## Коды причин (`reason_code`)

Публичные коды, которые видит пользователь через backend:

* `file_type_not_allowed`
* `file_too_large`
* `empty_file`
* `unsafe_file_name`
* `mime_mismatch`
* `invalid_pdf`
* `encrypted_pdf_not_allowed`
* `invalid_office_document`
* `invalid_image`
* `malware_detected`
* `file_scan_unavailable`

`file_guard` может хранить технические сообщения на английском, но backend обязан возвращать безопасный русский текст по `reason_code`.

### Сообщения пользователю

| reason_code | Сообщение |
| ----------- | --------- |
| `file_type_not_allowed` | Недопустимый тип файла. |
| `file_too_large` | Файл слишком большой. |
| `empty_file` | Файл пустой. |
| `unsafe_file_name` | Недопустимое имя файла. |
| `mime_mismatch` | Содержимое файла не соответствует расширению файла. |
| `invalid_pdf` | PDF-файл поврежден или не читается. |
| `encrypted_pdf_not_allowed` | Зашифрованные PDF-файлы запрещены. |
| `invalid_office_document` | Office-файл поврежден или имеет неверную структуру. |
| `invalid_image` | Изображение повреждено или имеет неверный формат. |
| `malware_detected` | Файл не прошел проверку безопасности. |
| `file_scan_unavailable` | Файл не удалось проверить. Попробуйте загрузить его позже. |

## Health и готовность

`/health` возвращает `200` только когда:

* FastAPI запущен
* антивирус либо явно отключён настройкой, либо готов к сканированию

Если `FILE_GUARD_REQUIRE_ANTIVIRUS=true`, а ClamAV не готов, `/health` возвращает `503` — контейнер считается неготовым к безопасной обработке загрузок.

Для production недопустимо `FILE_GUARD_ANTIVIRUS_ENABLED=false`. В production-like конфигурации используйте `FILE_GUARD_ANTIVIRUS_ENABLED=true` и `FILE_GUARD_REQUIRE_ANTIVIRUS=true`.

## Переменные окружения

Важные переменные backend:

* `FILE_GUARD_ENABLED` — направлять upload через `file_guard` (fail-closed при `true` и недоступном сервисе)
* `FILE_GUARD_URL` — внутренний URL сервиса (по умолчанию `http://file_guard:8080`)
* `FILE_GUARD_TIMEOUT_SECONDS` — HTTP-таймаут клиента backend при вызове `/scan` (по умолчанию `10`)
* `MAX_UPLOAD_SIZE_BYTES` — лимит размера одного файла

Важные переменные `file_guard`:

* `FILE_GUARD_REQUIRE_ANTIVIRUS` — если `true`, `/health` и `/scan` отклоняют работу без готового антивируса (`503` / `file_scan_unavailable`)
* `FILE_GUARD_SCAN_TIMEOUT_SECONDS` — end-to-end дедлайн одного `/scan` (парсинг + структурные проверки + AV; по умолчанию `30`)
* `FILE_GUARD_ANTIVIRUS_TIMEOUT_SECONDS` — таймаут одного вызова ClamAV внутри сканирования (по умолчанию `10`)
* `FILE_GUARD_MAX_FILE_SIZE_BYTES`
* `FILE_GUARD_UPLOAD_READ_CHUNK_BYTES`
* `FILE_GUARD_ALLOW_LIBMAGIC_FALLBACK`
* `FILE_GUARD_ANTIVIRUS_ENABLED`
* `FILE_GUARD_ANTIVIRUS_TIMEOUT_SECONDS`
* `FILE_GUARD_CLAMD_SOCKET_PATH`
* `FILE_GUARD_CLAMAV_UPDATE_ON_START`
* `FILE_GUARD_OFFICE_MAX_ENTRIES`
* `FILE_GUARD_OFFICE_MAX_TOTAL_UNCOMPRESSED_BYTES`
* `FILE_GUARD_OFFICE_MAX_ENTRY_UNCOMPRESSED_BYTES`
* `FILE_GUARD_OFFICE_MAX_COMPRESSION_RATIO`
* `FILE_GUARD_OFFICE_MAX_XML_SCAN_BYTES`
* `FILE_GUARD_OFFICE_MAX_ENTRY_NAME_LENGTH`
* `FILE_GUARD_IMAGE_MAX_WIDTH`
* `FILE_GUARD_IMAGE_MAX_HEIGHT`
* `FILE_GUARD_IMAGE_MAX_PIXELS`

## Ручной smoke-тест

`file_guard` не публикует порт наружу (только `expose: 8080` внутри `project_net`). Прямые проверки `/health` и `/scan` выполняйте **из контейнера** или через backend upload.

Проверка compose-конфигурации и сборки:

```bash
docker compose config
docker compose build file_guard
docker compose up -d file_guard
docker compose logs -f file_guard
```

Проверка health (внутри контейнера):

```bash
docker compose exec file_guard curl -fsS http://localhost:8080/health
```

Ожидаемый ответ при готовом антивирусе:

```json
{
  "status": "ok",
  "antivirus": "ready"
}
```

При `FILE_GUARD_REQUIRE_ANTIVIRUS=true` и неготовом ClamAV ожидается `503`.

Проверка EICAR:

```bash
docker compose exec file_guard sh -c 'printf "%s\n" "X5O!P%@AP[4\\PZX54(P^)7CC)7}\$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!\$H+H*" > /tmp/eicar.txt && curl -fsS -F "file=@/tmp/eicar.txt" http://localhost:8080/scan'
```

Ожидаемый ответ:

```json
{
  "allowed": false,
  "reason_code": "malware_detected"
}
```

Загрузка валидного PNG/PDF (файл должен быть доступен внутри контейнера, например через `docker compose cp`):

```bash
docker compose cp ./valid.png file_guard:/tmp/valid.png
docker compose exec file_guard curl -fsS -F "file=@/tmp/valid.png" http://localhost:8080/scan
```

Ожидаемый ответ:

```json
{
  "allowed": true,
  "reason_code": null
}
```

Проверка полного пути через backend (upload к заявке/КП) — отдельный сценарий в [release-checklist.md](./release/release-checklist.md).

## Примечания

Текущая реализация держит ClamAV внутри `file_guard`. Если нагрузка вырастет, антивирусный движок можно вынести в отдельный сервис без изменения контракта загрузки backend.

Любой ручной smoke, который сохраняет файл через backend, должен после успешной проверки удалить созданную связь в БД и объект в хранилище. Прямые вызовы `/scan` не оставляют артефактов в persistence, но проверки загрузки через backend не должны оставлять тестовые файлы в MinIO или в таблицах связей файлов.
