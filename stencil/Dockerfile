FROM python:3.10-slim

# Устанавливаем системные зависимости для 3D/геометрии (если требуются)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Запускаем FastAPI сервер
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]