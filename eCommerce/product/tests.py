from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Product, ProductCategory, Brand, Colour, SizeOption, ProductItem, ProductImage, ProductVariation
from decimal import Decimal

class ProductModelTests(APITestCase):
    """
    Tests for the product data models to ensure relationships and properties work correctly.
    """
    def setUp(self):
        """Set up a standard set of product data for model tests."""
        self.category = ProductCategory.objects.create(name='Footwear')
        self.brand = Brand.objects.create(name='Nike')
        self.colour_red = Colour.objects.create(colour_name='Red')
        self.size_10 = SizeOption.objects.create(size_name='10', sort_order=1)
        
        self.product = Product.objects.create(
            name='Air Max',
            description='A classic shoe.',
            category=self.category,
            brand=self.brand
        )
        self.product_item_red = ProductItem.objects.create(
            product=self.product,
            colour=self.colour_red,
            sku_base='NIKE-AIRMAX-RED',
            original_price=150.00,
            sale_price=120.00
        )
        ProductVariation.objects.create(
            product_item=self.product_item_red,
            size=self.size_10,
            qty_in_stock=20
        )

    def test_product_item_price_property(self):
        """Test that the `price` property returns the sale price if available."""
        self.assertEqual(self.product_item_red.price, Decimal('120.00'))
        
        # Test fallback to original price
        self.product_item_red.sale_price = None
        self.product_item_red.save()
        self.assertEqual(self.product_item_red.price, Decimal('150.00'))

class ProductAPITests(APITestCase):
    """
    End-to-end tests for the public-facing Product API endpoints.
    """
    def setUp(self):
        """Set up a rich dataset for testing the API."""
        # Categories and Brands
        self.cat_footwear = ProductCategory.objects.create(name='Footwear')
        self.cat_apparel = ProductCategory.objects.create(name='Apparel')
        self.brand_nike = Brand.objects.create(name='Nike')
        self.brand_adidas = Brand.objects.create(name='Adidas')

        # Colors and Sizes
        self.colour_red = Colour.objects.create(colour_name='Red')
        self.colour_blue = Colour.objects.create(colour_name='Blue')
        self.size_10 = SizeOption.objects.create(size_name='10')
        self.size_11 = SizeOption.objects.create(size_name='11')

        # Product 1: Nike Air Max (Red, Blue) - Lowest price 150
        self.prod_airmax = Product.objects.create(name='Nike Air Max', category=self.cat_footwear, brand=self.brand_nike, description='A classic shoe')
        item_airmax_red = ProductItem.objects.create(product=self.prod_airmax, colour=self.colour_red, sku_base='NIKE-AIRMAX-RED', original_price=150.00)
        ProductImage.objects.create(product_item=item_airmax_red, image_filename='airmax_red.jpg', is_default=True)
        ProductVariation.objects.create(product_item=item_airmax_red, size=self.size_10, qty_in_stock=10)
        
        item_airmax_blue = ProductItem.objects.create(product=self.prod_airmax, colour=self.colour_blue, sku_base='NIKE-AIRMAX-BLUE', original_price=155.00)
        ProductImage.objects.create(product_item=item_airmax_blue, image_filename='airmax_blue.jpg', is_default=True)

        # Product 2: Adidas Ultraboost (Red) - Price 180
        self.prod_ultraboost = Product.objects.create(name='Adidas Ultraboost', category=self.cat_footwear, brand=self.brand_adidas, description='A comfy runner')
        item_ultra_red = ProductItem.objects.create(product=self.prod_ultraboost, colour=self.colour_red, sku_base='ADIDAS-ULTRA-RED', original_price=180.00)
        ProductImage.objects.create(product_item=item_ultra_red, image_filename='ultraboost_red.jpg', is_default=True)

        # Product 3: Nike T-Shirt (Apparel) - Price 40
        self.prod_tshirt = Product.objects.create(name='Nike Dri-FIT T-Shirt', category=self.cat_apparel, brand=self.brand_nike, description='A training shirt')
        item_tshirt_blue = ProductItem.objects.create(product=self.prod_tshirt, colour=self.colour_blue, sku_base='NIKE-TSHIRT-BLUE', original_price=40.00)
        ProductImage.objects.create(product_item=item_tshirt_blue, image_filename='tshirt_blue.jpg', is_default=True)

    def test_list_products_pagination(self):
        """Ensure product list is paginated correctly."""
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

    def test_list_serializer_content(self):
        """Verify the content of the lightweight ProductListSerializer."""
        url = reverse('product-list')
        response = self.client.get(url)
        
        airmax_data = next((p for p in response.data['results'] if p['name'] == 'Nike Air Max'), None)
        self.assertIsNotNone(airmax_data)
        self.assertEqual(airmax_data['brand'], 'Nike')
        self.assertEqual(airmax_data['price'], '150.00') # Serializer converts Decimal to string
        self.assertTrue('airmax_red.jpg' in airmax_data['image'])

    def test_detail_serializer_content(self):
        """Verify the content of the heavy ProductDetailSerializer."""
        url = reverse('product-detail', kwargs={'id': self.prod_airmax.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['name'], 'Nike Air Max')
        self.assertEqual(data['brand']['name'], 'Nike')
        self.assertEqual(len(data['items']), 2)
        
        red_item = next((i for i in data['items'] if i['colour'] == 'Red'), None)
        self.assertIsNotNone(red_item)
        self.assertEqual(len(red_item['variations']), 1)
        self.assertEqual(red_item['variations'][0]['size'], '10')

    def test_filtering_by_category(self):
        """Test if filtering by category name works."""
        url = reverse('product-list') + '?category=Apparel'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Nike Dri-FIT T-Shirt')

    def test_filtering_by_brand(self):
        """Test if filtering by brand name works."""
        url = reverse('product-list') + '?brand=Adidas'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Adidas Ultraboost')

    def test_filtering_by_price_range(self):
        """Test if filtering by min_price and max_price works."""
        url = reverse('product-list') + '?min_price=100&max_price=160'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Nike Air Max')

    def test_sorting_by_price(self):
        """Test if sorting by the annotated price works."""
        # Ascending order
        url = reverse('product-list') + '?ordering=price'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [p['price'] for p in response.data['results']]
        self.assertEqual(prices, ['40.00', '150.00', '180.00'])

        # Descending order
        url = reverse('product-list') + '?ordering=-price'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [p['price'] for p in response.data['results']]
        self.assertEqual(prices, ['180.00', '150.00', '40.00'])

    def test_searching_by_name(self):
        """Test if searching by product name works."""
        url = reverse('product-list') + '?search=ultraboost'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Adidas Ultraboost')

    def test_404_for_nonexistent_product(self):
        """Test that a 404 is returned for a product ID that does not exist."""
        url = reverse('product-detail', kwargs={'id': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('errors', response.data)
        self.assertIn('detail', response.data['errors'])
