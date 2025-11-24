from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from .models import SiteUser, Address, Country, UserAddress
from product.models import Product, ProductCategory, Brand, Colour, SizeOption, ProductItem, ProductVariation
from cart.models import ShoppingCart, ShoppingCartItem

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

class CartMergingTests(APITestCase):
    """
    Tests for the cart merging logic upon user login.
    """
    def setUp(self):
        """Set up a user and product variations for cart tests."""
        self.user = SiteUser.objects.create_user(**TEST_USER_DATA, is_active=True)
        
        # Product setup
        category = ProductCategory.objects.create(name='Apparel')
        brand = Brand.objects.create(name='TestBrand')
        colour = Colour.objects.create(colour_name='Blue')
        size_s = SizeOption.objects.create(size_name='S')
        size_m = SizeOption.objects.create(size_name='M')
        
        product = Product.objects.create(name='Test Polo', category=category, brand=brand)
        product_item = ProductItem.objects.create(product=product, colour=colour, sku_base='TEST-POLO-BLUE', original_price=50.00)
        
        self.variation_s = ProductVariation.objects.create(product_item=product_item, size=size_s, qty_in_stock=20)
        self.variation_m = ProductVariation.objects.create(product_item=product_item, size=size_m, qty_in_stock=20)

        self.login_url = reverse('token_obtain_pair')
        self.cart_url = reverse('cart-list')

    def test_login_merges_guest_cart_to_empty_user_cart(self):
        """
        Test that a guest's cart is reassigned to them upon logging in if they don't have a cart.
        """
        # 1. Create a guest cart and add an item
        guest_client = APIClient()
        guest_client.post(self.cart_url, {'product_variation': self.variation_s.id, 'qty': 2}, format='json')
        
        self.assertEqual(ShoppingCart.objects.count(), 1)
        guest_cart = ShoppingCart.objects.first()
        self.assertIsNone(guest_cart.user)
        self.assertIsNotNone(guest_cart.session_key)

        # 2. Log in as the user
        login_data = {'email': self.user.email, 'password': TEST_USER_DATA['password']}
        guest_client.post(self.login_url, login_data, format='json')

        # 3. Verify the cart has been merged
        self.assertEqual(ShoppingCart.objects.count(), 1)
        user_cart = ShoppingCart.objects.first()
        self.assertEqual(user_cart.user, self.user)
        self.assertIsNone(user_cart.session_key)
        self.assertEqual(user_cart.items.count(), 1)
        self.assertEqual(user_cart.items.first().qty, 2)

    def test_login_merges_guest_cart_into_existing_user_cart(self):
        """
        Test that a guest's cart items are merged into an existing user's cart upon login.
        """
        # 1. Create a cart for the authenticated user with an item
        user_cart = ShoppingCart.objects.create(user=self.user)
        ShoppingCartItem.objects.create(cart=user_cart, product_variation=self.variation_s, qty=1)
        
        # 2. Create a guest cart with a different item and an overlapping item
        guest_client = APIClient()
        guest_client.post(self.cart_url, {'product_variation': self.variation_s.id, 'qty': 2}, format='json') # Overlapping
        guest_client.post(self.cart_url, {'product_variation': self.variation_m.id, 'qty': 3}, format='json') # New item

        self.assertEqual(ShoppingCart.objects.count(), 2)

        # 3. Log in
        login_data = {'email': self.user.email, 'password': TEST_USER_DATA['password']}
        guest_client.post(self.login_url, login_data, format='json')

        # 4. Verify the merge
        self.assertEqual(ShoppingCart.objects.count(), 1, "Guest cart should have been deleted.")
        
        user_cart.refresh_from_db()
        self.assertEqual(user_cart.items.count(), 2, "Cart should have two distinct items.")
        
        item_s = user_cart.items.get(product_variation=self.variation_s)
        item_m = user_cart.items.get(product_variation=self.variation_m)

        self.assertEqual(item_s.qty, 3, "Quantities of overlapping item should be summed (1 + 2).")
        self.assertEqual(item_m.qty, 3, "New item should be added with its quantity.")

    def test_login_with_no_guest_cart(self):
        """
        Test that logging in without a guest cart does not create a cart or cause errors.
        """
        self.assertEqual(ShoppingCart.objects.count(), 0)
        
        login_data = {'email': self.user.email, 'password': TEST_USER_DATA['password']}
        response = self.client.post(self.login_url, login_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ShoppingCart.objects.count(), 0, "No cart should be created just by logging in.")

        # Viewing the cart after logging in should create one
        self.client.force_authenticate(user=self.user)
        self.client.get(self.cart_url)
        self.assertEqual(ShoppingCart.objects.count(), 1)
        self.assertEqual(ShoppingCart.objects.first().user, self.user)

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
        # The response is paginated, so we check the 'results' list
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['address']['city'], 'Anytown')

    def test_unauthenticated_access_fails(self):
        """Ensure unauthenticated users cannot access protected profile endpoints."""
        # Clear authentication credentials
        self.client.credentials()
        
        detail_url = reverse('user-detail')
        address_url = reverse('user-address-list')

        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(address_url).status_code, status.HTTP_401_UNAUTHORIZED)
