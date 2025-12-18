import random
import string
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Order, ShippingCost


def create_new_order():
    try:
        date = str(timezone.now().date())
        random_number = ''.join(random.choices(string.digits, k=8))
        reference_number = f'{date}-{random_number}'
        order = Order(reference_number=reference_number)
        order.save()
        return order
    except IntegrityError:
        create_new_order()


def get_or_set_order_session(request):
    # Try to get order_id from session first
    order_id = request.session.get('order_id', None)
    
    # Fallback: Try to get order_id from custom header (for localStorage approach)
    if order_id is None:
        order_id_header = request.META.get('HTTP_X_ORDER_ID', None)
        if order_id_header:
            try:
                order_id = int(order_id_header)
                # Validate that order exists and is not finalized
                order = Order.objects.get(id=order_id, ordered=False)
                # Save to session for future requests
                request.session['order_id'] = order.id
                request.session.modified = True
                return order
            except (ValueError, Order.DoesNotExist):
                pass

    if order_id is None:
        order = create_new_order()
        request.session['order_id'] = order.id
        request.session.modified = True

    else:
        try:
            order = Order.objects.get(id=order_id, ordered=False)
        except Order.DoesNotExist:
            order = create_new_order()
            request.session['order_id'] = order.id
            request.session.modified = True

    if request.user.is_authenticated and order.user is None:
        order.user = request.user
        order.save()

    # Refresh order to get latest items count
    order.refresh_from_db()
    
    # If the session doesn't say a coupon was intentionally applied this session,
    # make sure we don't carry over an old coupon on a reused, not-finalized order.
    if not request.session.get('coupon_applied_at'):
        if getattr(order, 'coupon_id', None):
            order.coupon = None
            order.save(update_fields=['coupon'])

    # If the cart is empty, don't keep shipping or coupon around
    # IMPORTANT: Check items count after refresh
    items_count = order.items.count()
    if items_count == 0:
        # Always clear coupon when cart is empty, regardless of session flag
        if getattr(order, 'coupon_id', None):
            order.coupon = None
            order.save(update_fields=['coupon'])
        # Clear coupon session flag
        if 'coupon_applied_at' in request.session:
            del request.session['coupon_applied_at']
            request.session.modified = True
        # Clear shipping and discounts
        order.clear_discounts_and_shipping(request)
    
    # Clear shipping and tax data if no shipping address is set (for ALL orders)
    if hasattr(order, 'items') and order.items.count() > 0:
        if not order.shipping_address:
            order.total_shipping_cost = 0
            order.tax_amount = 0
            order.is_tax_exempt = False
            order.wholesale_discount = 0
            order.save(update_fields=['total_shipping_cost', 'tax_amount', 'is_tax_exempt', 'wholesale_discount'])
            # Clear shipping cost from session
            if hasattr(request, 'session') and 'shipping_cost' in request.session:
                del request.session['shipping_cost']
    
    return order


def calculate_total_shipping_cost(order, country=None, state=None, city=None):
        # Get location from order if not provided
        if not (country or state or city):
            if not order.shipping_address:
                return Decimal('0.00')
            country = order.shipping_address.country
            state = order.shipping_address.state
            city = order.shipping_address.city
        
        # Check if warehouse settings are configured
        if not hasattr(settings, 'WAREHOUSE_COUNTRY') or not settings.WAREHOUSE_COUNTRY:
            return Decimal('0.00')
        
        # Get shipping cost rules based on shipment type
        qs = ShippingCost.objects.all()

        if country != settings.WAREHOUSE_COUNTRY:
            qs = qs.filter(shipment_type=ShippingCost.INTERNATIONAL)
        elif state != settings.WAREHOUSE_STATE:
            qs = qs.filter(shipment_type=ShippingCost.OTHER_STATE)
        elif city != settings.WAREHOUSE_CITY:
            qs = qs.filter(shipment_type=ShippingCost.OTHER_CITY)
        else:
            qs = qs.filter(shipment_type=ShippingCost.LOCAL)

        # If no shipping rules found for this type, return 0
        if not qs.exists():
            return Decimal('0.00')

        total = Decimal('0.00')
        for item in order.items.all():
            charges = calculate_item_shipping_charges(qs, item.variant)
            if charges:
                total += Decimal(str(charges)) * item.quantity
        
        return total


def calculate_item_shipping_charges(qs, variant):
    # Get volume and weight, default to 1 if not set
    volume = getattr(variant, 'volume', None) or 1
    weight = getattr(variant, 'weight', None) or 1
    shipping_cost_by_volume = None
    shipping_cost_by_weight = None
    charges = None
    
    # Try to find exact match first
    try:
        shipping_cost_by_volume = qs.get(parameter__exact=ShippingCost.VOLUME,
                                         value_start__lte=volume,
                                         value_end__gte=volume)
    except ShippingCost.DoesNotExist:
        pass

    try:
        shipping_cost_by_weight = qs.get(parameter__exact=ShippingCost.WEIGHT,
                                         value_start__lte=weight,
                                         value_end__gte=weight)
    except ShippingCost.DoesNotExist:
        pass

    # If no exact match, try to find the highest range for the shipment type
    if not shipping_cost_by_volume:
        try:
            # Get the highest volume range for this shipment type
            volume_costs = qs.filter(parameter=ShippingCost.VOLUME).order_by('-value_end')
            if volume_costs.exists():
                shipping_cost_by_volume = volume_costs.first()
        except:
            pass

    if not shipping_cost_by_weight:
        try:
            # Get the highest weight range for this shipment type
            weight_costs = qs.filter(parameter=ShippingCost.WEIGHT).order_by('-value_end')
            if weight_costs.exists():
                shipping_cost_by_weight = weight_costs.first()
        except:
            pass

    if shipping_cost_by_volume and shipping_cost_by_weight:
        if shipping_cost_by_volume.charges > shipping_cost_by_weight.charges:
            charges = shipping_cost_by_volume.charges
        else:
            charges = shipping_cost_by_weight.charges
    elif shipping_cost_by_volume:
        charges = shipping_cost_by_volume.charges
    elif shipping_cost_by_weight:
        charges = shipping_cost_by_weight.charges
    else:
        # If no shipping data available, return None (will be handled by calling function)
        charges = None
    return charges


def send_new_order_email(order):

    context = {
        'order': order, 'site': settings.SITE_URL,
    }
    subject = render_to_string("email/new_order_email_subject.txt", context).strip()
    text_body = render_to_string("email/new_order_email_body.txt", context)
    html_body = render_to_string("email/new_order_email_body.html", context)

    send_mail(
        subject=subject,
        message=text_body,
        html_message=html_body,
        from_email=[settings.DEFAULT_FROM_EMAIL],
        recipient_list=[order.user.email],
        fail_silently=False,
    )
