from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


from django.db import models
from django_countries.fields import CountryField


from django.db import models
from smart_selects.db_fields import ChainedForeignKey

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name"]

    def __str__(self):
        return self.name


class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "States"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.country.name})"


class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="cities", null=True, blank=True)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.state.name}"
    
    @property
    def country(self):
        """Get country through state"""
        return self.state.country
    
    def get_full_address(self):
        """Get complete address: City, State, Country"""
        return f"{self.name}, {self.state.name}, {self.state.country.name}"


class NEW_TaxRate(models.Model):
    """NEW: Tax rates for different countries, states, and cities"""

    TAX_TYPE_CHOICES = [
        ("sales", "Sales Tax"),
        ("use", "Use Tax"),
        ("excise", "Excise Tax"),
        ("property", "Property Tax"),
        ("income", "Income Tax"),
        ("other", "Other"),
    ]

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="tax_rates")
    state = ChainedForeignKey(
        State,
        chained_field="country",
        chained_model_field="country",
        show_all=False,
        auto_choose=True,
        sort=True,
        on_delete=models.CASCADE,
        related_name="tax_rates",
    )
    city = ChainedForeignKey(
        City,
        chained_field="state",
        chained_model_field="state",
        show_all=False,
        auto_choose=True,
        sort=True,
        on_delete=models.CASCADE,
        related_name="tax_rates",
        blank=False,
        null=False,
    )

    rate = models.DecimalField(max_digits=5, decimal_places=4, help_text="0.0875 = 8.75%")
    tax_type = models.CharField(max_length=50, choices=TAX_TYPE_CHOICES, default="sales")
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "NEW Tax Rate"
        verbose_name_plural = "NEW Tax Rates"
        ordering = ["country", "state", "city", "-effective_date"]

    def __str__(self):
        loc = self.country.name
        if self.state:
            loc += f", {self.state.name}"
        if self.city:
            loc += f", {self.city.name}"
        return f"{loc} - {self.rate * 100:.2f}% ({self.tax_type})"





# class NEW_TaxRate(models.Model):
#     """NEW: Tax rates for different US states, counties, and cities"""
    
#     # US State choices
#     STATE_CHOICES = [
#         ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'), ('CA', 'California'),
#         ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'), ('FL', 'Florida'), ('GA', 'Georgia'),
#         ('HI', 'Hawaii'), ('ID', 'Idaho'), ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'),
#         ('KS', 'Kansas'), ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
#         ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'), ('MO', 'Missouri'),
#         ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'), ('NH', 'New Hampshire'), ('NJ', 'New Jersey'),
#         ('NM', 'New Mexico'), ('NY', 'New York'), ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'),
#         ('OK', 'Oklahoma'), ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
#         ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'), ('VT', 'Vermont'),
#         ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'), ('WI', 'Wisconsin'), ('WY', 'Wyoming'),
#         ('DC', 'District of Columbia')
#     ]
    
#     # Tax type choices
#     TAX_TYPE_CHOICES = [
#         ('sales', 'Sales Tax'),
#         ('use', 'Use Tax'),
#         ('excise', 'Excise Tax'),
#         ('property', 'Property Tax'),
#         ('income', 'Income Tax'),
#         ('other', 'Other')
#     ]
    
#     state = models.CharField(max_length=2, choices=STATE_CHOICES, help_text="US state code (e.g., CA, NY, TX)")
#     county = models.CharField(max_length=100, blank=True, help_text="County name (optional)")
#     city = models.CharField(max_length=100, blank=True, help_text="City name (optional)")
#     rate = models.DecimalField(max_digits=5, decimal_places=4, help_text="Tax rate as decimal (0.0875 = 8.75%)")
#     tax_type = models.CharField(max_length=50, choices=TAX_TYPE_CHOICES, default='sales', help_text="Type of tax (sales, use, etc.)")
#     effective_date = models.DateField(help_text="Date when this rate becomes effective")
#     expiry_date = models.DateField(null=True, blank=True, help_text="Date when this rate expires (optional)")
#     is_active = models.BooleanField(default=True, help_text="Whether this rate is currently active")
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         verbose_name = "NEW Tax Rate"
#         verbose_name_plural = "NEW Tax Rates"
#         ordering = ['state', 'county', 'city', '-effective_date']

#     def __str__(self):
#         location = f"{self.state}"
#         if self.county:
#             location += f", {self.county}"
#         if self.city:
#             location += f", {self.city}"
#         return f"{location} - {self.rate}% ({self.tax_type})"

class NEW_TaxExemption(models.Model):
    """NEW: Tax exemption status for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tax_exemption')
    is_exempt = models.BooleanField(default=False, help_text="Whether user is tax exempt")
    exemption_type = models.CharField(max_length=50, choices=[
        ('resale', 'Resale Certificate'),
        ('nonprofit', 'Non-Profit Organization'),
        ('government', 'Government Entity'),
        ('other', 'Other')
    ], blank=True, help_text="Type of tax exemption")
    certificate_number = models.CharField(max_length=100, blank=True, help_text="Exemption certificate number")
    certificate_file = models.FileField(upload_to='tax_exemptions/', blank=True, help_text="Upload exemption certificate")
    effective_date = models.DateField(null=True, blank=True, help_text="Date exemption becomes effective")
    expiry_date = models.DateField(null=True, blank=True, help_text="Date exemption expires")
    admin_notes = models.TextField(blank=True, help_text="Admin notes about this exemption")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "NEW Tax Exemption"
        verbose_name_plural = "NEW Tax Exemptions"

    def __str__(self):
        return f"{self.user.username} - {'Exempt' if self.is_exempt else 'Not Exempt'}"

    @property
    def is_valid(self):
        """Check if exemption is currently valid"""
        if not self.is_exempt:
            return False
        
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.effective_date and self.effective_date > today:
            return False
        
        if self.expiry_date and self.expiry_date < today:
            return False
        
        return True

class NEW_TaxCalculation(models.Model):
    """NEW: Store tax calculations for orders"""
    order = models.ForeignKey('cart.Order', on_delete=models.CASCADE, related_name='tax_calculations')
    tax_rate = models.ForeignKey(NEW_TaxRate, on_delete=models.SET_NULL, null=True)
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount subject to tax")
    tax_rate_value = models.DecimalField(max_digits=5, decimal_places=4, help_text="Tax rate applied")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Calculated tax amount")
    is_exempt = models.BooleanField(default=False, help_text="Whether this calculation was exempt")
    exemption_reason = models.CharField(max_length=200, blank=True, help_text="Reason for exemption")
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "NEW Tax Calculation"
        verbose_name_plural = "NEW Tax Calculations"
        ordering = ['-calculated_at']

    def __str__(self):
        return f"Tax for Order #{self.order.id}: ${self.tax_amount}"

    def save(self, *args, **kwargs):
        # Auto-calculate tax amount
        if not self.tax_amount and self.taxable_amount and self.tax_rate_value:
            self.tax_amount = self.taxable_amount * self.tax_rate_value
        super().save(*args, **kwargs)