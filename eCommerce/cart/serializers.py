from rest_framework import serializers
from .models import ShoppingCart, ShoppingCartItem

class CartItemReadSerializer(serializers.ModelSerializer):
    """
    Read-Only serializer to display rich data in the cart.
    Flattens the nested product data for easier frontend consumption.
    """
    product_name = serializers.CharField(source='product_variation.product_item.product.name')
    product_brand = serializers.CharField(source='product_variation.product_item.product.brand.name')
    colour = serializers.CharField(source='product_variation.product_item.colour.colour_name')
    size = serializers.CharField(source='product_variation.size.size_name')
    price = serializers.DecimalField(source='product_variation.product_item.price', max_digits=10, decimal_places=2)
    image = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = ShoppingCartItem
        fields = ['id', 'product_variation', 'qty', 'product_name', 'product_brand',
                  'colour', 'size', 'price', 'image', 'subtotal']

    def get_image(self, obj):
        # Fetch the default image for this specific color variant
        item = obj.product_variation.product_item
        default_image = item.images.filter(is_default=True).first()
        if default_image:
            # Return absolute URL if request context is available
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(default_image.image_filename.url)
            return default_image.image_filename.url
        return None

class CartItemWriteSerializer(serializers.ModelSerializer):
    """
    Write serializer for adding/updating items.
    """
    class Meta:
        model = ShoppingCartItem
        fields = ['id', 'product_variation', 'qty']

    def validate(self, data):
        # Optional: Check stock levels here
        variation = data.get('product_variation')
        qty = data.get('qty')
        if variation and qty > variation.qty_in_stock:
            raise serializers.ValidationError(f"Only {variation.qty_in_stock} items in stock.")
        return data

class ShoppingCartSerializer(serializers.ModelSerializer):
    items = CartItemReadSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ['id', 'user', 'items', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['user']
