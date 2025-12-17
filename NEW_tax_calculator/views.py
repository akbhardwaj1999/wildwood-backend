from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from decimal import Decimal
from .models import NEW_TaxExemption, NEW_TaxRate
from .utils import NEW_calculate_tax_for_order, NEW_get_tax_summary_for_order
from .forms import NEW_TaxExemptionRequestForm

@login_required
def NEW_tax_exemption_request(request):
    """
    NEW: View for users to request tax exemption
    """
    if request.method == 'POST':
        form = NEW_TaxExemptionRequestForm(request.POST, request.FILES)
        if form.is_valid():
            # Check if user already has an exemption
            exemption, created = NEW_TaxExemption.objects.get_or_create(
                user=request.user,
                defaults={
                    'is_exempt': False,
                    'exemption_type': form.cleaned_data['exemption_type'],
                    'certificate_number': form.cleaned_data['certificate_number'],
                    'certificate_file': form.cleaned_data['certificate_file'],
                    'admin_notes': 'Pending admin approval'
                }
            )
            
            if not created:
                # Update existing exemption
                exemption.exemption_type = form.cleaned_data['exemption_type']
                exemption.certificate_number = form.cleaned_data['certificate_number']
                if form.cleaned_data['certificate_file']:
                    exemption.certificate_file = form.cleaned_data['certificate_file']
                exemption.admin_notes = 'Updated - Pending admin approval'
                exemption.is_exempt = False
                exemption.save()
            
            messages.success(request, 'Your tax exemption request has been submitted for review.')
            return redirect('NEW_tax_calculator:exemption_status')
    else:
        form = NEW_TaxExemptionRequestForm()
    
    return render(request, 'NEW_tax_calculator/exemption_request.html', {
        'form': form,
        'has_exemption': hasattr(request.user, 'tax_exemption')
    })

@login_required
def NEW_tax_exemption_status(request):
    """
    NEW: View for users to check their tax exemption status
    """
    try:
        exemption = request.user.tax_exemption
    except NEW_TaxExemption.DoesNotExist:
        exemption = None
    
    return render(request, 'NEW_tax_calculator/exemption_status.html', {
        'exemption': exemption
    })

def NEW_tax_calculator_api(request):
    """
    NEW: API endpoint for tax calculation
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        state = request.POST.get('state')
        county = request.POST.get('county', '')
        city = request.POST.get('city', '')
        amount = Decimal(request.POST.get('amount', '0'))
        
        if not state or amount <= 0:
            return JsonResponse({'error': 'Invalid parameters'}, status=400)
        
        # Get tax rate
        from .utils import NEW_get_tax_rate
        tax_rate = NEW_get_tax_rate(state, county, city)
        
        if tax_rate:
            tax_amount = amount * tax_rate.rate
            return JsonResponse({
                'success': True,
                'tax_rate': float(tax_rate.rate),
                'tax_rate_percentage': float(tax_rate.rate * 100),
                'tax_amount': float(tax_amount),
                'total_amount': float(amount + tax_amount),
                'location': str(tax_rate)
            })
        else:
            return JsonResponse({
                'success': True,
                'tax_rate': 0.0,
                'tax_rate_percentage': 0.0,
                'tax_amount': 0.0,
                'total_amount': float(amount),
                'location': 'No tax rate found'
            })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def NEW_tax_summary(request, order_id):
    """
    NEW: View for detailed tax summary of an order
    """
    from cart.models import Order
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    tax_summary = NEW_get_tax_summary_for_order(order)
    
    return render(request, 'NEW_tax_calculator/tax_summary.html', {
        'order': order,
        'tax_summary': tax_summary
    })

def NEW_tax_rates_list(request):
    """
    NEW: Public view for tax rates by state
    """
    state = request.GET.get('state', '')
    
    if state:
        rates = NEW_TaxRate.objects.filter(
            state=state.upper(),
            is_active=True
        ).order_by('county', 'city')
    else:
        rates = NEW_TaxRate.objects.filter(
            is_active=True,
            county__isnull=True,
            city__isnull=True
        ).order_by('state')
    
    return render(request, 'NEW_tax_calculator/tax_rates.html', {
        'rates': rates,
        'selected_state': state
    })