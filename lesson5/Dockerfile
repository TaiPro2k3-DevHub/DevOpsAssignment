# Step 1: Builder
FROM python:3.14-slim-bookworm AS builder

WORKDIR /app

RUN pip install poetry

# Bắt buộc Poetry tạo .venv ngay trong /app/.venv
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-root

# Step 2: Production Runtime
FROM python:3.14-slim-bookworm AS runner

WORKDIR /app

# 1. Thêm biến môi trường để hệ thống tìm thấy lệnh uvicorn trong .venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

COPY --from=builder /app/.venv /app/.venv

COPY . .

# USER appuser

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]