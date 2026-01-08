from decimal import Decimal
from django.utils import timezone
from django.db import models
from .models import NEW_WholesaleDiscountConfig, NEW_WholesaleUser, NEW_WholesaleDiscount

def NEW_is_user_wholesale(user):
    """
    NEW: Check if user has wholesale access
    """
    if not user or not user.is_authenticated:
        return False
    
    try:
        return user.wholesale_profile.is_wholesale
    except NEW_WholesaleUser.DoesNotExist:
        return False

def NEW_get_active_discount_config():
    """
    NEW: Get the active discount configuration
    """
    try:
        return NEW_WholesaleDiscountConfig.objects.filter(is_active=True).first()
    except NEW_WholesaleDiscountConfig.DoesNotExist:
        return None

def NEW_calculate_wholesale_discount(order_amount, user):
    """
    NEW: Calculate wholesale discount based on order amount
    Simple system: Above X amount → Y% discount
    """
    if not NEW_is_user_wholesale(user):
        return Decimal('0.00')
    
    config = NEW_get_active_discount_config()
    if not config:
        return Decimal('0.00')
    
    discount_percentage = config.get_discount_for_amount(order_amount)
    
    if discount_percentage > 0:
        discount_amount = (order_amount * discount_percentage) / 100
        return discount_amount
    
    return Decimal('0.00')

def NEW_apply_wholesale_discount_to_order(order):
    """
    NEW: Apply wholesale discount to order
    """
    if not order.user or not NEW_is_user_wholesale(order.user):
        return Decimal('0.00')
    
    order_amount = Decimal(str(order.get_raw_subtotal()))
    discount_amount = NEW_calculate_wholesale_discount(order_amount, order.user)
    
    if discount_amount > 0:
        # Create discount record
        try:
            wholesale_user = order.user.wholesale_profile
            config = NEW_get_active_discount_config()
            
            if config:
                discount_percentage = config.get_discount_for_amount(order_amount)
                
                NEW_WholesaleDiscount.objects.create(
                    order=order,
                    wholesale_user=wholesale_user,
                    discount_type='percentage',
                    discount_value=discount_percentage,
                    discount_amount=discount_amount,
                    order_amount=order_amount
                )
        except Exception as e:
            # Log error but don't break the order
            pass
    
    return discount_amount

def NEW_get_discount_summary(user):
    """
    NEW: Get discount summary for user
    """
    if not NEW_is_user_wholesale(user):
        return None
    
    config = NEW_get_active_discount_config()
    if not config:
        return None
    
    return {
        'is_wholesale': True,
        'discount_tiers': [
            {
                'threshold': config.threshold_1,
                'discount': config.discount_1,
                'description': f"Above ${config.threshold_1} → {config.discount_1}% off"
            },
            {
                'threshold': config.threshold_2,
                'discount': config.discount_2,
                'description': f"Above ${config.threshold_2} → {config.discount_2}% off"
            },
            {
                'threshold': config.threshold_3,
                'discount': config.discount_3,
                'description': f"Above ${config.threshold_3} → {config.discount_3}% off"
            },
            {
                'threshold': config.threshold_4,
                'discount': config.discount_4,
                'description': f"Above ${config.threshold_4} → {config.discount_4}% off"
            }
        ]
    }

def NEW_get_next_discount_threshold(current_amount):
    """
    NEW: Get the next discount threshold for current amount
    """
    config = NEW_get_active_discount_config()
    if not config:
        return None
    
    if current_amount < config.threshold_1:
        return {
            'threshold': config.threshold_1,
            'discount': config.discount_1,
            'amount_needed': config.threshold_1 - current_amount,
            'description': f"Add ${config.threshold_1 - current_amount:.2f} more to get {config.discount_1}% off"
        }
    elif current_amount < config.threshold_2:
        return {
            'threshold': config.threshold_2,
            'discount': config.discount_2,
            'amount_needed': config.threshold_2 - current_amount,
            'description': f"Add ${config.threshold_2 - current_amount:.2f} more to get {config.discount_2}% off"
        }
    elif current_amount < config.threshold_3:
        return {
            'threshold': config.threshold_3,
            'discount': config.discount_3,
            'amount_needed': config.threshold_3 - current_amount,
            'description': f"Add ${config.threshold_3 - current_amount:.2f} more to get {config.discount_3}% off"
        }
    elif current_amount < config.threshold_4:
        return {
            'threshold': config.threshold_4,
            'discount': config.discount_4,
            'amount_needed': config.threshold_4 - current_amount,
            'description': f"Add ${config.threshold_4 - current_amount:.2f} more to get {config.discount_4}% off"
        }
    else:
        return {
            'threshold': config.threshold_4,
            'discount': config.discount_4,
            'amount_needed': 0,
            'description': f"You're getting the maximum {config.discount_4}% discount!"
        }