"""
URL configuration for eCommerce project.
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from users.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

# Health check view
def health_check(request):
    """A simple view that returns a 200 OK response."""
    return JsonResponse({"status": "ok"})

schema_view = get_schema_view(
   openapi.Info(
      title="E-Commerce API",
      default_version='v1',
      description="API documentation for the E-Commerce backend project.",
      contact=openapi.Contact(email="contact@example.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('healthz/', health_check, name='health-check'), # Health check endpoint

    # API v1 URLs
    path('api/v1/auth/', include('users.urls')),
    path('api/v1/products/', include('product.urls')),
    path('api/v1/cart/', include('cart.urls')),

    # JWT Token Endpoints using the custom view
    path('api/v1/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
