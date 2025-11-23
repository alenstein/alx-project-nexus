from django.core.management.base import BaseCommand
from django.utils import timezone
from product.models import ProductVariation

class Command(BaseCommand):
    """
    A Django management command to check for low stock levels.
    This command can be run as a cron job.
    """
    help = 'Checks for product variations with low stock and sends a notification.'

    def handle(self, *args, **kwargs):
        # Define the threshold for what is considered "low stock".
        low_stock_threshold = 5

        # Find all product variations that are at or below the threshold.
        low_stock_items = ProductVariation.objects.filter(qty_in_stock__lte=low_stock_threshold)

        if low_stock_items.exists():
            self.stdout.write(self.style.WARNING(f"Found {low_stock_items.count()} items with low stock (<= {low_stock_threshold} units)."))
            
            for item in low_stock_items:
                self.stdout.write(
                    f"  - Product: {item.product_item.product.name}, "
                    f"Color: {item.product_item.colour.colour_name}, "
                    f"Size: {item.size.size_name}, "
                    f"Stock: {item.qty_in_stock}"
                )
            
            # --- Placeholder for actual notification logic ---
            # In a real application, you would send an email or a Slack notification here.
            # Example:
            # from django.core.mail import send_mail
            #
            # subject = "Low Stock Alert"
            # message = "The following items are running low on stock:\n"
            # for item in low_stock_items:
            #     message += f"- {item}\n"
            #
            # send_mail(subject, message, 'noreply@yourdomain.com', ['admin@yourdomain.com'])
            # -------------------------------------------------

        else:
            self.stdout.write(self.style.SUCCESS("No items with low stock found."))

        self.stdout.write(self.style.SUCCESS(f"Stock check completed at {timezone.now()}"))
