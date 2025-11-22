from django.contrib import admin
from .models import Product, ProductImage, ProductItem, ProductVariation, ProductCategory, SizeOption, Brand, Colour

# Register your models here.
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ProductItem)
admin.site.register(ProductVariation)
admin.site.register(ProductCategory)
admin.site.register(SizeOption)
admin.site.register(Brand)
admin.site.register(Colour)


