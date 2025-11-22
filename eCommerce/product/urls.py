from django.urls import path
from .views import (
    ProductListView, 
    ProductDetailView,
    ProductCategoryListView,
    BrandListView
)

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('<int:id>/', ProductDetailView.as_view(), name='product-detail'),
    path('categories/', ProductCategoryListView.as_view(), name='category-list'),
    path('brands/', BrandListView.as_view(), name='brand-list'),
]
