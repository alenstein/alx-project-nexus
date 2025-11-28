# --- Stage 1: Builder ---
FROM python:3.13-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN <<EOF cat > .env && \
    set -a && . ./.env && set +a && \
    python eCommerce/manage.py collectstatic --noinput
SECRET_KEY="dummy"
DEBUG=False
DB_NAME="dummy"
DB_USER="dummy"
DB_PASSWORD="dummy"
DB_HOST="dummy"
DB_PORT="5432"
CELERY_BROKER_URL="dummy"
CELERY_RESULT_BACKEND="dummy"
EOF


# --- Stage 2: Production ---
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:$PATH"

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/staticfiles /app/staticfiles

COPY eCommerce/ .
# --- THE FIX ---
# Copy the entrypoint script and make it executable.
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
