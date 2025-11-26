#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py create_superuser

# Run the database seeder. The seeder script itself will check if it needs to run.
echo "Checking if database seeding is required..."
python manage.py seed_db

# --- Start Celery worker in the background ---
echo "Starting Celery worker in the background..."
celery -A eCommerce worker --loglevel=info &

# --- Start the main application (Gunicorn) in the foreground ---
echo "Starting Gunicorn server..."
exec "$@"
