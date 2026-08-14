# Stencil Forge

Веб-версия генератора герметичных STL-трафаретов из Gerber paste-mask.

## Запуск в Docker

```bash
docker compose up --build -d
```

Откройте <http://localhost:8080>. Проверка состояния: <http://localhost:8080/api/health>.

Остановка:

```bash
docker compose down
```

Результаты хранятся во временной памяти контейнера и по умолчанию удаляются через 60 минут. Лимит файла — 25 МБ. Значения можно изменить через `MAX_UPLOAD_MB` и `JOB_TTL_MINUTES` в `compose.yaml`.

## Локальный запуск для разработки

```bash
python -m venv .venv
.venv/Scripts/pip install -r gerber_stencil_generator/requirements.txt
.venv/Scripts/uvicorn app:app --reload --port 8080
```

## Возможности

- `.gtp`, `.gbp`, `.gbr`, `.ger`, `.pho`;
- толщина, поля, скругление, компенсация апертур;
- фиксированный или автоматический размер листа;
- поворот, отражение, фильтр малых апертур;
- SVG-предпросмотр, STL и JSON-отчёт;
- проверка герметичности модели перед выдачей.
