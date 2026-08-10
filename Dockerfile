# ── TrayForge Docker Image ──
# Лёгкий nginx-контейнер для раздачи статического приложения
FROM nginx:1.27-alpine

# Копируем конфиг nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем файлы приложения
COPY index.html /usr/share/nginx/html/
COPY styles.css /usr/share/nginx/html/
COPY app.js     /usr/share/nginx/html/

# Nginx слушает порт 80 внутри контейнера
EXPOSE 80

# Healthcheck — проверяем что nginx отвечает
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost/ || exit 1
