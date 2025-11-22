from django.contrib import admin
from .models import Address, Country, SiteUser, UserAddress

# Register your models here.
admin.site.register(Address)
admin.site.register(Country)
admin.site.register(SiteUser)
admin.site.register(UserAddress)