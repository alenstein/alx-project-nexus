#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Apply database migrations
echo "Applying database migrations..."
python eCommerce/manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
python eCommerce/manage.py create_superuser

# Run the database seeder.
echo "Checking if database seeding is required..."
python eCommerce/manage.py seed_db

echo "Setup tasks complete. This container will now exit."
