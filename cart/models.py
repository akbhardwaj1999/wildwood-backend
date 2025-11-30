import uuid

from django.contrib.auth import get_user_model
from django.db import models

# import from 2 levels above
from galleryItem.models import Variant, SpecialPrice

User = get_user_model()


class Address(models.Model):
    BILLING = 'B'
    SHIPPING = 'S'
    ADDRESS_CHOICES = (
        (BILLING, 'Billing'),
        (SHIPPING, 'Shipping'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email_address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=16)
    company_name = models.CharField(max_length=100, blank=True)
    address_line_1 = models.CharField(max_length=150)
    address_line_2 = models.CharField(max_length=150, blank=True)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_line_1}, {self.address_line_2}, {self.zip_code}, {self.city}, {self.state}, {self.country}"

    class Meta:
        verbose_name_plural = 'Addresses'

 
class OrderItem(models.Model):
    order = models.ForeignKey(
        "Order", related_name='items', on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    special_price = models.ForeignKey(SpecialPrice, blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.variant.product.title} x {self.variant.title}"

    def get_raw_item_price(self):
        if self.special_price: 
            return self.special_price.get_raw_special_price(self.variant)
        else:
            return self.variant.price

    def get_raw_total_item_price(self):
        return self.quantity * self.get_raw_item_price()

    def get_item_price(self):
        price = self.get_raw_item_price()
        return "{:.2f}".format(price)

    def get_total_item_price(self):
        price = self.get_raw_total_item_price()
        return "{:.2f}".format(price)


class Order(models.Model):
    NOT_FINALIZED = 'N'
    ORDERED = 'O'
    SHIPPED = 'S'
    DELIVERED = 'D'
    CANCELED = 'C'

    STATUS_CHOICES = (
        (NOT_FINALIZED, 'Not finalized yet'),
        (ORDERED, 'Not shipped yet'),
        (SHIPPED, 'Shipped'),
        (DELIVERED, 'Delivered'),
        (CANCELED, 'Canceled'),
    )

    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.CASCADE)
    reference_number = models.CharField(default=uuid.uuid4, max_length=36, unique=True)
    start_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True, help_text="Last time cart was modified")
    ordered_date = models.DateTimeField(blank=True, null=True)
    ordered = models.BooleanField(default=False)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=NOT_FINALIZED)

    billing_address = models.ForeignKey(
        Address, related_name='billing_address', blank=True, null=True, on_delete=models.SET_NULL)
    shipping_address = models.ForeignKey(
        Address, related_name='shipping_address', blank=True, null=True, on_delete=models.SET_NULL)

    total_shipping_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    coupon = models.ForeignKey('Coupon', blank=True, null=True, on_delete=models.SET_NULL)
    
    # NEW: Tax and wholesale fields
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="NEW: Tax amount for this order")
    wholesale_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="NEW: Wholesale discount amount")
    is_tax_exempt = models.BooleanField(default=False, help_text="NEW: Whether this order is tax exempt")
    
    # NEW: Abandoned cart email tracking
    abandoned_email_sent = models.BooleanField(default=False, help_text="Whether abandoned cart email has been sent")
    abandoned_email_sent_at = models.DateTimeField(null=True, blank=True, help_text="When abandoned cart email was sent")
    abandoned_email_count = models.IntegerField(default=0, help_text="Number of abandoned cart emails sent")
    recovery_link_clicked_at = models.DateTimeField(null=True, blank=True, help_text="When user clicked recovery link from email (delays next email)")

    def __str__(self):
        return self.reference_number

    def clear_discounts_and_shipping(self, request=None):
        """
        Zero out coupon + shipping for this open order and optionally
        clear the session flags that drive the UI.
        """
        updated = []
        if getattr(self, "coupon_id", None):
            self.coupon = None
            updated.append("coupon")
        if getattr(self, "total_shipping_cost", 0):
            self.total_shipping_cost = 0
            updated.append("total_shipping_cost")
        if updated:
            self.save(update_fields=updated)

        if request is not None:
            request.session.pop("coupon_applied_at", None)
            request.session.pop("shipping_cost", None)

    def get_raw_subtotal(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_raw_total_item_price()
        return total

    def get_subtotal(self):
        subtotal = self.get_raw_subtotal()
        return "{:.2f}".format(subtotal) if subtotal else "0.00"

    def get_raw_coupon_discount_amount(self):
        if self.coupon.discount_type == Coupon.DiscountType.FIXED_AMOUNT:
            return self.coupon.discount
        if self.coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
            return (self.coupon.discount / 100) * self.get_raw_subtotal()
        return 0

    def get_coupon_discount_amount(self):
        if self.coupon:
            coupon_discount_amount = self.get_raw_coupon_discount_amount()
            return "{:.2f}".format(coupon_discount_amount) if coupon_discount_amount else "0.00"
        else:
            return "0.00"

    def get_raw_total(self):
        from decimal import Decimal
        
        # Calculate subtotal after discounts
        subtotal = self.get_raw_subtotal()
        
        # Apply discounts - but NOT both coupon and wholesale together
        # Client requirement: No coupon combination with wholesale
        if self.wholesale_discount > 0:
            # If wholesale discount exists, use only wholesale discount
            subtotal -= self.wholesale_discount
        elif self.coupon:
            # If no wholesale discount, apply coupon discount
            subtotal -= self.get_raw_coupon_discount_amount()
        
        # Add tax on subtotal (after discounts, before shipping)
        # Note: Tax is only calculated on checkout page, not cart page
        total = subtotal + self.tax_amount
        
        # Add shipping cost (ensure it's Decimal)
        total += Decimal(str(self.total_shipping_cost))
        
        return total

    def get_total(self):
        total = self.get_raw_total()
        return "{:.2f}".format(total) if total else "0.00"
    
    # NEW: Get subtotal after wholesale discount but before tax
    def get_raw_subtotal_after_discounts(self):
        subtotal = self.get_raw_subtotal()
        if self.coupon:
            subtotal -= self.get_raw_coupon_discount_amount()
        subtotal -= self.wholesale_discount
        return subtotal
    
    def get_subtotal_after_discounts(self):
        subtotal = self.get_raw_subtotal_after_discounts()
        return "{:.2f}".format(subtotal) if subtotal else "0.00"
    
    def get_wholesale_discount_percentage(self):
        """Get wholesale discount percentage for display"""
        if self.wholesale_discount > 0:
            subtotal = self.get_raw_subtotal()
            if subtotal > 0:
                percentage = (self.wholesale_discount / subtotal) * 100
                return round(float(percentage), 1)
        return 0


class Payment(models.Model):
    PAYPAL = 'P'
    PAYMENT_CHOICES = (
        (PAYPAL, 'PayPal'),
    )

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=1, choices=PAYMENT_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)
    amount = models.FloatField()
    raw_response = models.TextField()

    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
        return f"PAYMENT-{self.order}-{self.pk}"


class ShippingCost(models.Model):
    VOLUME = 'V'
    WEIGHT = 'W'
    PARAMETER_CHOICES = (
        (VOLUME, "Volume"),
        (WEIGHT, "Weight"),
    )

    LOCAL = 'L'
    OTHER_CITY = 'OC'
    OTHER_STATE = 'OS'
    INTERNATIONAL = 'I'

    SHIPMENT_TYPE_CHOICES = (
        (LOCAL, "Local"),
        (OTHER_CITY, "Other City"),
        (OTHER_STATE, "Other State"),
        (INTERNATIONAL, "International"),
    )

    parameter = models.CharField(choices=PARAMETER_CHOICES, max_length=1)
    value_start = models.PositiveIntegerField()
    value_end = models.PositiveIntegerField()

    shipment_type = models.CharField(choices=SHIPMENT_TYPE_CHOICES, max_length=2)
    charges = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.get_parameter_display()}, {self.value_start}-{self.value_end}, {self.get_shipment_type_display()}, {self.charges}"

    def get_charges(self):
        return "{:.2f}".format(self.charges)


class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        FIXED_AMOUNT = 'fixed_amount', 'Fixed Amount'
        PERCENTAGE = 'percentage', 'Percentage'

    title = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    code = models.CharField(max_length=20, unique=True)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_type = models.CharField(choices=DiscountType.choices, max_length=15)
    minimum_order_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    single_use_per_user = models.BooleanField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
