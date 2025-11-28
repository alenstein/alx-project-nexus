# --- Stage 1: Builder ---
# This is a temporary stage to build our assets.
FROM python:3.13-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a dummy .env file and run collectstatic
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
# This is the final, lean image that will be deployed.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:$PATH"

WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages


# Copy the executables (like gunicorn and celery) from the builder stage
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy collected static files from the builder stage
COPY --from=builder /app/staticfiles /app/staticfiles

# Copy the application code to the root of the workdir for a clean, flat structure.
COPY eCommerce/ .

EXPOSE 8000
