FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required by shapely, gerbonara, and trimesh
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-dev \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    && pip install --no-cache-dir -r requirements.txt

# Copy core library and API
COPY stencil_core.py .
COPY main.py .
COPY aperture_library.json .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health').read()" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
