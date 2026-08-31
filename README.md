# TrayForge Platform

Набор инструментов для разработчиков и инженеров, объединённых под одним порталом.

## Сервисы

| Сервис | Образ | Описание |
|---|---|---|
| **portal** | `ghcr.io/rostgg/trayforge-portal:main` | Nginx — лендинг + reverse proxy |
| **trayforge** | `ghcr.io/rostgg/trayforge-app:main` | Параметрический генератор STL-лотков для SMT |
| **stencil-api** | `ghcr.io/rostgg/trayforge-stencil:main` | Python API — генератор Gerber → STL трафаретов |
| **kicanvas** | `ghcr.io/rostgg/trayforge-kicanvas:main` | Gerber / KiCad Viewer на базе KiCanvas (статика) |

## Быстрый старт (production)

### Требования

- Docker Engine 24+ и Docker Compose v2
- SSL-сертификат от Let's Encrypt (или любой другой CA)

### 1. Клонировать репозиторий

```bash
git clone https://github.com/ROSTGG/TrayForge.git
cd TrayForge
```

### 2. Получить SSL-сертификат

```bash
# Установить certbot, если нет
sudo apt install certbot

# Выпустить сертификат (порт 80 должен быть свободен)
sudo certbot certonly --standalone -d mscghost.dynet.com
```

Сертификат будет в `/etc/letsencrypt/archive/mscghost.dynet.com/`.

> Если домен другой — поменяй `server_name` в [`portal/nginx.conf`](portal/nginx.conf)
> и пути к сертификатам в [`docker-compose.yml`](docker-compose.yml).

### 3. Запустить все сервисы

```bash
docker compose up -d
```

Портал доступен на `https://mscghost.dynet.com`.  
HTTP (порт 80) автоматически редиректит на HTTPS.

### Остановить

```bash
docker compose down
```

### Посмотреть логи

```bash
# Все сервисы
docker compose logs -f

# Конкретный сервис
docker compose logs -f portal
docker compose logs -f stencil-api
```

### Обновить образы до последней версии

```bash
docker compose pull
docker compose up -d
```

---

## Разработка

### Локальный запуск Stencil Generator

```bash
cd stencil
pip install -r gerber_stencil_generator/requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

Открыть: `http://localhost:8080`

### Локальный запуск TrayForge (статика)

Просто открой `trayforge/index.html` в браузере — или:

```bash
cd trayforge
python -m http.server 8000
```

Открыть: `http://localhost:8000`

### Локальный запуск Gerber Viewer (KiCanvas)

Статическая страница, подгружает KiCanvas с CDN:

```bash
cd kicanvas
python -m http.server 8001
```

Открыть: `http://localhost:8001`

### Сборка образов вручную

```bash
# Portal
docker build -t trayforge-portal ./portal

# TrayForge app
docker build -t trayforge-app ./trayforge

# Stencil Generator
docker build -t trayforge-stencil ./stencil
```

---

## CI/CD

При каждом пуше в ветку `main` GitHub Actions автоматически собирает и публикует образы в GHCR:

| Workflow | Триггер | Образ |
|---|---|---|
| `build-app.yml` | изменения в `trayforge/` | `ghcr.io/rostgg/trayforge-app:main` |
| `build-portal.yml` | изменения в `portal/` | `ghcr.io/rostgg/trayforge-portal:main` |
| `build-stencil.yml` | изменения в `stencil/` | `ghcr.io/rostgg/trayforge-stencil:main` |
| `build-kicanvas.yml` | изменения в `kicanvas/` | `ghcr.io/rostgg/trayforge-kicanvas:main` |

После успешного пуша — достаточно выполнить `docker compose pull && docker compose up -d` на сервере.

---

## Маршрутизация (nginx)

| URL | Куда проксируется |
|---|---|
| `https://…/` | Лендинг (portal/index.html) |
| `https://…/trayforge/` | `trayforge:80` |
| `https://…/stencil/` | `stencil-api:8080` |
| `https://…/kicanvas/` | `kicanvas:80` |

## Переменные окружения (stencil-api)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `MAX_UPLOAD_MB` | `25` | Максимальный размер загружаемого файла |
| `JOB_TTL_MINUTES` | `60` | Время хранения результатов задания |
