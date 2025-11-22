from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Product, ProductCategory, Brand
from .serializers import (
    ProductListSerializer, 
    ProductDetailSerializer,
    ProductCategorySerializer,
    BrandSerializer
)

class ProductListView(generics.ListAPIView):
    """
    API view to list all products.
    Uses a lightweight serializer and is optimized for performance.
    """
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """
        Optimized queryset to prevent N+1 query problems.
        Prefetches related items and their default images in a minimal number of queries.
        """
        return Product.objects.all().prefetch_related(
            'items__images'
        ).order_by('id')

class ProductDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve a single product with all its details.
    """
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id' # Use 'id' for the lookup

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
