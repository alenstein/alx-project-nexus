from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import ShoppingCart, ShoppingCartItem
from .serializers import ShoppingCartSerializer, CartItemWriteSerializer

def get_cart(request):
    """
    Helper function to get or create a cart for the current user (authenticated or anonymous).
    """
    if request.user.is_authenticated:
        cart, _ = ShoppingCart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, _ = ShoppingCart.objects.get_or_create(session_key=session_key, user=None)
    return cart

class CartViewSet(viewsets.ViewSet):
    """
    A ViewSet for viewing, adding, updating, and removing items from a shopping cart.
    - `list`: Retrieves the user's current cart.
    - `create`: Adds a new item to the cart or updates the quantity if it already exists.
    - `partial_update`: Updates the quantity of a specific cart item.
    - `destroy`: Removes a specific item from the cart.
    """
    permission_classes = [AllowAny]

    def list(self, request):
        """
        Retrieves the current user's shopping cart.
        """
        cart = get_cart(request)
        serializer = ShoppingCartSerializer(cart, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        """
        Adds a product variation to the cart.
        If the item is already in the cart, its quantity is increased.
        """
        cart = get_cart(request)
        serializer = CartItemWriteSerializer(data=request.data, context={'cart': cart})
        serializer.is_valid(raise_exception=True)
        
        product_variation = serializer.validated_data['product_variation']
        quantity = serializer.validated_data['qty']

        cart_item, created = ShoppingCartItem.objects.get_or_create(
            cart=cart,
            product_variation=product_variation,
            defaults={'qty': quantity}
        )

        if not created:
            cart_item.qty += quantity
            cart_item.save()

        # Re-validate stock after any quantity change
        if cart_item.qty > product_variation.qty_in_stock:
            # Raise a standard validation error
            raise serializers.ValidationError(
                f"Not enough stock. Only {product_variation.qty_in_stock} items available."
            )
        
        cart_serializer = ShoppingCartSerializer(cart, context={'request': request})
        return Response(cart_serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def partial_update(self, request, pk=None):
        """
        Updates the quantity of a specific item in the cart.
        """
        cart = get_cart(request)
        try:
            cart_item = ShoppingCartItem.objects.get(id=pk, cart=cart)
        except ShoppingCartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CartItemWriteSerializer(cart_item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        cart_serializer = ShoppingCartSerializer(cart, context={'request': request})
        return Response(cart_serializer.data)

    def destroy(self, request, pk=None):
        """
        Removes an item from the cart.
        """
        cart = get_cart(request)
        try:
            cart_item = ShoppingCartItem.objects.get(id=pk, cart=cart)
        except ShoppingCartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
