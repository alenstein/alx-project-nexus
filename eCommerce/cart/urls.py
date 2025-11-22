from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet

# A router is used to automatically generate the URLs for a ViewSet.
# This will create endpoints for list, create, retrieve, update, and destroy actions.
router = DefaultRouter()
router.register(r'', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
]
