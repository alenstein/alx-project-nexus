# --- Stage 1: Builder ---
# This stage only installs Python dependencies
FROM python:3.13-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# --- Stage 2: Production ---
# This is the final image that will be deployed
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:$PATH"

# Install netcat for the wait-for-db script
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the entire application source code
COPY . .

# Run collectstatic directly in the final stage.
# This ensures the staticfiles directory is created and populated correctly.
RUN export SECRET_KEY='dummy' && \
    export DEBUG='False' && \
    export DB_NAME='dummy' && \
    export DB_USER='dummy' && \
    export DB_PASSWORD='dummy' && \
    export DB_HOST='dummy' && \
    export DB_PORT='5432' && \
    export CELERY_BROKER_URL='dummy' && \
    export CELERY_RESULT_BACKEND='dummy' && \
    python eCommerce/manage.py collectstatic --noinput

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
