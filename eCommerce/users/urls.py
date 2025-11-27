from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView,
    EmailConfirmationView,
    UserLogoutView,
    UserDetailView,
    UserAddressViewSet,
)

router = DefaultRouter()
router.register(r'addresses', UserAddressViewSet, basename='user-address')

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('confirm-email/<str:uidb64>/<str:token>/', EmailConfirmationView.as_view(), name='email-confirm'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('me/', UserDetailView.as_view(), name='user-detail'),
    path('', include(router.urls)),
]
