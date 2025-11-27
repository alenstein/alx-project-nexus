from django_filters import rest_framework as filters
from .models import Product


class ProductFilter(filters.FilterSet):
    """
    Custom filter set for the Product model.
    Enables filtering by category, brand, and a price range.
    """
    # Filter by the name of the related category (case-insensitive)
    category = filters.CharFilter(field_name='category__name', lookup_expr='iexact')
    
    # Filter by the name of the related brand (case-insensitive)
    brand = filters.CharFilter(field_name='brand__name', lookup_expr='iexact')

    # Filter for items with a price greater than or equal to the given value
    min_price = filters.NumberFilter(field_name="items__original_price", lookup_expr='gte')
    
    # Filter for items with a price less than or equal to the given value
    max_price = filters.NumberFilter(field_name="items__original_price", lookup_expr='lte')

    class Meta:
        model = Product
        # These fields are now explicitly defined above for more control
        fields = ['category', 'brand', 'min_price', 'max_price']
