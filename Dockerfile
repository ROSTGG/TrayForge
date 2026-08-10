FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY portal/index.html /usr/share/nginx/html/portal/index.html
COPY index.html /usr/share/nginx/html/trayforge/index.html
COPY styles.css /usr/share/nginx/html/trayforge/styles.css
COPY app.js     /usr/share/nginx/html/trayforge/app.js
EXPOSE 80 443
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost/ || exit 1
