from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from users.models import SiteUser
from product.models import Product, ProductCategory, Brand, Colour, SizeOption, ProductItem, ProductVariation
from .models import ShoppingCart

class CartAPITests(APITestCase):
    """
    End-to-end tests for the Shopping Cart API endpoints, covering both authenticated and guest users.
    """
    def setUp(self):
        """Set up users, products, and other necessary data for cart tests."""
        self.user = SiteUser.objects.create_user(username='testuser', email='test@example.com', password='password123', is_active=True)
        
        # Product setup
        category = ProductCategory.objects.create(name='Apparel')
        brand = Brand.objects.create(name='TestBrand')
        colour = Colour.objects.create(colour_name='Green')
        size_m = SizeOption.objects.create(size_name='M')
        size_l = SizeOption.objects.create(size_name='L')
        
        product = Product.objects.create(name='Test T-Shirt', category=category, brand=brand)
        product_item = ProductItem.objects.create(product=product, colour=colour, sku_base='TEST-SHIRT-GREEN', original_price=25.00)
        
        self.variation_m = ProductVariation.objects.create(product_item=product_item, size=size_m, qty_in_stock=10)
        self.variation_l = ProductVariation.objects.create(product_item=product_item, size=size_l, qty_in_stock=5)

    # --- Guest User Tests ---

    def test_guest_can_view_empty_cart(self):
        """Test that a guest user can view their cart, which is created on first view."""
        url = reverse('cart-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_price'], '0.00')
        self.assertTrue('session_key' in response.data)
        self.assertEqual(response.data['items'], [])

    def test_guest_can_add_item_to_cart(self):
        """Test a guest user can add an item to their cart."""
        url = reverse('cart-list')
        data = {'product_variation': self.variation_m.id, 'qty': 2}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['total_price'], '50.00')
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['product_name'], 'Test T-Shirt')
        
        # Verify a cart was created with a session key
        self.assertTrue(ShoppingCart.objects.filter(session_key=self.client.session.session_key, user=None).exists())

    def test_guest_cart_is_persistent_across_requests(self):
        """Test that a guest's cart persists across multiple requests using the same client."""
        url = reverse('cart-list')
        # First request
        self.client.post(url, {'product_variation': self.variation_m.id, 'qty': 1}, format='json')
        # Second request
        response = self.client.post(url, {'product_variation': self.variation_l.id, 'qty': 2}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['items']), 2)
        self.assertEqual(response.data['total_price'], '75.00') # 25.00 * 1 + 25.00 * 2

    def test_different_guests_have_different_carts(self):
        """Test that two different guest clients have isolated carts."""
        guest1_client = APIClient()
        guest2_client = APIClient()
        url = reverse('cart-list')

        # Guest 1 adds an item
        guest1_client.post(url, {'product_variation': self.variation_m.id, 'qty': 1}, format='json')
        
        # Guest 2's cart should be empty
        response2 = guest2_client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data['items']), 0)

        # Guest 1's cart should have one item
        response1 = guest1_client.get(url)
        self.assertEqual(len(response1.data['items']), 1)

    def test_guest_can_update_cart_item(self):
        """Test a guest can update an item quantity in their cart."""
        url = reverse('cart-list')
        self.client.post(url, {'product_variation': self.variation_m.id, 'qty': 1}, format='json')
        
        cart_item_id = self.client.get(url).data['items'][0]['id']
        update_url = reverse('cart-detail', kwargs={'pk': cart_item_id})
        response = self.client.patch(update_url, {'qty': 5}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'][0]['qty'], 5)
        self.assertEqual(response.data['total_price'], '125.00')

    def test_guest_can_remove_item_from_cart(self):
        """Test a guest can remove an item from their cart."""
        url = reverse('cart-list')
        self.client.post(url, {'product_variation': self.variation_m.id, 'qty': 1}, format='json')
        cart_item_id = self.client.get(url).data['items'][0]['id']

        delete_url = reverse('cart-detail', kwargs={'pk': cart_item_id})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify cart is now empty
        list_response = self.client.get(url)
        self.assertEqual(len(list_response.data['items']), 0)

    # --- Authenticated User Tests (Regression) ---

    def test_authenticated_user_can_add_to_cart(self):
        """Test that a logged-in user can still add items to their cart."""
        self.client.force_authenticate(user=self.user)
        url = reverse('cart-list')
        data = {'product_variation': self.variation_m.id, 'qty': 3}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['qty'], 3)
        
        # Verify a cart was created for the user
        self.assertTrue(ShoppingCart.objects.filter(user=self.user).exists())

    def test_add_existing_item_updates_quantity_for_auth_user(self):
        """Test that adding an existing item increases its quantity for an authenticated user."""
        self.client.force_authenticate(user=self.user)
        url = reverse('cart-list')
        self.client.post(url, {'product_variation': self.variation_m.id, 'qty': 1}, format='json')
        response = self.client.post(url, {'product_variation': self.variation_m.id, 'qty': 2}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['qty'], 3)
        self.assertEqual(response.data['total_price'], '75.00')

    def test_cannot_add_more_than_stock_for_auth_user(self):
        """Test stock validation for an authenticated user."""
        self.client.force_authenticate(user=self.user)
        url = reverse('cart-list')
        data = {'product_variation': self.variation_m.id, 'qty': 11} # Stock is 10
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Not enough stock. Only 10 items available.', str(response.data))
