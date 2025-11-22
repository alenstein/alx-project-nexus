from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from .models import SiteUser, Address, Country, UserAddress

# Use a consistent set of test data
TEST_USER_DATA = {
    'email': 'testuser@example.com',
    'username': 'testuser',
    'first_name': 'Test',
    'last_name': 'User',
    'password': 'StrongPassword123!',
}

class UserModelTests(TestCase):
    """
    Tests for the behavior of the custom user and address models.
    """
    def test_create_user(self):
        """Ensure a user can be created with an email as the username field."""
        user = SiteUser.objects.create_user(**TEST_USER_DATA)
        self.assertEqual(user.email, TEST_USER_DATA['email'])
        self.assertEqual(user.username, TEST_USER_DATA['username'])
        self.assertTrue(user.check_password(TEST_USER_DATA['password']))
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active) # create_user should create an active user by default

    def test_create_superuser(self):
        """Ensure a superuser is created with appropriate flags."""
        superuser = SiteUser.objects.create_superuser(**TEST_USER_DATA)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)

    def test_user_address_default_logic(self):
        """Test that only one address can be the default."""
        user = SiteUser.objects.create_user(**TEST_USER_DATA)
        country = Country.objects.create(name='Testland')
        address1 = Address.objects.create(address_line1='123 Test St', city='Testville', region='Test Region', postal_code='12345', country=country)
        address2 = Address.objects.create(address_line1='456 Test Ave', city='Testville', region='Test Region', postal_code='12345', country=country)

        # Set first address as default
        user_addr1 = UserAddress.objects.create(user=user, address=address1, is_default=True)
        self.assertTrue(user_addr1.is_default)

        # Set second address as default, should automatically unset the first one
        user_addr2 = UserAddress.objects.create(user=user, address=address2, is_default=True)
        self.assertTrue(user_addr2.is_default)

        # Refresh the first address from the database to check its state
        user_addr1.refresh_from_db()
        self.assertFalse(user_addr1.is_default)
        self.assertEqual(UserAddress.objects.filter(user=user, is_default=True).count(), 1)

class AuthFlowAPITests(APITestCase):
    """
    End-to-end tests for the entire authentication and user management API flow.
    """
    def test_user_registration_and_email_confirmation(self):
        """
        Test the full registration and email confirmation flow.
        """
        # 1. User Registration
        url = reverse('user-register')
        data = {**TEST_USER_DATA, 'password2': TEST_USER_DATA['password']}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SiteUser.objects.count(), 1)
        
        user = SiteUser.objects.get(email=TEST_USER_DATA['email'])
        self.assertFalse(user.is_active, "User should be inactive until email is confirmed.")

        # 2. Email Confirmation
        self.assertEqual(len(mail.outbox), 1, "An email should be sent.")
        email = mail.outbox[0]
        self.assertEqual(email.to, [TEST_USER_DATA['email']])
        
        # Extract confirmation link from email body
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        confirm_url = reverse('email-confirm', kwargs={'uidb64': uid, 'token': token})
        
        response = self.client.get(confirm_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user.refresh_from_db()
        self.assertTrue(user.is_active, "User should be active after email confirmation.")

    def test_registration_password_mismatch(self):
        """Ensure registration fails if passwords do not match."""
        url = reverse('user-register')
        data = {**TEST_USER_DATA, 'password2': 'WrongPassword!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_and_logout(self):
        """
        Test that an active user can log in to get tokens and then log out.
        """
        # Create an active user first
        user = SiteUser.objects.create_user(**TEST_USER_DATA, is_active=True)

        # 1. Login (Token Obtain)
        login_url = reverse('token_obtain_pair')
        login_data = {'email': TEST_USER_DATA['email'], 'password': TEST_USER_DATA['password']}
        response = self.client.post(login_url, login_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        refresh_token = response.data['refresh']

        # 2. Logout (Token Blacklist)
        logout_url = reverse('user-logout')
        # Authenticate the request to logout
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        response = self.client.post(logout_url, {'refresh': refresh_token}, format='json')

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # 3. Verify token is blacklisted
        refresh_url = reverse('token_refresh')
        response = self.client.post(refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, "Blacklisted token should not be refreshable.")

    def test_login_inactive_user(self):
        """Ensure an inactive user cannot log in."""
        # Create an inactive user directly
        SiteUser.objects.create_user(**TEST_USER_DATA, is_active=False)
        
        login_url = reverse('token_obtain_pair')
        login_data = {'email': TEST_USER_DATA['email'], 'password': TEST_USER_DATA['password']}
        response = self.client.post(login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class UserProfileAPITests(APITestCase):
    """
    Tests for authenticated user profile and address management.
    """
    def setUp(self):
        """Set up an authenticated user for all tests in this class."""
        self.user = SiteUser.objects.create_user(**TEST_USER_DATA, is_active=True)
        
        # Log in the user and get tokens
        login_url = reverse('token_obtain_pair')
        login_data = {'email': self.user.email, 'password': TEST_USER_DATA['password']}
        response = self.client.post(login_url, login_data, format='json')
        self.access_token = response.data['access']
        
        # Set credentials for all subsequent requests in this class
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_get_and_update_user_details(self):
        """Test retrieving and updating the authenticated user's own profile."""
        url = reverse('user-detail')
        
        # 1. Retrieve details
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

        # 2. Update details
        update_data = {'first_name': 'Updated', 'phone_number': '1234567890'}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.phone_number, '1234567890')

    def test_address_management(self):
        """Test creating, listing, and updating user addresses."""
        url = reverse('user-address-list')
        country = Country.objects.create(name='Testland')

        # 1. Create a new address
        address_data = {
            'address': {
                'address_line1': '123 Main St',
                'city': 'Anytown',
                'region': 'Test Region',
                'postal_code': '12345',
                'country_id': country.id
            },
            'is_default': True
        }
        response = self.client.post(url, address_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserAddress.objects.count(), 1)
        self.assertEqual(Address.objects.count(), 1)

        # 2. List addresses
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['address']['city'], 'Anytown')

    def test_unauthenticated_access_fails(self):
        """Ensure unauthenticated users cannot access protected profile endpoints."""
        # Clear authentication credentials
        self.client.credentials()
        
        detail_url = reverse('user-detail')
        address_url = reverse('user-address-list')

        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(address_url).status_code, status.HTTP_401_UNAUTHORIZED)
