# --- Stage 1: Builder ---
# This stage installs dependencies and collects static files.
FROM python:3.13-slim as builder

# --- Environment Variables ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --- Build-time Arguments ---
# Declare all arguments that are needed during the build process.
# These are passed in from the 'docker build' command and are not persisted.
ARG SECRET_KEY
ARG DEBUG
ARG ALLOWED_HOSTS
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ARG DB_HOST
ARG DB_PORT
ARG CELERY_BROKER_URL
ARG CELERY_RESULT_BACKEND
ARG EMAIL_BACKEND

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY eCommerce/ .
COPY entrypoint.sh .

# --- Collect Static Files ---
# This command now uses all the arguments provided during the build.
RUN python manage.py collectstatic --noinput

# --- Stage 2: Production ---
# This is the final, lean image that will be run.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Copy collected static files from the builder stage
COPY --from=builder /app/staticfiles /app/staticfiles

# Copy the application code and entrypoint
COPY eCommerce/ .
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

# Expose the port the app runs on
EXPOSE 8000

# The entrypoint script will run migrations and create a superuser before starting the app.
ENTRYPOINT ["/app/entrypoint.sh"]

# The command that the entrypoint will execute after it finishes.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "eCommerce.wsgi:application"]
