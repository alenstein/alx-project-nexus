from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Product, ProductCategory, Brand
from .serializers import (
    ProductListSerializer, 
    ProductDetailSerializer,
    ProductCategorySerializer,
    BrandSerializer
)
from .filters import ProductFilter

class ProductListView(generics.ListAPIView):
    """
    API view to list all products with filtering, sorting, and pagination.
    
    **Filtering:**
    - `category`: Filter by category name (e.g., `?category=Clothing`)
    - `brand`: Filter by brand name (e.g., `?brand=Nike`)
    - `min_price`: Filter by minimum price (e.g., `?min_price=50`)
    - `max_price`: Filter by maximum price (e.g., `?max_price=200`)
    
    **Sorting:**
    - `ordering`: Sort by price or name (e.g., `?ordering=price` or `?ordering=-price`)
    
    **Searching:**
    - `search`: Search by product name and description (e.g., `?search=shirt`)
    """
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    filterset_class = ProductFilter
    ordering_fields = ['items__original_price', 'name']
    search_fields = ['name', 'description']

    def get_queryset(self):
        """
        Optimized queryset to prevent N+1 query problems.
        Prefetches related items and their default images in a minimal number of queries.
        """
        return Product.objects.all().prefetch_related(
            'items__images'
        ).distinct()

class ProductDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve a single product with all its details.
    """
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

class ProductCategoryListView(generics.ListAPIView):
    """
    API view to list all product categories.
    """
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [AllowAny]

class BrandListView(generics.ListAPIView):
    """
    API view to list all brands.
    """
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [AllowAny]
