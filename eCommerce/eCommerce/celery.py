import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eCommerce.settings')

# Create a Celery instance and configure it using the settings from Django.
# The first argument is the name of the current module.
app = Celery('eCommerce')

# Load task modules from all registered Django app configs.
# Celery will look for a 'tasks.py' file in each app.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps.
app.autodiscover_tasks()
