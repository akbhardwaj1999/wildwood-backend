from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Address, Order, OrderItem, Payment, Coupon, ShippingCost
from galleryItem.models import Variant
from galleryItem.serializers import VariantSerializer

User = get_user_model()


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for Address model"""
    address_type_display = serializers.CharField(source='get_address_type_display', read_only=True)
    
    class Meta:
        model = Address
        fields = (
            'id', 'user', 'first_name', 'last_name', 'email_address', 'phone_number',
            'company_name', 'address_line_1', 'address_line_2', 'country', 'state',
            'city', 'zip_code', 'address_type', 'address_type_display', 'default'
        )
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model"""
    variant = VariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=Variant.objects.all(), source='variant', write_only=True, required=False
    )
    item_price = serializers.SerializerMethodField()
    total_item_price = serializers.SerializerMethodField()
    product_title = serializers.CharField(source='variant.product.title', read_only=True)
    variant_title = serializers.CharField(source='variant.title', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = (
            'id', 'order', 'variant', 'variant_id', 'special_price', 'quantity',
            'item_price', 'total_item_price', 'product_title', 'variant_title'
        )
        read_only_fields = ('id',)
    
    def get_item_price(self, obj):
        """Get formatted item price"""
        return obj.get_item_price()
    
    def get_total_item_price(self, obj):
        """Get formatted total item price"""
        return obj.get_total_item_price()


class OrderItemCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating OrderItem (simplified)"""
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=Variant.objects.filter(active=True), source='variant'
    )
    
    class Meta:
        model = OrderItem
        fields = ('variant_id', 'quantity')
    
    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model"""
    items = OrderItemSerializer(many=True, read_only=True)
    billing_address = AddressSerializer(read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    subtotal = serializers.SerializerMethodField()
    coupon_discount_amount = serializers.SerializerMethodField()
    coupon_code = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id', 'user', 'user_email', 'user_username', 'reference_number',
            'start_date', 'last_updated', 'ordered_date', 'ordered', 'status',
            'status_display', 'billing_address', 'shipping_address',
            'total_shipping_cost', 'coupon', 'coupon_code', 'tax_amount', 'wholesale_discount',
            'is_tax_exempt', 'subtotal', 'coupon_discount_amount', 'total',
            'items', 'abandoned_email_sent', 'abandoned_email_count'
        )
        read_only_fields = (
            'id', 'reference_number', 'start_date', 'last_updated',
            'ordered_date', 'subtotal', 'coupon_discount_amount', 'total', 'coupon_code'
        )

    def get_subtotal(self, obj):
        """Get formatted subtotal"""
        return obj.get_subtotal()
    
    def get_coupon_discount_amount(self, obj):
        """Get formatted coupon discount amount"""
        return obj.get_coupon_discount_amount()
    
    def get_coupon_code(self, obj):
        """Get coupon code if coupon is applied"""
        if obj.coupon:
            return obj.coupon.code
        return None
    
    def get_total(self, obj):
        """Get formatted total"""
        return obj.get_total()


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Order (simplified)"""
    
    class Meta:
        model = Order
        fields = ('user',)


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    order_reference = serializers.CharField(source='order.reference_number', read_only=True)
    
    class Meta:
        model = Payment
        fields = (
            'id', 'order', 'order_reference', 'payment_method', 'payment_method_display',
            'timestamp', 'successful', 'amount', 'raw_response', 'transaction_id', 'reference_number'
        )
        read_only_fields = ('id', 'timestamp', 'reference_number')


class CreatePaymentSerializer(serializers.Serializer):
    """Serializer for creating payment"""
    payment_method = serializers.ChoiceField(choices=Payment.PAYMENT_CHOICES)
    address_id = serializers.IntegerField(required=False, help_text="Address ID for shipping")
    # For Stripe
    stripe_token = serializers.CharField(required=False, allow_blank=True, help_text="Stripe payment token")
    # For PayPal
    paypal_order_id = serializers.CharField(required=False, allow_blank=True, help_text="PayPal order ID")


class CouponSerializer(serializers.ModelSerializer):
    """Serializer for Coupon model"""
    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)
    
    class Meta:
        model = Coupon
        fields = (
            'id', 'title', 'description', 'code', 'discount', 'discount_type',
            'discount_type_display', 'minimum_order_amount', 'single_use_per_user', 'active'
        )
        read_only_fields = ('id',)


class ShippingCostSerializer(serializers.ModelSerializer):
    """Serializer for ShippingCost model"""
    parameter_display = serializers.CharField(source='get_parameter_display', read_only=True)
    shipment_type_display = serializers.CharField(source='get_shipment_type_display', read_only=True)
    charges_display = serializers.CharField(source='get_charges', read_only=True)
    
    class Meta:
        model = ShippingCost
        fields = (
            'id', 'parameter', 'parameter_display', 'value_start', 'value_end',
            'shipment_type', 'shipment_type_display', 'charges', 'charges_display'
        )
        read_only_fields = ('id',)


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding item to cart"""
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=Variant.objects.filter(active=True)
    )
    quantity = serializers.IntegerField(min_value=1, default=1)
    
    def validate_variant(self, value):
        """Validate variant is active and in stock"""
        if not value.active:
            raise serializers.ValidationError("This variant is not available")
        return value
    
    def validate(self, data):
        """Validate variant is in stock"""
        variant = data.get('variant_id')
        quantity = data.get('quantity', 1)
        if variant and variant.quantity < quantity:
            raise serializers.ValidationError({
                'variant_id': f"Only {variant.quantity} items available in stock"
            })
        if variant and variant.quantity <= 0:
            raise serializers.ValidationError({
                'variant_id': "This variant is out of stock"
            })
        return data


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity"""
    quantity = serializers.IntegerField(min_value=1)


class ApplyCouponSerializer(serializers.Serializer):
    """Serializer for applying coupon"""
    code = serializers.CharField(max_length=20)
