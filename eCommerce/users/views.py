from rest_framework import generics, status, views, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (
    UserRegistrationSerializer, 
    UserDetailSerializer, 
    UserAddressSerializer,
    CustomTokenObtainPairSerializer
)
from .models import SiteUser, UserAddress
from .tasks import send_confirmation_email_task  # Import the Celery task
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import get_object_or_404

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that uses the custom serializer to check for active users and merge carts.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # Pass context to the serializer
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class UserRegistrationView(generics.CreateAPIView):
    """
    API view for user registration.
    Creates an inactive user and sends a confirmation email via a background task.
    """
    queryset = SiteUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        # Generate token and confirmation link
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        confirm_link = f"http://localhost:8000/api/v1/auth/confirm-email/{uid}/{token}/"
        
        subject = 'Activate Your E-Commerce Account'
        message = f'Hi {user.first_name},\n\nPlease click the link below to confirm your email address and activate your account:\n{confirm_link}'
        
        # --- Send email asynchronously ---
        send_confirmation_email_task.delay(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )

class EmailConfirmationView(views.APIView):
    """
    API view to confirm a user's email and activate their account.
    """
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = SiteUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, SiteUser.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({'message': 'Email confirmed successfully. You can now log in.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Confirmation link is invalid or has expired.'}, status=status.HTTP_400_BAD_REQUEST)

class UserLogoutView(views.APIView):
    """
    API view for user logout.
    Blacklists the refresh token to invalidate the session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    API view to retrieve and update the authenticated user's details.
    """
    queryset = SiteUser.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserAddressViewSet(viewsets.ModelViewSet):
    """
    API viewset for managing user addresses.
    """
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the addresses
        for the currently authenticated user, ordered by the default status.
        """
        # Short-circuit for schema generation
        if getattr(self, 'swagger_fake_view', False):
            return UserAddress.objects.none()
            
        return UserAddress.objects.filter(user=self.request.user).order_by('-is_default')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
