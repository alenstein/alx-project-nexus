from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import SiteUser
from product.models import Product, ProductCategory, Brand, Colour, SizeOption, ProductItem, ProductVariation

class CartAPITests(APITestCase):
    """
    End-to-end tests for the Shopping Cart API endpoints.
    """
    def setUp(self):
        """Set up users, products, and other necessary data for cart tests."""
        # User 1 (will be authenticated for most tests)
        self.user1 = SiteUser.objects.create_user(username='user1', email='user1@example.com', password='password123', is_active=True)
        
        # User 2 (to test security isolation)
        self.user2 = SiteUser.objects.create_user(username='user2', email='user2@example.com', password='password123', is_active=True)

        # Authenticate as User 1 by default
        self.client.force_authenticate(user=self.user1)

        # Create a product with variations
        category = ProductCategory.objects.create(name='Apparel')
        brand = Brand.objects.create(name='TestBrand')
        colour = Colour.objects.create(colour_name='Green')
        size_m = SizeOption.objects.create(size_name='M')
        
        product = Product.objects.create(name='Test T-Shirt', category=category, brand=brand)
        product_item = ProductItem.objects.create(product=product, colour=colour, sku_base='TEST-SHIRT-GREEN', original_price=25.00)
        
        self.variation_m = ProductVariation.objects.create(product_item=product_item, size=size_m, qty_in_stock=10)

    def test_unauthenticated_user_cannot_access_cart(self):
        """Ensure unauthenticated users receive a 401 Unauthorized error."""
        self.client.force_authenticate(user=None)
        url = reverse('cart-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_view_empty_cart_creates_it(self):
        """Test that viewing the cart for a new user creates an empty cart."""
        url = reverse('cart-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_price'], '0.00')
        self.assertEqual(response.data['items'], [])

    def test_add_item_to_cart(self):
        """Test adding a new product variation to the cart."""
        url = reverse('cart-list')
        data = {'product_variation': self.variation_m.id, 'qty': 2}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['total_price'], '50.00')
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['product_name'], 'Test T-Shirt')

    def test_add_existing_item_updates_quantity(self):
        """Test that adding an existing item increases its quantity."""
        url = reverse('cart-list')
        # Add the item first
        self.client.post(url, {'product_variation': self.variation_m.id, 'qty': 1}, format='json')
        
        # Add the same item again
        response = self.client.post(url, {'product_variation': self.variation_m.id, 'qty': 2}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['qty'], 3) # 1 + 2 = 3
        self.assertEqual(response.data['total_price'], '75.00') # 3 * 25.00

    def test_cannot_add_more_than_stock(self):
        """Test that adding an item fails if the quantity exceeds stock."""
        url = reverse('cart-list')
        data = {'product_variation': self.variation_m.id, 'qty': 11} # Stock is 10
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check for the standard DRF error format
        self.assertIn('non_field_errors', response.data['errors'])
        self.assertIn('Only 10 items in stock', str(response.data['errors']['non_field_errors']))

    def test_update_cart_item_quantity(self):
        """Test updating the quantity of an item already in the cart."""
        # Add an item first
        post_url = reverse('cart-list')
        self.client.post(post_url, {'product_variation': self.variation_m.id, 'qty': 2}, format='json')
        
        # Get the ID of the created cart item
        list_response = self.client.get(post_url)
        cart_item_id = list_response.data['items'][0]['id']

        # Update the quantity
        update_url = reverse('cart-detail', kwargs={'pk': cart_item_id})
        response = self.client.patch(update_url, {'qty': 4}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['qty'], 4)
        self.assertEqual(response.data['total_price'], '100.00')

    def test_remove_item_from_cart(self):
        """Test deleting an item from the cart."""
        # Add an item
        url = reverse('cart-list')
        self.client.post(url, {'product_variation': self.variation_m.id, 'qty': 1}, format='json')
        
        cart_item_id = self.client.get(url).data['items'][0]['id']

        # Delete the item
        delete_url = reverse('cart-detail', kwargs={'pk': cart_item_id})
        response = self.client.delete(delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify the cart is now empty
        list_response = self.client.get(url)
        self.assertEqual(len(list_response.data['items']), 0)
        self.assertEqual(list_response.data['total_price'], '0.00')

    def test_user_cannot_access_another_users_cart_item(self):
        """Test that a user cannot update or delete another user's cart item."""
        # Add an item to User 1's cart
        url = reverse('cart-list')
        self.client.post(url, {'product_variation': self.variation_m.id, 'qty': 1}, format='json')
        cart_item_id = self.client.get(url).data['items'][0]['id']

        # Authenticate as User 2
        self.client.force_authenticate(user=self.user2)

        # Try to delete User 1's cart item
        delete_url = reverse('cart-detail', kwargs={'pk': cart_item_id})
        response = self.client.delete(delete_url)

        # Should fail with 404 because the item is not in User 2's cart
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
