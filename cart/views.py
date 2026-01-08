import json
import logging
from decimal import Decimal

from mainsite.location_data import get_countries, get_us_states, get_cities_for_state, get_state_name, get_state_code
from NEW_tax_calculator.models import NEW_TaxRate
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View, TemplateView, FormView, ListView, DetailView

from cart.forms import AddressForm
from cart.models import OrderItem, Variant, Address, Payment, Order, Coupon
from cart.utils import get_or_set_order_session, calculate_total_shipping_cost, send_new_order_email
from mainsite.mixins import TemplateResponseMixinWithMobileSupport
from mainsite.tasks import send_out_of_stock_email

logger = logging.getLogger(__name__)


class CartView(TemplateResponseMixinWithMobileSupport, TemplateView):
    template_name = "cart.html"

    def get_context_data(self, **kwargs):
        context = super(CartView, self).get_context_data(**kwargs)
        order = get_or_set_order_session(self.request)
        
        # NO SHIPPING CALCULATION ON CART PAGE - Only on checkout page
        if order and order.items.exists():
            # Clear all shipping, tax, and wholesale data on cart page
            order.total_shipping_cost = 0
            order.tax_amount = 0
            order.is_tax_exempt = False
            # Keep wholesale discount calculation for registered users
            if order.user and order.user.is_authenticated:
                from NEW_wholesale_discounts.utils import NEW_apply_wholesale_discount_to_order
                order.wholesale_discount = NEW_apply_wholesale_discount_to_order(order)
            else:
                order.wholesale_discount = 0
            order.save(update_fields=['total_shipping_cost', 'tax_amount', 'is_tax_exempt', 'wholesale_discount'])
            # Clear shipping cost from session
            if 'shipping_cost' in self.request.session:
                del self.request.session['shipping_cost']
        else:
            # If no items in cart, clear everything
            if order:
                order.total_shipping_cost = 0
                order.tax_amount = 0
                order.is_tax_exempt = False
                # Keep wholesale discount calculation for registered users
                if order.user and order.user.is_authenticated:
                    from NEW_wholesale_discounts.utils import NEW_apply_wholesale_discount_to_order
                    order.wholesale_discount = NEW_apply_wholesale_discount_to_order(order)
                else:
                    order.wholesale_discount = 0
                order.save(update_fields=['total_shipping_cost', 'tax_amount', 'is_tax_exempt', 'wholesale_discount'])
            # Clear shipping cost from session when cart is empty
            if 'shipping_cost' in self.request.session:
                del self.request.session['shipping_cost']
        
        context["order"] = order
        # Countries, states, warehouse info removed - not needed on cart page anymore
        return context
    
    # get_available_states and get_available_cities methods removed - not needed on cart page anymore


class QuickAddToCartView(View):
    def get(self, request, *args, **kwargs):
        order = get_or_set_order_session(self.request)
        variant = get_object_or_404(Variant, id=request.GET['id'])

        item_filter = order.items.filter(variant=variant)
        is_new_item = not item_filter.exists()
        
        if item_filter.exists():
            item = item_filter.first()
            item.quantity += 1
            item.save()
        else:
            OrderItem.objects.create(variant=variant, order=order)

        # NO SHIPPING CALCULATION ON CART PAGE - Only on checkout page
        order.total_shipping_cost = 0
        
        # IMPORTANT: If user modifies cart (adds/removes/updates items) and cart has abandoned emails,
        # reset the email counters because user is actively engaging with the cart again
        # This applies to ANY cart modification, not just new items
        if order.abandoned_email_count > 0:
            from django.utils import timezone
            current_time = timezone.now()
            # Reset email counters and update timestamps
            # Note: We need to use update() to bypass auto_now_add restriction for start_date
            Order.objects.filter(id=order.id).update(
                start_date=current_time,
                last_updated=current_time,  # Also update last_updated to ensure scheduler picks this cart
                abandoned_email_count=0,
                abandoned_email_sent=False,
                abandoned_email_sent_at=None,
                total_shipping_cost=0
            )
            # Refresh the order object to get updated values
            order.refresh_from_db()
        else:
            order.save(update_fields=['total_shipping_cost'])

        response = {
            "status": "success",
            "total_items": order.items.count(),
            "sub_total": order.get_subtotal(),
            "shipping_cost": order.total_shipping_cost,
            "total": order.get_total(),
            "mini-cart-html": render_to_string('mini-cart.html', {"current_order": order})
        }

        return JsonResponse(response)


class IncreaseQuantityView(View):
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        order_item.quantity += 1
        order_item.save()

        # NO SHIPPING CALCULATION ON CART PAGE - Only on checkout page
        order = order_item.order
        order.total_shipping_cost = 0
        
        # IMPORTANT: Reset email counters if cart has abandoned emails (user is actively engaging)
        if order.abandoned_email_count > 0:
            from django.utils import timezone
            current_time = timezone.now()
            Order.objects.filter(id=order.id).update(
                start_date=current_time,
                last_updated=current_time,
                abandoned_email_count=0,
                abandoned_email_sent=False,
                abandoned_email_sent_at=None,
                total_shipping_cost=0
            )
            order.refresh_from_db()
        else:
            order.save(update_fields=['total_shipping_cost'])
        return redirect("cart:summary")


class DecreaseQuantityView(View):
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        order = order_item.order
        
        if order_item.quantity <= 1:
            order_item.delete()
        else:
            order_item.quantity -= 1
            order_item.save()

        # NO SHIPPING CALCULATION ON CART PAGE - Only on checkout page
        order.total_shipping_cost = 0
        if 'shipping_cost' in request.session:
            del request.session['shipping_cost']
        
        # IMPORTANT: Reset email counters if cart has abandoned emails (user is actively engaging)
        if order.abandoned_email_count > 0:
            from django.utils import timezone
            current_time = timezone.now()
            Order.objects.filter(id=order.id).update(
                start_date=current_time,
                last_updated=current_time,
                abandoned_email_count=0,
                abandoned_email_sent=False,
                abandoned_email_sent_at=None,
                total_shipping_cost=0
            )
            order.refresh_from_db()
        else:
            order.save(update_fields=['total_shipping_cost'])
        return redirect("cart:summary")


class UpdateQuantityView(View):
    def get(self, request, *args, **kwargs):
        order_item_id = request.GET.get('id')
        quantity = request.GET.get('quantity')

        order_item = get_object_or_404(OrderItem, id=order_item_id)
        order_item.quantity = quantity or 0
        order_item.save()

        # NO SHIPPING CALCULATION ON CART PAGE - Only on checkout page
        order = order_item.order
        order.total_shipping_cost = 0
        
        # IMPORTANT: Reset email counters if cart has abandoned emails (user is actively engaging)
        if order.abandoned_email_count > 0:
            from django.utils import timezone
            current_time = timezone.now()
            Order.objects.filter(id=order.id).update(
                start_date=current_time,
                last_updated=current_time,
                abandoned_email_count=0,
                abandoned_email_sent=False,
                abandoned_email_sent_at=None,
                total_shipping_cost=0
            )
            order.refresh_from_db()
        else:
            order.save(update_fields=['total_shipping_cost'])

        response = {
            "status": "success",
            "total_items": order.items.count(),
            "sub_total": order.get_subtotal(),
            "shipping_cost": order.total_shipping_cost,
            "total": order.get_total(),
        }
        return JsonResponse(response)


class RemoveFromCartView(View):
    def get(self, request, *args, **kwargs):
        if kwargs['pk'] != '0':
            order_item_id = kwargs['pk']
        else:
            order_item_id = request.GET.get('id')

        try:
            order_item = OrderItem.objects.get(id=order_item_id)
            order = order_item.order
            order_item.delete()
        except OrderItem.DoesNotExist:
            # If order item doesn't exist, redirect to cart
            return redirect("cart:summary")

        # NO SHIPPING CALCULATION ON CART PAGE - Only on checkout page
        order.total_shipping_cost = 0
        if 'shipping_cost' in request.session:
            del request.session['shipping_cost']
        
        # IMPORTANT: Reset email counters if cart has abandoned emails (user is actively engaging)
        if order.abandoned_email_count > 0:
            from django.utils import timezone
            current_time = timezone.now()
            Order.objects.filter(id=order.id).update(
                start_date=current_time,
                last_updated=current_time,
                abandoned_email_count=0,
                abandoned_email_sent=False,
                abandoned_email_sent_at=None,
                total_shipping_cost=0
            )
            order.refresh_from_db()
        else:
            order.save(update_fields=['total_shipping_cost'])

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {
                    "status": "success",
                    "total_items": order.items.count(),
                    "sub_total": order.get_subtotal(),
                    "shipping_cost": order.total_shipping_cost,
                    "total": order.get_total(),
                }
            )
        else:
            return redirect("cart:summary")


class CheckoutView(TemplateResponseMixinWithMobileSupport, FormView):
    template_name = "checkout.html"
    form_class = AddressForm

    def get_success_url(self):
        return reverse("cart:payment")
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests to ensure context data is available"""
        return self.render_to_response(self.get_context_data())
    
    def get_available_states(self):
        """Get states that have tax rates configured in admin panel"""
        try:
            # Get unique states from tax rates
            states_with_rates = NEW_TaxRate.objects.filter(
                is_active=True,
                county__in=['', None],  # State-level rates onlyARE
                city__in=['', None]
            ).values_list('state', flat=True).distinct()
            
            # Convert state codes to state names
            state_choices = dict(NEW_TaxRate.STATE_CHOICES)
            available_states = []
            
            for state_code in states_with_rates:
                if state_code in state_choices:
                    available_states.append((state_code, state_choices[state_code]))
            
            # If no tax rates configured, fall back to all states
            if not available_states:
                available_states = NEW_TaxRate.STATE_CHOICES[1:]  # Skip empty choice
            
            return available_states
        except Exception as e:
            # Fallback to all states
            return NEW_TaxRate.STATE_CHOICES[1:] if hasattr(NEW_TaxRate, 'STATE_CHOICES') else get_us_states()
    
    def get_available_cities(self, state_code):
        """Get cities that have tax rates configured for a specific state"""
        try:
            # Get cities from tax rates for this state
            cities_with_rates = NEW_TaxRate.objects.filter(
                state=state_code,
                is_active=True,
                city__isnull=False
            ).exclude(city='').values_list('city', flat=True).distinct()
            
            # Convert to list of tuples for consistency
            available_cities = [(city, city) for city in cities_with_rates]
            
            # If no cities configured, fall back to default cities
            if not available_cities:
                available_cities = [(city, city) for city in get_cities_for_state(state_code)]
            
            return available_cities
        except Exception as e:
            # Fallback to default cities
            return [(city, city) for city in get_cities_for_state(state_code)]

    def form_valid(self, form):
        order = get_or_set_order_session(self.request)

        # Convert ID numbers to names for consistency with AJAX calls
        from NEW_tax_calculator.models import Country, State, City
        
        country_id = form.cleaned_data['shipping_country']
        state_id = form.cleaned_data['shipping_state']
        city_id = form.cleaned_data['shipping_city']
        
        # Get names from IDs
        try:
            country_name = Country.objects.get(id=country_id).name
        except (Country.DoesNotExist, ValueError):
            country_name = country_id
            
        try:
            state_name = State.objects.get(id=state_id).name
        except (State.DoesNotExist, ValueError):
            state_name = state_id
            
        try:
            city_name = City.objects.get(id=city_id).name
        except (City.DoesNotExist, ValueError):
            city_name = city_id
        

        address = Address.objects.create(
            address_type='S',
            user=self.request.user if self.request.user.is_authenticated else None,
            first_name=form.cleaned_data['shipping_first_name'],
            last_name=form.cleaned_data['shipping_last_name'],
            email_address=form.cleaned_data['shipping_email_address'],
            phone_number=form.cleaned_data['shipping_phone_number'],
            company_name=form.cleaned_data['shipping_company_name'],
            address_line_1=form.cleaned_data['shipping_address_line_1'],
            address_line_2=form.cleaned_data['shipping_address_line_2'],
            country=country_name,  # Use name instead of ID
            state=state_name,      # Use name instead of ID
            city=city_name,        # Use name instead of ID
            zip_code=form.cleaned_data['shipping_zip_code'],
        )
        order.shipping_address = address
        # Save shipping address immediately so tax calculation can use it
        order.save(update_fields=['shipping_address'])
        
        # Calculate tax and wholesale discount
        from NEW_tax_calculator.utils import NEW_calculate_tax_for_order
        from NEW_wholesale_discounts.utils import NEW_apply_wholesale_discount_to_order
        
        # Apply wholesale discount first
        wholesale_discount = NEW_apply_wholesale_discount_to_order(order)
        order.wholesale_discount = wholesale_discount
        
        # Calculate tax on the discounted amount
        tax_amount, tax_rate, is_exempt = NEW_calculate_tax_for_order(order)
        order.tax_amount = tax_amount
        order.is_tax_exempt = is_exempt
        order.save(update_fields=['tax_amount', 'is_tax_exempt', 'wholesale_discount'])

        is_billing_address_same = form.cleaned_data['is_billing_address_same']
        if is_billing_address_same:
            address = Address.objects.create(
                address_type='B',
                user=self.request.user if self.request.user.is_authenticated else None,
                first_name=form.cleaned_data['shipping_first_name'],
                last_name=form.cleaned_data['shipping_last_name'], 
                email_address=form.cleaned_data['shipping_email_address'],
                phone_number=form.cleaned_data['shipping_phone_number'],
                company_name=form.cleaned_data['shipping_company_name'],
                address_line_1=form.cleaned_data['shipping_address_line_1'],
                address_line_2=form.cleaned_data['shipping_address_line_2'],
                country=country_name,  # Use converted name
                state=state_name,      # Use converted name
                city=city_name,        # Use converted name
                zip_code=form.cleaned_data['shipping_zip_code'],
            )
            order.billing_address = address
        else:
            # Convert billing address IDs to names as well
            billing_country_id = form.cleaned_data['billing_country']
            billing_state_id = form.cleaned_data['billing_state']
            billing_city_id = form.cleaned_data['billing_city']
            
            try:
                billing_country_name = Country.objects.get(id=billing_country_id).name
            except (Country.DoesNotExist, ValueError):
                billing_country_name = billing_country_id
                
            try:
                billing_state_name = State.objects.get(id=billing_state_id).name
            except (State.DoesNotExist, ValueError):
                billing_state_name = billing_state_id
                
            try:
                billing_city_name = City.objects.get(id=billing_city_id).name
            except (City.DoesNotExist, ValueError):
                billing_city_name = billing_city_id
            
            address = Address.objects.create(
                address_type='B',
                user=self.request.user if self.request.user.is_authenticated else None,
                first_name=form.cleaned_data['billing_first_name'],
                last_name=form.cleaned_data['billing_last_name'],
                email_address=form.cleaned_data['billing_email_address'],
                phone_number=form.cleaned_data['billing_phone_number'],
                company_name=form.cleaned_data['billing_company_name'],
                address_line_1=form.cleaned_data['billing_address_line_1'],
                address_line_2=form.cleaned_data['billing_address_line_2'],
                country=billing_country_name,  # Use converted name
                state=billing_state_name,      # Use converted name
                city=billing_city_name,        # Use converted name
                zip_code=form.cleaned_data['billing_zip_code'],
            )
            order.billing_address = address

        order.total_shipping_cost = calculate_total_shipping_cost(order)
        
        # Save order with ALL calculations in one go
        order.save(update_fields=[
            'tax_amount', 'is_tax_exempt', 'wholesale_discount', 
            'total_shipping_cost', 'shipping_address', 'billing_address'
        ])
        
        
        messages.info(
            self.request, "Your order has been created")
        return super(CheckoutView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(CheckoutView, self).get_form_kwargs()
        kwargs["user_id"] = self.request.user.id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(CheckoutView, self).get_context_data(**kwargs)
        order = get_or_set_order_session(self.request)
        
        # ALWAYS clear tax and shipping when no shipping address OR when cart is empty
        if order:
            if not order.items.exists() or not order.shipping_address:
                order.tax_amount = 0
                order.is_tax_exempt = False
                # Keep wholesale discount calculation for registered users
                if order.user and order.user.is_authenticated:
                    from NEW_wholesale_discounts.utils import NEW_apply_wholesale_discount_to_order
                    order.wholesale_discount = NEW_apply_wholesale_discount_to_order(order)
                else:
                    order.wholesale_discount = 0
                order.total_shipping_cost = 0
                order.save(update_fields=['tax_amount', 'wholesale_discount', 'is_tax_exempt', 'total_shipping_cost'])
                # Clear shipping cost from session
                if 'shipping_cost' in self.request.session:
                    del self.request.session['shipping_cost']
            
            # ADDITIONAL CHECK: If shipping address exists but we're on refresh (no POST data)
            # Clear tax and shipping to force recalculation
            elif order.shipping_address and not self.request.POST:
                # On page refresh, clear tax and shipping to force recalculation
                order.tax_amount = 0
                order.is_tax_exempt = False
                # Keep wholesale discount calculation for registered users
                if order.user and order.user.is_authenticated:
                    from NEW_wholesale_discounts.utils import NEW_apply_wholesale_discount_to_order
                    order.wholesale_discount = NEW_apply_wholesale_discount_to_order(order)
                else:
                    order.wholesale_discount = 0
                order.total_shipping_cost = 0
                order.save(update_fields=['tax_amount', 'wholesale_discount', 'is_tax_exempt', 'total_shipping_cost'])
                # Clear shipping cost from session
                if 'shipping_cost' in self.request.session:
                    del self.request.session['shipping_cost']
        
        context["order"] = order
        # Remove old country/state logic - now using APIs
        # context["countries"] = get_countries()
        # context["us_states"] = self.get_available_states()

        if self.request.POST.get('shipping_country', None):
            country = self.request.POST['shipping_country']
            if country == 'United States':
                context["states"] = self.get_available_states()
                
                if self.request.POST.get('shipping_state', None):
                    state_code = get_state_code(self.request.POST['shipping_state'])
                    if state_code:
                        context["cities"] = self.get_available_cities(state_code)

        # Calculate grand total based on whether address is set
        if order and order.shipping_address:
            # If address is set, use full calculation
            context["grand_total"] = order.get_total()
        else:
            # If no address, only show subtotal after discounts
            context["grand_total"] = order.get_subtotal_after_discounts() if order else "0.00"
        return context


class PaymentView(TemplateResponseMixinWithMobileSupport, TemplateView):
    template_name = 'payment.html'

    def get_context_data(self, **kwargs):
        context = super(PaymentView, self).get_context_data(**kwargs)
        context["PAYPAL_CLIENT_ID"] = settings.PAYPAL_CLIENT_ID
        order = get_or_set_order_session(self.request)
        
        # Safety check: If tax or shipping is zero but we have a shipping address, recalculate
        if order and order.shipping_address:
            if order.tax_amount == 0 or order.total_shipping_cost == 0:
                from NEW_tax_calculator.utils import NEW_calculate_tax_for_order
                from NEW_wholesale_discounts.utils import NEW_apply_wholesale_discount_to_order
                
                # Recalculate tax
                tax_amount, tax_rate, is_exempt = NEW_calculate_tax_for_order(order)
                order.tax_amount = tax_amount
                order.is_tax_exempt = is_exempt
                
                # Recalculate wholesale discount
                order.wholesale_discount = NEW_apply_wholesale_discount_to_order(order)
                
                # Recalculate shipping
                order.total_shipping_cost = calculate_total_shipping_cost(order)
                
                # Save all calculations
                order.save(update_fields=['tax_amount', 'is_tax_exempt', 'wholesale_discount', 'total_shipping_cost'])
                
        
        context['order'] = order
        context['CALLBACK_URL'] = self.request.build_absolute_uri(
            reverse("cart:thank-you"))
        
        # Add grand_total to context for consistency with checkout page
        if order:
            context["grand_total"] = order.get_total()
        else:
            context["grand_total"] = "0.00"
            
        return context


class ConfirmOrderView(View):
    def post(self, request, *args, **kwargs):
        order = get_or_set_order_session(request)
        body = json.loads(request.body)
        Payment.objects.create(
            order=order,
            successful=True,
            raw_response=json.dumps(body),
            amount=float(body["purchase_units"][0]["amount"]["value"]),
            payment_method=Payment.PAYPAL
        )

        with transaction.atomic():
            # Update order status
            order.ordered = True
            order.status = Order.ORDERED
            order.ordered_date = timezone.now()

            order.save()

            # Update products stock
            for item in order.items.all():
                item.variant.quantity = item.variant.quantity - item.quantity
                item.variant.save()

                # Update supplies stock
                for ps in item.variant.variantsupply_set.all():
                    ps.supply.quantity = ps.supply.quantity - (ps.quantity_required * item.quantity)
                    ps.supply.save()

        # Clear order session
        del request.session['order_id']

        if order.user:
            try:
                send_new_order_email(order)
            except Exception as e:
                logger.exception(e)

        try:
            send_out_of_stock_email(notify_all_in_stock=False)
        except Exception as e:
            logger.exception(e)

        return JsonResponse({"data": "Success"})


class ThankYouView(TemplateResponseMixinWithMobileSupport, TemplateView):
    template_name = 'thanks.html'


class ShippingCostView(View):
    """Shipping cost calculation for checkout page only"""
    def get(self, request, *args, **kwargs):
        country = request.GET['country']
        state = request.GET['state']
        city = request.GET['city']
        order = get_or_set_order_session(self.request)

        total = calculate_total_shipping_cost(order, country, state, city)
        
        # Update the order with the calculated shipping cost (convert to Decimal)
        from decimal import Decimal
        order.total_shipping_cost = Decimal(str(total))
        order.save(update_fields=['total_shipping_cost'])

        shipping_cost = {
            'country': country,
            'state': state,
            'city': city,
            'total': str(total),
        }
        self.request.session['shipping_cost'] = shipping_cost

        return JsonResponse({'shipping_cost': total})


class GetCountryStates(View):
    def get(self, request, *args, **kwargs):
        country_name = request.GET['country']
        
        if country_name == 'United States':
            # Get states from admin panel tax rates
            try:
                states_with_rates = NEW_TaxRate.objects.filter(
                    is_active=True,
                    county__in=['', None],  # State-level rates only
                    city__in=['', None]
                ).values_list('state', flat=True).distinct()
                
                # Convert state codes to state names
                state_choices = dict(NEW_TaxRate.STATE_CHOICES)
                states = []
                
                for state_code in states_with_rates:
                    if state_code in state_choices:
                        states.append(state_choices[state_code])
                
                # If no tax rates configured, fall back to all states
                if not states:
                    states = [state[1] for state in NEW_TaxRate.STATE_CHOICES[1:]]
                    
            except Exception as e:
                states = [state[1] for state in get_us_states()]
        else:
            states = []  # No states for non-US countries
        
        return JsonResponse(states, safe=False)


class GetStateCities(View):
    def get(self, request, *args, **kwargs):
        country_name = request.GET['country']
        state_name = request.GET['state']
        
        if country_name == 'United States':
            state_code = get_state_code(state_name)
            if state_code:
                # Get cities from admin panel tax rates
                try:
                    cities_with_rates = NEW_TaxRate.objects.filter(
                        state=state_code,
                        is_active=True,
                        city__isnull=False
                    ).exclude(city='').values_list('city', flat=True).distinct()
                    
                    cities = list(cities_with_rates)
                    
                    # If no cities configured, fall back to default cities
                    if not cities:
                        cities = get_cities_for_state(state_code)
                        
                except Exception as e:
                    cities = get_cities_for_state(state_code)
            else:
                cities = []
        else:
            cities = []  # No cities for non-US countries
        
        return JsonResponse(cities, safe=False)


class UpdateTaxView(View):
    """NEW: Update tax calculation when location changes"""
    def post(self, request, *args, **kwargs):
        try:
            country = request.POST.get('country')
            state = request.POST.get('state')
            city = request.POST.get('city')
            
            # Get current order
            order = get_or_set_order_session(request)
            
            if order and country and state and city:
                # Update the order's shipping address first
                if not order.shipping_address:
                    from cart.models import Address
                    order.shipping_address = Address.objects.create(
                        country=country,
                        state=state,
                        city=city,
                        address_type='S'
                    )
                else:
                    order.shipping_address.country = country
                    order.shipping_address.state = state
                    order.shipping_address.city = city
                    order.shipping_address.save()
                
                order.save()
                
                # Calculate tax
                from NEW_tax_calculator.utils import NEW_calculate_tax_for_order
                tax_amount, tax_rate, is_exempt = NEW_calculate_tax_for_order(order)
                
                # Update order
                order.tax_amount = tax_amount
                order.is_tax_exempt = is_exempt
                order.save()
                
                # Calculate grand total
                grand_total = order.get_raw_total()
                
                return JsonResponse({
                    'success': True,
                    'tax_amount': float(tax_amount),
                    'tax_rate': str(tax_rate),
                    'is_exempt': is_exempt,
                    'grand_total': float(grand_total),
                    'shipping_cost': float(order.total_shipping_cost)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required data'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class OrdersListView(LoginRequiredMixin, ListView):
    template_name = 'order-list.html'
    model = Order
    ordering = ['-ordered_date']

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user, ordered=True)
        return queryset


class OrdersDetailView(DetailView):
    slug_field = 'reference_number'
    slug_url_kwarg = 'reference_number'
    template_name = 'order-detail.html'
    model = Order


class ApplyCouponView(View):
    def get(self, request, *args, **kwargs):
        code = request.GET.get('coupon_code')
        order = get_or_set_order_session(self.request)

        # Check if wholesale discount exists - if so, don't allow coupon
        if order.wholesale_discount > 0:
            return JsonResponse({"error": "Coupons cannot be used with wholesale discounts."})

        try:
            coupon = Coupon.objects.get(code=code, active=True)
        except Coupon.DoesNotExist:
            return JsonResponse({"error": "Coupon code in invalid."})
        # IMPORTANT: Check if coupon is created for specific user
        if coupon.created_for_user:
            # This coupon is user-specific
            if request.user.is_anonymous():
                return JsonResponse({"error": "Please login to use this coupon."})
            
            # Only the user for whom coupon was created can use it
            if coupon.created_for_user != request.user:
                return JsonResponse({"error": "This coupon is not valid for your account."})
        
        # Check single use per user
        if coupon.single_use_per_user:
            if request.user.is_anonymous():
                return JsonResponse({"error": "Please login to apply for this coupon."})
            if Order.objects.filter(user=request.user, coupon=coupon).exclude(status=Order.NOT_FINALIZED).exists():
                return JsonResponse({"error": "This coupon has been consumed before."})
        # Check minimum order amount (only if minimum_order_amount > 0)
        if coupon.minimum_order_amount > 0:
        if order.get_raw_subtotal() < coupon.minimum_order_amount:
            return JsonResponse(
                {
                    "error": f"The minimum order amount should be ${coupon.minimum_order_amount} for this coupon."
                }
            )

        order.coupon = coupon
        order.save()

        return JsonResponse({"coupon_discount_amount": order.get_coupon_discount_amount()})


class CartRecoveryView(View):
    """
    Recover abandoned cart from email link
    Restores cart session using order reference number
    When user clicks recovery link, delays the next abandoned cart email
    """
    def get(self, request, reference_number):
        try:
            # Find the order by reference number
            order = Order.objects.get(
                reference_number=reference_number,
                ordered=False  # Only recover non-finalized orders
            )
            
            # IMPORTANT: If user clicks recovery link, delay the next email
            # Update start_date to current time (this delays next email check)
            # Keep abandoned_email_count as is (don't reset completely)
            if order.abandoned_email_count > 0:
                from django.utils import timezone
                current_time = timezone.now()
                # Update start_date to delay next email, but keep email_count
                # This way, if 1st email was sent, next email (2nd) will be delayed
                Order.objects.filter(id=order.id).update(
                    start_date=current_time,
                    last_updated=current_time,
                    recovery_link_clicked_at=current_time,
                )
                order.refresh_from_db()
            
            # Set order ID in session to restore cart
            request.session['order_id'] = order.id
            
            # Redirect to cart page
            messages.success(request, f"Welcome back! Your cart has been restored with {order.items.count()} item(s).")
            return redirect('cart:summary')  # Fixed: Use correct URL name
            
        except Order.DoesNotExist:
            messages.error(request, "This cart link is invalid or has expired.")
            return redirect('cart:summary')  # Fixed: Use correct URL name
