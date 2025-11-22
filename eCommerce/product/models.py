from django.db import models

# Create your models here.
class ProductCategory(models.Model):
    """
    Hierarchical category system (e.g., Clothing > Men > T-Shirts).
    Uses a self-referential foreign key.
    """
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Product Categories"

    def __str__(self):
        if self.parent_category:
            return f"{self.parent_category.name} > {self.name}"
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Colour(models.Model):
    """Lookup table for product colors."""
    colour_name = models.CharField(max_length=50)

    def __str__(self):
        return self.colour_name

class SizeOption(models.Model):
    """Lookup table for sizes (S, M, L, 42, 44, etc)."""
    size_name = models.CharField(max_length=50)
    sort_order = models.IntegerField(default=0, help_text="Order to display size in dropdowns")

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.size_name

# --- TIER 1: The Abstract Product ---
class Product(models.Model):
    """
    The abstract product definition.
    Contains data that is shared across all variations.
    """
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField()
    care_instructions = models.TextField(blank=True)
    about = models.TextField(blank=True)

    def __str__(self):
        return self.name

# --- TIER 2: The Visual Variant (Color) ---
class ProductItem(models.Model):
    """
    A specific visual variation of the product (e.g., 'Nike Shirt in RED').
    Holds the price and the link to specific images.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='items')
    colour = models.ForeignKey(Colour, on_delete=models.CASCADE, related_name='product_items')
    sku_base = models.CharField(max_length=100, unique=True, help_text="Base SKU for this color variant")
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.colour.colour_name}"

    @property
    def price(self):
        """Helper to return sale price if it exists, else original."""
        return self.sale_price if self.sale_price else self.original_price

class ProductImage(models.Model):
    """
    Images are linked to the ProductItem (Color), not the generic Product.
    This ensures Red shirts show Red images.
    """
    product_item = models.ForeignKey(ProductItem, on_delete=models.CASCADE, related_name='images')
    image_filename = models.ImageField(upload_to='products/', help_text="Uploads to MEDIA_ROOT/products/")
    is_default = models.BooleanField(default=False, help_text="Is this the main image for this color?")

    def __str__(self):
        return f"Image for {self.product_item}"

# --- TIER 3: The Inventory Variant (Size) ---
class ProductVariation(models.Model):
    """
    The specific physical inventory unit (e.g., 'Nike Shirt in RED, Size M').
    This is what is actually added to the cart.
    """
    product_item = models.ForeignKey(ProductItem, on_delete=models.CASCADE, related_name='variations')
    size = models.ForeignKey(SizeOption, on_delete=models.CASCADE)
    qty_in_stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product_item', 'size') # Prevent duplicate Red-Size M entries

    def __str__(self):
        return f"{self.product_item} - Size {self.size.size_name}"