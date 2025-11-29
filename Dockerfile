# --- Stage 1: Builder ---
FROM python:3.13-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Production ---
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:$PATH"

WORKDIR /app

# Copy installed packages and executables from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the entire project into the container
COPY . .

# Create a dummy .env file and run collectstatic
# This is necessary for the build process, even though the real .env file is used at runtime.
RUN echo "SECRET_KEY=dummy" > .env && \
    python manage.py collectstatic --noinput

# Copy the entrypoint script and make it executable.
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
