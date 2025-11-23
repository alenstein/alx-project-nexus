# --- Base Image ---
# Use an official Python runtime as a parent image that matches the development environment
FROM python:3.13-slim

# --- Environment Variables ---
# Set environment variables to prevent Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED=1

# --- Application Setup ---
# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire eCommerce application directory into the container
COPY eCommerce/ .

# --- Expose Port ---
# Expose the port the app runs on
EXPOSE 8000

# --- Entrypoint ---
# The command to run when the container starts.
# Gunicorn is a production-grade WSGI server.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "eCommerce.wsgi:application"]
