from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django import forms
from .models import NEW_TaxRate, NEW_TaxExemption, NEW_TaxCalculation, Country, State, City

class NEW_TaxRateForm(forms.ModelForm):
    """Custom form for TaxRate with smart_selects integration"""

    # Add percentage field for user-friendly input
    rate_percentage = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=True,
        help_text="Enter tax rate as percentage (e.g., 10.75 for 10.75%)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '10.75'})
    )

    class Meta:
        model = NEW_TaxRate
        fields = '__all__'
        widgets = {
            'rate': forms.HiddenInput(),  # Hide the decimal field, use percentage field instead
            'tax_type': forms.Select(attrs={'class': 'form-control'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make rate field not required since we'll set it in clean()
        self.fields['rate'].required = False
        # Make city field required (not optional)
        self.fields['city'].required = True
        self.fields['city'].blank = False
        # Convert decimal rate to percentage for display
        if self.instance and self.instance.pk and self.instance.rate:
            self.fields['rate_percentage'].initial = self.instance.rate * 100

    def clean(self):
        cleaned_data = super().clean()
        rate_percentage = cleaned_data.get('rate_percentage')

        if rate_percentage is not None:
            # Convert percentage to decimal
            cleaned_data['rate'] = rate_percentage / 100
        else:
            raise forms.ValidationError("Please enter tax rate percentage.")

        return cleaned_data

@admin.register(NEW_TaxRate)
class NEW_TaxRateAdmin(admin.ModelAdmin):
    """NEW: Admin interface for tax rates"""
    form = NEW_TaxRateForm
    list_display = [
        'country', 'state', 'city', 'rate_display', 'tax_type',
        'effective_date', 'expiry_date', 'is_active', 'created_at'
    ]
    list_filter = ['country', 'state', 'tax_type', 'is_active', 'effective_date']
    search_fields = ['country__name', 'state__name', 'city__name']
    ordering = ['state', 'city', '-effective_date']
    date_hierarchy = 'effective_date'

    fieldsets = (
        ('Location Information (ALL REQUIRED)', {
            'fields': ('country', 'state', 'city'),
            'description': 'All location fields are REQUIRED for proper tax calculation. Flow: Country → State → City. City is MANDATORY - tax rates are calculated at city level.'
        }),
        ('Tax Information', {
            'fields': ('rate_percentage', 'rate', 'tax_type'),
            'description': 'Enter tax rate as percentage (e.g., 10.75 for 10.75%). The system will automatically convert it to decimal format.'
        }),
        ('Validity Period', {
            'fields': ('effective_date', 'expiry_date', 'is_active')
        }),
    )

    class Media:
        js = (
            'admin/js/jquery.init.js',
            'smart-selects/admin/js/chainedfk.js',
            'smart-selects/admin/js/bindfields.js',
        )
        '''
        css = {
            'all': ('smart-selects/admin/css/chainedfk.css',)
        }
        '''

    def rate_display(self, obj):
        """Display rate as percentage"""
        return f"{obj.rate * 100:.2f}%"
    rate_display.short_description = 'Rate'
    rate_display.admin_order_field = 'rate'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

@admin.register(NEW_TaxExemption)
class NEW_TaxExemptionAdmin(admin.ModelAdmin):
    """NEW: Admin interface for tax exemptions"""
    list_display = [
        'user', 'is_exempt', 'exemption_type', 'certificate_number',
        'effective_date', 'expiry_date', 'is_valid_display', 'created_at'
    ]
    list_filter = ['is_exempt', 'exemption_type', 'effective_date', 'created_at']
    search_fields = ['user__username', 'user__email', 'certificate_number']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Exemption Details', {
            'fields': ('is_exempt', 'exemption_type', 'certificate_number', 'certificate_file')
        }),
        ('Validity Period', {
            'fields': ('effective_date', 'expiry_date')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        }),
    )

    def is_valid_display(self, obj):
        """Display if exemption is currently valid"""
        is_valid = obj.is_valid
        color = 'green' if is_valid else 'red'
        text = 'Valid' if is_valid else 'Invalid'
        return format_html('<span style="color: {};">{}</span>', color, text)
    is_valid_display.short_description = 'Currently Valid'
    is_valid_display.admin_order_field = 'is_exempt'

    actions = ['approve_exemptions', 'revoke_exemptions']

    def approve_exemptions(self, request, queryset):
        """Approve selected exemptions"""
        updated = queryset.update(
            is_exempt=True,
            effective_date=timezone.now().date()
        )
        self.message_user(request, f'{updated} exemptions approved.')
    approve_exemptions.short_description = 'Approve selected exemptions'

    def revoke_exemptions(self, request, queryset):
        """Revoke selected exemptions"""
        updated = queryset.update(
            is_exempt=False,
            expiry_date=timezone.now().date()
        )
        self.message_user(request, f'{updated} exemptions revoked.')
    revoke_exemptions.short_description = 'Revoke selected exemptions'

@admin.register(NEW_TaxCalculation)
class NEW_TaxCalculationAdmin(admin.ModelAdmin):
    """NEW: Admin interface for tax calculations"""
    list_display = [
        'order_link', 'tax_rate', 'taxable_amount', 'tax_rate_display',
        'tax_amount', 'is_exempt', 'calculated_at'
    ]
    list_filter = ['is_exempt', 'calculated_at', 'tax_rate__state']
    search_fields = ['order__id', 'tax_rate__state', 'exemption_reason']
    ordering = ['-calculated_at']
    date_hierarchy = 'calculated_at'
    readonly_fields = ['calculated_at']

    fieldsets = (
        ('Order Information', {
            'fields': ('order',)
        }),
        ('Tax Details', {
            'fields': ('tax_rate', 'taxable_amount', 'tax_rate_value', 'tax_amount')
        }),
        ('Exemption Information', {
            'fields': ('is_exempt', 'exemption_reason'),
            'classes': ('collapse',)
        }),
        ('Calculation Info', {
            'fields': ('calculated_at',),
            'classes': ('collapse',)
        }),
    )

    def order_link(self, obj):
        """Link to order admin"""
        url = reverse('admin:cart_order_change', args=[obj.order.id])
        return format_html('<a href="{}">Order #{}</a>', url, obj.order.id)
    order_link.short_description = 'Order'
    order_link.admin_order_field = 'order__id'

    def tax_rate_display(self, obj):
        """Display tax rate as percentage"""
        if obj.tax_rate_value:
            return f"{obj.tax_rate_value * 100:.2f}%"
        return "N/A"
    tax_rate_display.short_description = 'Rate'
    tax_rate_display.admin_order_field = 'tax_rate_value'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'tax_rate')


# Register the new models
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'country']
    list_filter = ['country']
    search_fields = ['name', 'country__name']
    ordering = ['country__name', 'name']




@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'state']
    list_filter = ['state__country', 'state']
    search_fields = ['name', 'state__name', 'state__country__name']
    ordering = ['state__country__name', 'state__name', 'name']