from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from decimal import Decimal
from .models import NEW_WholesaleUser, NEW_WholesaleRequest
from .utils import NEW_is_user_wholesale, NEW_get_discount_summary
from .forms import NEW_WholesaleRequestForm

@login_required
def NEW_wholesale_request(request):
    """
    NEW: View for users to request wholesale account
    """
    if request.method == 'POST':
        form = NEW_WholesaleRequestForm(request.POST, request.FILES)
        if form.is_valid():
            # Check if user already has a pending or approved request
            existing_request = NEW_WholesaleRequest.objects.filter(
                user=request.user,
                status__in=['pending', 'approved']
            ).first()
            
            if existing_request:
                if existing_request.status == 'pending':
                    messages.info(request, 'You already have a pending wholesale request.')
                else:
                    messages.info(request, 'You already have an approved wholesale account.')
                return redirect('NEW_wholesale_discounts:wholesale_status')
            
            # Create new request
            wholesale_request = form.save(commit=False)
            wholesale_request.user = request.user
            wholesale_request.save()
            
            messages.success(request, 'Your wholesale account request has been submitted for review.')
            return redirect('NEW_wholesale_discounts:wholesale_status')
    else:
        form = NEW_WholesaleRequestForm()
    
    return render(request, 'NEW_wholesale_discounts/wholesale_request.html', {
        'form': form,
        'is_wholesale': NEW_is_user_wholesale(request.user)
    })

@login_required
def NEW_wholesale_status(request):
    """
    NEW: View for users to check their wholesale status
    """
    try:
        wholesale_profile = request.user.wholesale_profile
    except NEW_WholesaleUser.DoesNotExist:
        wholesale_profile = None
        
        # Safety check: Auto-fix missing profile for approved requests
        approved_request = NEW_WholesaleRequest.objects.filter(
            user=request.user,
            status='approved'
        ).first()
        
        if approved_request:
            # Create missing wholesale profile
            wholesale_profile = NEW_WholesaleUser.objects.create(
                user=request.user,
                is_wholesale=True,
                approved_by=approved_request.reviewed_by,
                approved_at=approved_request.reviewed_at or timezone.now()
            )
    
    # Get recent requests
    recent_requests = NEW_WholesaleRequest.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    return render(request, 'NEW_wholesale_discounts/wholesale_status.html', {
        'wholesale_profile': wholesale_profile,
        'recent_requests': recent_requests
    })

@login_required
def NEW_wholesale_tiers(request):
    """
    NEW: View for displaying available wholesale discount tiers
    """
    from .models import NEW_WholesaleDiscountConfig
    
    # Get the active discount configuration
    config = NEW_WholesaleDiscountConfig.objects.filter(is_active=True).first()
    
    # Create tier-like data from configuration
    tiers = []
    if config:
        tiers = [
            {
                'name': f'Above ${config.threshold_1}',
                'min_order_amount': config.threshold_1,
                'discount_percentage': config.discount_1,
                'description': f'Get {config.discount_1}% off orders above ${config.threshold_1}'
            },
            {
                'name': f'Above ${config.threshold_2}',
                'min_order_amount': config.threshold_2,
                'discount_percentage': config.discount_2,
                'description': f'Get {config.discount_2}% off orders above ${config.threshold_2}'
            },
            {
                'name': f'Above ${config.threshold_3}',
                'min_order_amount': config.threshold_3,
                'discount_percentage': config.discount_3,
                'description': f'Get {config.discount_3}% off orders above ${config.threshold_3}'
            },
            {
                'name': f'Above ${config.threshold_4}',
                'min_order_amount': config.threshold_4,
                'discount_percentage': config.discount_4,
                'description': f'Get {config.discount_4}% off orders above ${config.threshold_4}'
            }
        ]
    
    return render(request, 'NEW_wholesale_discounts/wholesale_tiers.html', {
        'tiers': tiers,
        'is_wholesale': NEW_is_user_wholesale(request.user)
    })

def NEW_wholesale_discount_api(request):
    """
    NEW: API endpoint for wholesale discount calculation
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        order_amount = Decimal(request.POST.get('amount', '0'))
        
        if order_amount <= 0:
            return JsonResponse({'error': 'Invalid order amount'}, status=400)
        
        # Get discount summary
        summary = NEW_get_discount_summary(request.user)
        
        if summary:
            from .utils import NEW_calculate_wholesale_discount, NEW_get_next_discount_threshold
            discount_amount = NEW_calculate_wholesale_discount(order_amount, request.user)
            next_threshold = NEW_get_next_discount_threshold(order_amount)
            
            return JsonResponse({
                'success': True,
                'is_wholesale': summary['is_wholesale'],
                'discount_amount': float(discount_amount),
                'discount_tiers': summary['discount_tiers'],
                'next_threshold': next_threshold
            })
        else:
            return JsonResponse({
                'success': True,
                'is_wholesale': False,
                'discount_amount': 0.0,
                'discount_tiers': [],
                'next_threshold': None
            })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def NEW_wholesale_dashboard(request):
    """
    NEW: Wholesale user dashboard
    """
    if not NEW_is_user_wholesale(request.user):
        messages.warning(request, 'You need wholesale access to view this page.')
        return redirect('NEW_wholesale_discounts:wholesale_request')
    
    try:
        wholesale_profile = request.user.wholesale_profile
    except NEW_WholesaleUser.DoesNotExist:
        messages.error(request, 'Wholesale profile not found.')
        return redirect('NEW_wholesale_discounts:wholesale_request')
    
    # Get user's recent orders with wholesale discounts
    from cart.models import Order
    recent_orders = Order.objects.filter(
        user=request.user,
        wholesale_discounts__isnull=False
    ).order_by('-ordered_date')[:10]
    
    # Get discount configuration for display
    from .models import NEW_WholesaleDiscountConfig
    config = NEW_WholesaleDiscountConfig.objects.filter(is_active=True).first()
    
    return render(request, 'NEW_wholesale_discounts/wholesale_dashboard.html', {
        'wholesale_profile': wholesale_profile,
        'recent_orders': recent_orders,
        'discount_config': config
    })