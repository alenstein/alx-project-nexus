import logging
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import path, reverse
from rest_framework import status, views
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.test import APITestCase

from users.models import SiteUser

# --- Test-specific views and URLs for triggering exceptions ---

class AdminOnlyView(views.APIView):
    """A dummy view that is only accessible by admin users."""
    permission_classes = [IsAdminUser]
    def get(self, request):
        return Response({"message": "Success!"})

class ServerErrorView(views.APIView):
    """A dummy view that deliberately raises a generic exception."""
    def get(self, request):
        raise Exception("This is a deliberate test server error.")

# Define a temporary URL configuration for these tests.
# This keeps test endpoints out of our main urls.py.
urlpatterns = [
    path('test/admin-only/', AdminOnlyView.as_view(), name='test-admin-only'),
    path('test/server-error/', ServerErrorView.as_view(), name='test-server-error'),
]

# --- Test Suite ---

@override_settings(ROOT_URLCONF='eCommerce.eCommerce.tests')
class ExceptionHandlerIntegrationTests(APITestCase):
    """
    Integration tests for the custom_exception_handler.

    This suite verifies that various exceptions are caught and formatted
    into a consistent JSON response structure: {"errors": ...}
    """
    def setUp(self):
        # Create a regular user (non-admin)
        self.user = SiteUser.objects.create_user(username='testuser', email='test@example.com', password='password123', is_active=True)
        self.client.force_authenticate(user=self.user)

    def test_permission_denied_403(self):
        """
        Test that a PermissionDenied (403) error is formatted correctly.
        """
        url = reverse('test-admin-only')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('errors', response.data)
        self.assertIn('detail', response.data['errors'])
        self.assertEqual(response.data['errors']['detail'], 'You do not have permission to perform this action.')

    def test_method_not_allowed_405(self):
        """
        Test that a MethodNotAllowed (405) error is formatted correctly.
        We do this by trying to POST to a GET-only endpoint.
        """
        url = reverse('test-admin-only')
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn('errors', response.data)
        self.assertIn('detail', response.data['errors'])
        self.assertEqual(response.data['errors']['detail'], 'Method "POST" not allowed.')

    @patch('eCommerce.eCommerce.exception_handler.logger')
    def test_server_error_500(self, mock_logger):
        """
        Test that a generic unhandled exception (500) is formatted correctly
        and that the error is logged.
        """
        url = reverse('test-server-error')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('errors', response.data)
        self.assertIn('detail', response.data['errors'])
        self.assertEqual(response.data['errors']['detail'], 'A server error occurred. Please try again later.')

        # Verify that the error was logged
        self.assertTrue(mock_logger.error.called)
        # Check that the log message contains the expected text
        log_call_args = mock_logger.error.call_args[0][0]
        self.assertIn("Unhandled exception caught: This is a deliberate test server error.", log_call_args)
