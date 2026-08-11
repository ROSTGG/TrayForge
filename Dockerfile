FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf

# Портал (главная страница)
COPY index.html /usr/share/nginx/html/index.html

# TrayForge (приложение)
COPY trayforge/ /usr/share/nginx/html/trayforge/

EXPOSE 80 443
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost/ || exit 1
