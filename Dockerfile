# --- Base Image ---
# Use an official Python runtime as a parent image that matches the development environment
FROM python:3.13-slim

# --- Environment Variables ---
# Set environment variables to prevent Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED=1

# --- Build-time Arguments ---
# Declare an argument that can be passed in during the build process.
ARG SECRET_KEY

# --- Application Setup ---
# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire eCommerce application directory into the container
COPY eCommerce/ .

# Copy the entrypoint script
COPY entrypoint.sh .

# --- Make Entrypoint Executable ---
RUN chmod +x /app/entrypoint.sh

# --- Collect Static Files ---
# This command uses the SECRET_KEY provided as a build argument.
# This key is not saved in the final image layers.
RUN SECRET_KEY=${SECRET_KEY} python manage.py collectstatic --noinput

# --- Expose Port ---
# Expose the port the app runs on
EXPOSE 8000

# --- Entrypoint ---
# The entrypoint script will run migrations and create a superuser before starting the app.
ENTRYPOINT ["/app/entrypoint.sh"]

# --- Default Command ---
# The command that the entrypoint will execute after it finishes.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "eCommerce.wsgi:application"]
