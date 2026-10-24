FROM python:3.11-slim

# Cài đặt uv từ official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Cài đặt thư viện libpq để psycopg2 hoạt động nếu cần compile
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH="/app/src"

# Mặc định mở shell hoặc chạy uvicorn
CMD ["uv", "run", "uvicorn", "app.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "--reload"]
