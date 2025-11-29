# --- Stage 1: Builder ---
# Use 'as' keyword for aliasing the stage
FROM python:3.13-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the builder stage
COPY . .

# Export dummy environment variables and run collectstatic
# This makes the variables available for the collectstatic command
RUN export SECRET_KEY='dummy' && \
    export DEBUG='False' && \
    export DB_NAME='dummy' && \
    export DB_USER='dummy' && \
    export DB_PASSWORD='dummy' && \
    export DB_HOST='dummy' && \
    python eCommerce/manage.py collectstatic --noinput

# --- Stage 2: Production ---
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:$PATH"

WORKDIR /app

# Copy installed packages and executables from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code from the current directory
COPY . .

# Copy the collected static files from the builder stage
COPY --from=builder /app/staticfiles /app/staticfiles/

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
