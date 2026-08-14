FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    JOBS_DIR=/tmp/gerber-stencil-jobs

WORKDIR /app
RUN useradd --create-home --uid 10001 appuser
COPY gerber_stencil_generator/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./app.py
COPY static ./static
COPY gerber_stencil_generator ./gerber_stencil_generator
RUN mkdir -p "$JOBS_DIR" && chown -R appuser:appuser /app "$JOBS_DIR"

USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=3)"
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--proxy-headers"]
