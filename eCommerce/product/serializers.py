from rest_framework import serializers
from .models import (
    ProductCategory, Brand, Colour, SizeOption,
    Product, ProductItem, ProductImage, ProductVariation
)

# --- Lookup Serializers ---
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']

class ColourSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colour
        fields = ['id', 'colour_name']

class SizeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeOption
        fields = ['id', 'size_name', 'sort_order']

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'parent_category']

# --- Tier 3: Variation (Size) ---
class ProductVariationSerializer(serializers.ModelSerializer):
    size = serializers.StringRelatedField() # Returns "M" instead of ID
    size_id = serializers.IntegerField(source='size.id', read_only=True)

    class Meta:
        model = ProductVariation
        fields = ['id', 'size', 'size_id', 'qty_in_stock']

# --- Tier 2: Item (Color + Images) ---
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image_filename', 'is_default']

class ProductItemSerializer(serializers.ModelSerializer):
    colour = serializers.StringRelatedField()
    colour_id = serializers.IntegerField(source='colour.id', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variations = ProductVariationSerializer(many=True, read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ProductItem
        fields = ['id', 'colour', 'colour_id', 'sku_base', 'price', 'images', 'variations']

# --- Tier 1: Product (Parent) ---
class ProductListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views (Catalog page).
    Fetches the main image and the lowest price for a better user experience.
    """
    brand = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    price = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'brand', 'category', 'price', 'image']

    def get_price(self, obj):
        """Returns the lowest price of all available product items."""
        prices = [item.price for item in obj.items.all() if item.price is not None]
        if prices:
            return min(prices)
        return None

    def get_image(self, obj):
        """Returns the URL of the first default image found for any item."""
        # Using prefetch_related('items__images') in the view is recommended
        for item in obj.items.all():
            default_image = next((img for img in item.images.all() if img.is_default), None)
            if default_image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(default_image.image_filename.url)
                return default_image.image_filename.url
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Heavy serializer for the Product Detail Page.
    Includes all nested relationships (Items -> Images/Variations).
    """
    brand = BrandSerializer(read_only=True)
    category = ProductCategorySerializer(read_only=True)
    items = ProductItemSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'care_instructions', 'about',
                  'brand', 'category', 'items']
