from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class SiteUser(AbstractUser):
    """
    Custom user model that uses email as the unique identifier
    instead of a username. Inherits standard fields (first_name,
    last_name, password, is_staff) from AbstractUser.
    """
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # Set email as the unique identifier for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    def __str__(self):
        return self.email

class Country(models.Model):
    """Lookup table for countries."""
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name

class Address(models.Model):
    """
    Stores physical address data.
    Decoupled from User to allow reusability if needed.
    """
    unit_number = models.CharField(max_length=20, blank=True, null=True)
    street_number = models.CharField(max_length=20, blank=True, null=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100) # State/Province
    postal_code = models.CharField(max_length=20)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='addresses')

    def __str__(self):
        return f"{self.address_line1}, {self.city}"

class UserAddress(models.Model):
    """
    Junction table linking Users to Addresses.
    Allows a user to have multiple addresses (Home, Work).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_addresses')
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "User Addresses"

    def save(self, *args, **kwargs):
        # Logic: If setting as default, uncheck is_default for all other addresses of this user
        if self.is_default:
            UserAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.address}"
