# Multi-stage build для оптимизации размера образа
FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements.txt .

# Установка зависимостей
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.10-slim

WORKDIR /app

# Копирование зависимостей из builder
COPY --from=builder /root/.local /root/.local

# Копирование кода
COPY src/ src/
COPY api/ api/
COPY requirements.txt .

# Установка PATH
ENV PATH=/root/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000

# Запуск с uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
