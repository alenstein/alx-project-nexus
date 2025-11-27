import os
from django.core.management.base import BaseCommand
from users.models import SiteUser

class Command(BaseCommand):
    """
    Custom management command to create a superuser from environment variables.
    """
    help = 'Creates a superuser using credentials from environment variables'

    def handle(self, *args, **options):
        email = os.environ.get('SUPERUSER_EMAIL')
        password = os.environ.get('SUPERUSER_PASSWORD')
        username = os.environ.get('SUPERUSER_USERNAME')

        if not email or not password or not username:
            self.stdout.write(self.style.ERROR('SUPERUSER_EMAIL, SUPERUSER_PASSWORD, and SUPERUSER_USERNAME must be set in the environment.'))
            return

        if SiteUser.objects.filter(email=email).exists():
            self.stdout.write(self.style.SUCCESS(f'Superuser with email {email} already exists.'))
        else:
            SiteUser.objects.create_superuser(email=email, username=username, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser {email}'))
