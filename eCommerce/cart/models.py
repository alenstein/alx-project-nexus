from django.db import models
from django.conf import settings
from product.models import ProductVariation

class ShoppingCart(models.Model):
    """
    The user's cart bucket. Can be associated with a logged-in user or an anonymous session.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='cart', 
        null=True, 
        blank=True
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Guest Cart (Session: {self.session_key or 'Unknown'})"

    @property
    def total_price(self):
        """Calculates total price of all items in cart."""
        total = sum(item.subtotal for item in self.items.all())
        return total

class ShoppingCartItem(models.Model):
    """
    Individual items in the cart.
    Links to ProductVariation to ensure we capture the specific Size.
    """
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name='items')
    # Linking to Variation (Tier 3) to capture Size + Color
    product_variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product_variation') # Prevent duplicate rows for same item

    def __str__(self):
        return f"{self.qty} x {self.product_variation}"

    @property
    def subtotal(self):
        """
        Calculates subtotal for this line item.
        Uses the helper property from ProductItem model.
        """
        price = self.product_variation.product_item.price
        return price * self.qty
