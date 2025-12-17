from decimal import Decimal
from django.utils import timezone
from django.db import models
from .models import NEW_TaxRate, NEW_TaxExemption, NEW_TaxCalculation, City

def NEW_get_tax_rate(country, state, city=None):
    """
    NEW: Get applicable tax rate for a given location using new model structure
    Priority: City > State > Country
    """
    today = timezone.now().date()
    
    
    # Try to find city-specific rate first
    if city:
        rate = NEW_TaxRate.objects.filter(
            country__name__iexact=country,
            state__name__iexact=state,
            city__name__iexact=city,
            is_active=True,
            effective_date__lte=today
        ).filter(
            models.Q(expiry_date__isnull=True) | models.Q(expiry_date__gte=today)
        ).order_by('-effective_date').first()
        
        if rate:
            return rate
    
    # Fall back to state rate
    rate = NEW_TaxRate.objects.filter(
        country__name__iexact=country,
        state__name__iexact=state,
        city__isnull=True,
        is_active=True,      
        effective_date__lte=today
    ).filter(
        models.Q(expiry_date__isnull=True) | models.Q(expiry_date__gte=today)
    ).order_by('-effective_date').first()
    
    if rate:
        return rate
    
    # Fall back to country-wide rate
    rate = NEW_TaxRate.objects.filter(
        country__name__iexact=country,
        state__isnull=True,
        city__isnull=True,
        is_active=True,
        effective_date__lte=today
    ).filter(
        models.Q(expiry_date__isnull=True) | models.Q(expiry_date__gte=today)
    ).order_by('-effective_date').first()
    
    return rate

def NEW_is_user_tax_exempt(user):
    """
    NEW: Check if user is tax exempt
    """
    if not user or not user.is_authenticated:
        return False
    
    try:
        exemption = user.tax_exemption
        return exemption.is_valid
    except NEW_TaxExemption.DoesNotExist:
        return False

def NEW_calculate_tax_for_order(order):
    """
    NEW: Calculate tax for an order using new model structure
    Returns: (tax_amount, tax_rate, is_exempt)
    """
    # Check if user is tax exempt
    if NEW_is_user_tax_exempt(order.user):
        # Create exempt calculation record
        NEW_TaxCalculation.objects.create(
            order=order,
            taxable_amount=order.get_raw_subtotal(),
            tax_rate_value=Decimal('0.0000'),
            tax_amount=Decimal('0.00'),
            is_exempt=True, 
            exemption_reason="User has valid tax exemption"
        )
        return Decimal('0.00'), None, True
    
    # Get shipping address for tax calculation
    if not order.shipping_address:
        return Decimal('0.00'), None, False
    
    address = order.shipping_address
    
    
    # Get applicable tax rate using new model structure
    tax_rate = NEW_get_tax_rate(
        country=address.country,
        state=address.state,
        city=address.city
    )
    
    if not tax_rate:
        return Decimal('0.00'), None, False
    
    # Calculate tax amount
    taxable_amount = order.get_raw_subtotal()
    tax_amount = taxable_amount * tax_rate.rate  # Rate is already stored as decimal (0.1075 for 10.75%)
    
    # Create calculation record
    NEW_TaxCalculation.objects.create(
        order=order,
        tax_rate=tax_rate,
        taxable_amount=taxable_amount,
        tax_rate_value=tax_rate.rate,
        tax_amount=tax_amount,
        is_exempt=False
    )
    
    return tax_amount, tax_rate, False

def NEW_get_tax_summary_for_order(order):
    """
    NEW: Get detailed tax summary for an order
    """
    calculations = order.tax_calculations.all()
    
    if not calculations.exists():
        return {
            'total_tax': Decimal('0.00'),
            'is_exempt': False,
            'exemption_reason': None,
            'tax_breakdown': []
        }
    
    total_tax = sum(calc.tax_amount for calc in calculations)
    is_exempt = any(calc.is_exempt for calc in calculations)
    exemption_reason = None
    
    if is_exempt:
        exempt_calc = calculations.filter(is_exempt=True).first()
        exemption_reason = exempt_calc.exemption_reason if exempt_calc else "Tax exempt"
    
    tax_breakdown = []
    for calc in calculations:
        if not calc.is_exempt and calc.tax_rate:
            tax_breakdown.append({
                'location': str(calc.tax_rate),
                'rate': f"{calc.tax_rate_value * 100:.2f}%",
                'taxable_amount': calc.taxable_amount,
                'tax_amount': calc.tax_amount
            })
    
    return {
        'total_tax': total_tax,
        'is_exempt': is_exempt,
        'exemption_reason': exemption_reason,
        'tax_breakdown': tax_breakdown
    }

def NEW_create_default_tax_rates():
    """
    NEW: Create default tax rates for US states and cities
    """
    from datetime import date
    
    # Get or create United States country
    country, created = Country.objects.get_or_create(name="United States")
    if created:
        print(f"Created country: {country.name}")
    
    # Default tax rates for US states
    state_rates = {
        'California': 0.0875,  # 8.75%
        'New York': 0.0800,    # 8.00%
        'Texas': 0.0625,       # 6.25%
        'Florida': 0.0600,     # 6.00%
        'Illinois': 0.0625,    # 6.25%
        'Pennsylvania': 0.0600, # 6.00%
        'Ohio': 0.0575,        # 5.75%
        'Georgia': 0.0400,     # 4.00%
        'North Carolina': 0.0475, # 4.75%
        'Michigan': 0.0600,    # 6.00%
    }
    
    # Create states and tax rates
    for state_name, rate_value in state_rates.items():
        # Get or create state
        state, created = State.objects.get_or_create(
            name=state_name,
            country=country
        )
        if created:
            print(f"Created state: {state.name}")
        
        # Create state-level tax rate
        tax_rate, created = NEW_TaxRate.objects.get_or_create(
            country=country,
            state=state,
            city=None,
            defaults={
                'rate': rate_value,
                'tax_type': 'sales',
                'effective_date': date.today(),
                'is_active': True
            }
        )
        if created:
            print(f"Created tax rate for {state.name}: {rate_value * 100:.2f}%")
    
    # Create some city-specific rates
    city_rates = {
        ('California', 'San Francisco'): 0.0875,  # 8.75%
        ('California', 'Los Angeles'): 0.0900,    # 9.00%
        ('California', 'San Diego'): 0.0775,      # 7.75%
        ('New York', 'New York City'): 0.0875,    # 8.75%
        ('Texas', 'Houston'): 0.0825,             # 8.25%
        ('Texas', 'Dallas'): 0.0825,              # 8.25%
    }
    
    for (state_name, city_name), rate_value in city_rates.items():
        try:
            state = State.objects.get(name=state_name, country=country)
            
            # Get or create city
            city, created = City.objects.get_or_create(
                name=city_name,
                state=state
            )
            if created:
                print(f"Created city: {city.name}")
            
            # Create city-level tax rate
            tax_rate, created = NEW_TaxRate.objects.get_or_create(
                country=country,
                state=state,
                city=city,
                defaults={
                    'rate': rate_value,
                    'tax_type': 'sales',
                    'effective_date': date.today(),
                    'is_active': True
                }
            )
            if created:
                print(f"Created tax rate for {city.name}, {state.name}: {rate_value * 100:.2f}%")
        except State.DoesNotExist:
            print(f"State {state_name} not found, skipping city {city_name}")

# Hardcoded tax rates removed - all tax rates should be added through admin panel
