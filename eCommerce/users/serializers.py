from rest_framework import serializers
from .models import SiteUser, Address, Country, UserAddress
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from cart.models import ShoppingCart, ShoppingCartItem

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that checks if the user is active and merges carts on login.
    """
    def validate(self, attrs):
        # Default validation
        data = super().validate(attrs)

        # Check for active user
        if not self.user.is_active:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        # Merge guest cart with user cart
        request = self.context.get('request')
        if request and request.session.session_key:
            session_key = request.session.session_key
            try:
                guest_cart = ShoppingCart.objects.get(session_key=session_key, user=None)
                
                # Check if the user already has a cart
                try:
                    user_cart = ShoppingCart.objects.get(user=self.user)
                    # Merge items from guest_cart to user_cart
                    for guest_item in guest_cart.items.all():
                        user_item, created = ShoppingCartItem.objects.get_or_create(
                            cart=user_cart,
                            product_variation=guest_item.product_variation,
                            defaults={'qty': guest_item.qty}
                        )
                        if not created:
                            user_item.qty += guest_item.qty
                            user_item.save()
                    # Delete the guest cart after merging
                    guest_cart.delete()
                except ShoppingCart.DoesNotExist:
                    # No user cart exists, so just assign the guest cart to the user
                    guest_cart.user = self.user
                    guest_cart.session_key = None
                    guest_cart.save()

            except ShoppingCart.DoesNotExist:
                # No guest cart to merge
                pass

        return data

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration. Handles password validation and creation.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = SiteUser
        fields = ('email', 'username', 'first_name', 'last_name', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = SiteUser.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.is_active = False  # Deactivate account until email confirmation
        user.save()
        return user

class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying user details.
    """
    class Meta:
        model = SiteUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'phone_number', 'date_joined')
        read_only_fields = ('email', 'date_joined')

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'

class AddressSerializer(serializers.ModelSerializer):
    country = serializers.StringRelatedField(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), source='country', write_only=True)

    class Meta:
        model = Address
        fields = '__all__'

class UserAddressSerializer(serializers.ModelSerializer):
    address = AddressSerializer()

    class Meta:
        model = UserAddress
        fields = ('id', 'address', 'is_default')
        # Add ordering to fix pagination warning
        ordering = ['-is_default']


    def create(self, validated_data):
        address_data = validated_data.pop('address')
        address = Address.objects.create(**address_data)
        # The user is passed in from the view's perform_create method and is in validated_data
        user_address = UserAddress.objects.create(address=address, **validated_data)
        return user_address

    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)
        if address_data:
            # Update the nested Address instance
            Address.objects.filter(id=instance.address.id).update(**address_data)
        
        # Update the UserAddress instance
        instance.is_default = validated_data.get('is_default', instance.is_default)
        instance.save()
        return instance
