from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

class NEW_WholesaleDiscountConfig(models.Model):
    """
    NEW: Configurable wholesale discount thresholds
    Simple system: Above X amount → Y% discount
    """
    name = models.CharField(max_length=100, help_text="Configuration name")
    
    # Threshold amounts
    threshold_1 = models.DecimalField(
        max_digits=10, decimal_places=2, default=500.00,
        help_text="First threshold amount (e.g., $500)"
    )
    discount_1 = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00,
        help_text="First discount percentage (e.g., 10%)"
    )
    
    threshold_2 = models.DecimalField(
        max_digits=10, decimal_places=2, default=1000.00,
        help_text="Second threshold amount (e.g., $1000)"
    )
    discount_2 = models.DecimalField(
        max_digits=5, decimal_places=2, default=15.00,
        help_text="Second discount percentage (e.g., 15%)"
    )
    
    threshold_3 = models.DecimalField(
        max_digits=10, decimal_places=2, default=2000.00,
        help_text="Third threshold amount (e.g., $2000)"
    )
    discount_3 = models.DecimalField(
        max_digits=5, decimal_places=2, default=20.00,
        help_text="Third discount percentage (e.g., 20%)"
    )
    
    threshold_4 = models.DecimalField(
        max_digits=10, decimal_places=2, default=2500.00,
        help_text="Fourth threshold amount (e.g., $2500)"
    )
    discount_4 = models.DecimalField(
        max_digits=5, decimal_places=2, default=25.00,
        help_text="Fourth discount percentage (e.g., 25%)"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Wholesale Discount Configuration"
        verbose_name_plural = "Wholesale Discount Configurations"
    
    def __str__(self):
        return f"{self.name} - Active: {self.is_active}"
    
    def get_discount_for_amount(self, amount):
        """
        Get the appropriate discount percentage for a given amount
        Returns the highest applicable discount
        """
        if amount >= self.threshold_4:
            return self.discount_4
        elif amount >= self.threshold_3:
            return self.discount_3
        elif amount >= self.threshold_2:
            return self.discount_2
        elif amount >= self.threshold_1:
            return self.discount_1
        else:
            return Decimal('0.00')

class NEW_WholesaleUser(models.Model):
    """
    NEW: Simplified wholesale user model
    No more tiers - just wholesale status
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='wholesale_profile'
    )
    is_wholesale = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_wholesale_users'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Admin notes about this wholesale user")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Wholesale User"
        verbose_name_plural = "Wholesale Users"
    
    def __str__(self):
        return f"{self.user.username} - Wholesale: {self.is_wholesale}"

class NEW_WholesaleRequest(models.Model):
    """
    NEW: Wholesale account request model
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wholesale_requests')
    business_name = models.CharField(max_length=200)
    business_type = models.CharField(
        max_length=100, 
        choices=[
            ('retailer', 'Retailer'),
            ('distributor', 'Distributor'),
            ('reseller', 'Reseller'),
            ('contractor', 'Contractor'),
            ('nonprofit', 'Non-Profit Organization'),
            ('other', 'Other')
        ],
        help_text="Type of business"
    )
    tax_id = models.CharField(max_length=50, blank=True, help_text="Tax ID or EIN")
    website = models.URLField(blank=True, help_text="Business website")
    expected_monthly_volume = models.TextField(help_text="Expected monthly order volume")
    reason = models.TextField(help_text="Why do you need wholesale access?")
    documents = models.FileField(upload_to='wholesale_documents/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_wholesale_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, help_text="Admin review notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Wholesale Request"
        verbose_name_plural = "Wholesale Requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.business_name} ({self.status})"

class NEW_WholesaleDiscount(models.Model):
    """
    NEW: Track wholesale discounts applied to orders
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    order = models.ForeignKey('cart.Order', on_delete=models.CASCADE, related_name='wholesale_discounts')
    wholesale_user = models.ForeignKey(NEW_WholesaleUser, on_delete=models.CASCADE)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=5, decimal_places=2, help_text="Discount percentage or amount")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Actual discount amount applied")
    order_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Order amount before discount")
    applied_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Wholesale Discount"
        verbose_name_plural = "Wholesale Discounts"
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"Order #{self.order.id} - {self.discount_amount} discount"