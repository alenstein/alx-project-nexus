import random
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db import transaction
from product.models import (
    ProductCategory,
    Brand,
    Colour,
    SizeOption,
    Product,
    ProductItem,
    ProductImage,
    ProductVariation,
)

# --- Configuration ---
IMAGE_PROVIDER_URL = "https://picsum.photos/800/800"
MIN_PRODUCT_COUNT = 10  # The script will run if there are fewer than this many products.

# --- Sample Data ---
CATEGORIES = ["T-Shirts", "Hoodies", "Jeans", "Sneakers", "Hats"]
BRANDS = ["Nike", "Adidas", "Puma", "Levi's", "Vans"]
COLOURS = ["Black", "White", "Red", "Blue", "Grey"]
SIZES = ["XS", "S", "M", "L", "XL"]
PRODUCT_TEMPLATES = [
    {"name": "Classic Crewneck", "category": "T-Shirts"},
    {"name": "Graphic Print Tee", "category": "T-Shirts"},
    {"name": "Pullover Hoodie", "category": "Hoodies"},
    {"name": "Zip-Up Hoodie", "category": "Hoodies"},
    {"name": "Slim Fit Jeans", "category": "Jeans"},
    {"name": "Straight Leg Jeans", "category": "Jeans"},
    {"name": "Running Shoes", "category": "Sneakers"},
    {"name": "High-Top Sneakers", "category": "Sneakers"},
    {"name": "Baseball Cap", "category": "Hats"},
    {"name": "Beanie", "category": "Hats"},
]

class Command(BaseCommand):
    help = "Seeds the database with products, but only if the database is empty."

    @transaction.atomic
    def handle(self, *args, **options):
        # --- Check if the database is already seeded ---
        if Product.objects.count() >= MIN_PRODUCT_COUNT:
            self.stdout.write(self.style.SUCCESS(f"Database already contains {Product.objects.count()} products. Seeding is not required."))
            return

        self.stdout.write(self.style.SUCCESS("--- Starting Database Seeding ---"))

        # --- Clean Up Old Data (for a clean slate) ---
        self.stdout.write("Clearing old product data...")
        Product.objects.all().delete()
        ProductCategory.objects.all().delete()
        Brand.objects.all().delete()
        Colour.objects.all().delete()
        SizeOption.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Old data cleared."))

        # --- Create Core Attributes ---
        self.stdout.write("Creating categories, brands, colours, and sizes...")
        category_objs = [ProductCategory.objects.create(name=name) for name in CATEGORIES]
        brand_objs = [Brand.objects.create(name=name) for name in BRANDS]
        colour_objs = [Colour.objects.create(colour_name=name) for name in COLOURS]
        size_objs = [SizeOption.objects.create(size_name=name) for name in SIZES]
        self.stdout.write(self.style.SUCCESS("Core attributes created."))

        # --- Create Products and Variations ---
        self.stdout.write("Creating products and downloading images...")
        for template in PRODUCT_TEMPLATES:
            product_brand = random.choice(brand_objs)
            product = Product.objects.create(
                name=template["name"],
                category=random.choice([c for c in category_objs if c.name == template["category"]]),
                brand=product_brand,
                description=f"A high-quality {template['name']} from {product_brand.name}.",
            )

            product_colour = random.choice(colour_objs)
            product_item = ProductItem.objects.create(
                product=product,
                colour=product_colour,
                sku_base=f"{product.brand.name.upper()[:3]}-{product.name.replace(' ', '').upper()[:5]}-{product_colour.colour_name.upper()[:3]}",
                original_price=round(random.uniform(20.0, 100.0), 2),
            )

            try:
                response = requests.get(IMAGE_PROVIDER_URL, stream=True, timeout=15)
                if response.status_code == 200:
                    image_name = f"{product_item.sku_base}_{random.randint(1000, 9999)}.jpg"
                    product_image = ProductImage(product_item=product_item, is_default=True)
                    product_image.image_filename.save(image_name, ContentFile(response.content), save=True)
                    self.stdout.write(f"  - Image downloaded for {product.name} ({product_colour.colour_name})")
                else:
                    self.stdout.write(self.style.WARNING(f"  - Failed to download image for {product.name}. Status: {response.status_code}"))
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"  - Error downloading image for {product.name}: {e}"))

            for size in random.sample(size_objs, k=random.randint(2, len(SIZES))):
                ProductVariation.objects.create(
                    product_item=product_item,
                    size=size,
                    qty_in_stock=random.randint(5, 50),
                )
        
        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully created {len(PRODUCT_TEMPLATES)} products."))
        self.stdout.write(self.style.SUCCESS("--- Database Seeding Complete ---"))
