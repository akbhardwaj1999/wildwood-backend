from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
import json

from .models import Country, State, City
from .utils import NEW_get_tax_rate, NEW_calculate_tax_for_order, NEW_is_user_tax_exempt
from cart.utils import get_or_set_order_session, calculate_total_shipping_cost
from cart.models import Address, Order


@method_decorator(csrf_exempt, name='dispatch')
class CountriesAPIView(View):
    """API to fetch all countries"""
    
    def get(self, request):
        try:
            countries = Country.objects.all().order_by('name')
            countries_data = [
                {
                    'id': country.id,
                    'name': country.name
                }
                for country in countries
            ]
            
            return JsonResponse({
                'success': True,
                'countries': countries_data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class StatesAPIView(View):
    """API to fetch states for a specific country"""
    
    def get(self, request, country_id):
        try:
            states = State.objects.filter(country_id=country_id).order_by('name')
            states_data = [
                {
                    'id': state.id,
                    'name': state.name,
                    'country_id': state.country_id
                }
                for state in states
            ]
            
            return JsonResponse({
                'success': True,
                'states': states_data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CitiesAPIView(View):
    """API to fetch cities for a specific state"""
    
    def get(self, request, state_id):
        try:
            cities = City.objects.filter(state_id=state_id).order_by('name')
            cities_data = [
                {
                    'id': city.id,
                    'name': city.name,
                    'state_id': city.state_id
                }
                for city in cities
            ]
            
            return JsonResponse({
                'success': True,
                'cities': cities_data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def calculate_tax_api(request):
    """
    API endpoint to calculate tax based on address/location for checkout page.
    
    Accepts:
    - country (string): Country name
    - state (string): State name
    - city (string, optional): City name
    - subtotal (decimal, optional): Subtotal amount. If not provided, uses current order subtotal
    
    Returns:
    - tax_amount: Calculated tax amount
    - tax_rate: Tax rate percentage
    - tax_rate_decimal: Tax rate as decimal (0.0875 for 8.75%)
    - is_exempt: Whether user is tax exempt
    - subtotal: Subtotal amount
    - grand_total: Total including tax
    - location: Location string for tax rate
    """
    try:
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
        
        country = data.get('country', '').strip()
        state = data.get('state', '').strip()
        city = data.get('city', '').strip()
        subtotal = data.get('subtotal')
        
        # Validate required fields
        if not country or not state:
            return Response({
                'success': False,
                'error': 'Country and state are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get current order from session
        order = get_or_set_order_session(request)
        
        # If subtotal not provided, use order subtotal
        if subtotal is None:
            if order and order.items.exists():
                subtotal = float(order.get_raw_subtotal())
            else:
                subtotal = 0.0
        else:
            subtotal = float(subtotal)
        
        # Check if user is tax exempt
        is_exempt = False
        if request.user.is_authenticated:
            is_exempt = NEW_is_user_tax_exempt(request.user)
        
        # If user is exempt, return zero tax
        if is_exempt:
            return Response({
                'success': True,
                'tax_amount': 0.0,
                'tax_rate': '0.00%',
                'tax_rate_decimal': 0.0,
                'is_exempt': True,
                'subtotal': subtotal,
                'grand_total': subtotal,
                'location': 'Tax Exempt',
                'exemption_reason': 'User has valid tax exemption'
            }, status=status.HTTP_200_OK)
        
        # Get tax rate for location
        tax_rate_obj = NEW_get_tax_rate(
            country=country,
            state=state,
            city=city if city else None
        )
        
        if not tax_rate_obj:
            # No tax rate found for this location
            return Response({
                'success': True,
                'tax_amount': 0.0,
                'tax_rate': '0.00%',
                'tax_rate_decimal': 0.0,
                'is_exempt': False,
                'subtotal': subtotal,
                'grand_total': subtotal,
                'location': f'{city}, {state}, {country}' if city else f'{state}, {country}',
                'message': 'No tax rate found for this location'
            }, status=status.HTTP_200_OK)
        
        # Calculate tax amount
        tax_rate_decimal = float(tax_rate_obj.rate)
        tax_amount = subtotal * tax_rate_decimal
        grand_total = subtotal + tax_amount
        
        return Response({
            'success': True,
            'tax_amount': round(tax_amount, 2),
            'tax_rate': f'{tax_rate_decimal * 100:.2f}%',
            'tax_rate_decimal': tax_rate_decimal,
            'is_exempt': False,
            'subtotal': round(subtotal, 2),
            'grand_total': round(grand_total, 2),
            'location': str(tax_rate_obj),
            'tax_type': tax_rate_obj.tax_type
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def update_address_and_calculate_tax(request):
    """
    API endpoint to update order address and calculate tax in one call.
    This is the main endpoint for checkout page.
    
    Accepts:
    - country (string): Country name
    - state (string): State name
    - city (string, optional): City name
    - zip_code (string, optional): ZIP code
    - address_line_1 (string, optional): Street address
    - address_line_2 (string, optional): Additional address info
    - first_name (string, optional): First name
    - last_name (string, optional): Last name
    - email_address (string, optional): Email
    - phone_number (string, optional): Phone
    
    Returns:
    - order_id: Order ID
    - tax_amount: Calculated tax amount
    - tax_rate: Tax rate percentage
    - is_exempt: Whether user is tax exempt
    - subtotal: Subtotal after discounts
    - shipping_cost: Shipping cost
    - grand_total: Total including tax and shipping
    """
    try:
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
        
        country = data.get('country', '').strip()
        state = data.get('state', '').strip()
        city = data.get('city', '').strip()
        zip_code = data.get('zip_code', '').strip()
        
        # Validate required fields
        if not country or not state:
            return Response({
                'success': False,
                'error': 'Country and state are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get current order
        order = get_or_set_order_session(request)
        
        if not order or not order.items.exists():
            return Response({
                'success': False,
                'error': 'Cart is empty. Please add items to cart first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update or create shipping address
        if order.shipping_address:
            address = order.shipping_address
            address.country = country
            address.state = state
            address.city = city
            if zip_code:
                address.zip_code = zip_code
            if data.get('address_line_1'):
                address.address_line_1 = data.get('address_line_1')
            if data.get('address_line_2'):
                address.address_line_2 = data.get('address_line_2')
            if data.get('first_name'):
                address.first_name = data.get('first_name')
            if data.get('last_name'):
                address.last_name = data.get('last_name')
            if data.get('email_address'):
                address.email_address = data.get('email_address')
            if data.get('phone_number'):
                address.phone_number = data.get('phone_number')
            address.save()
        else:
            # Create new shipping address
            address = Address.objects.create(
                user=request.user if request.user.is_authenticated else None,
                country=country,
                state=state,
                city=city,
                zip_code=zip_code or '',
                address_line_1=data.get('address_line_1', ''),
                address_line_2=data.get('address_line_2', ''),
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                email_address=data.get('email_address', ''),
                phone_number=data.get('phone_number', ''),
                address_type=Address.SHIPPING
            )
            order.shipping_address = address
            order.save()
        
        # Recalculate shipping cost with updated address (handle gracefully if settings missing)
        try:
            from django.conf import settings as django_settings
            # Check if warehouse settings exist
            if hasattr(django_settings, 'WAREHOUSE_COUNTRY') and django_settings.WAREHOUSE_COUNTRY:
                # Pass updated country, state, city explicitly for accurate shipping calculation
                shipping_cost = calculate_total_shipping_cost(order, country=country, state=state, city=city if city else None)
                # Convert to Decimal if it's not already
                if not isinstance(shipping_cost, Decimal):
                    shipping_cost = Decimal(str(shipping_cost))
            else:
                # Warehouse settings not configured - shipping cost will be 0
                shipping_cost = Decimal('0.00')
            order.total_shipping_cost = shipping_cost
            order.save(update_fields=['total_shipping_cost'])
        except Exception as e:
            # If shipping calculation fails, set to 0 and log error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Shipping cost calculation failed: {str(e)}", exc_info=True)
            shipping_cost = Decimal('0.00')
            order.total_shipping_cost = shipping_cost
            order.save(update_fields=['total_shipping_cost'])
        
        # Apply wholesale discount if user is wholesale
        wholesale_discount_percentage = None
        try:
            from NEW_wholesale_discounts.utils import NEW_apply_wholesale_discount_to_order
            from NEW_wholesale_discounts.models import NEW_WholesaleDiscountConfig
            wholesale_discount = NEW_apply_wholesale_discount_to_order(order)
            order.wholesale_discount = wholesale_discount
            order.save(update_fields=['wholesale_discount'])
            
            # Get discount percentage for display
            if wholesale_discount > 0:
                subtotal_before_discount = order.get_raw_subtotal()
                config = NEW_WholesaleDiscountConfig.objects.filter(is_active=True).first()
                if config and subtotal_before_discount > 0:
                    wholesale_discount_percentage = float(config.get_discount_for_amount(subtotal_before_discount))
        except Exception as e:
            # If wholesale discount fails, set to 0
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Wholesale discount calculation failed: {str(e)}")
            order.wholesale_discount = Decimal('0.00')
            order.save(update_fields=['wholesale_discount'])
        
        # Calculate tax (on subtotal after wholesale discount)
        tax_amount, tax_rate_obj, is_exempt = NEW_calculate_tax_for_order(order)
        order.tax_amount = tax_amount
        order.is_tax_exempt = is_exempt
        order.save(update_fields=['tax_amount', 'is_tax_exempt'])
        
        # Get order totals
        subtotal = float(order.get_raw_subtotal())
        wholesale_discount_float = float(order.wholesale_discount)
        shipping_cost_float = float(shipping_cost)
        tax_amount_float = float(tax_amount)
        grand_total = float(order.get_total())
        
        # Prepare response
        response_data = {
            'success': True,
            'order_id': order.id,
            'subtotal': round(subtotal, 2),
            'wholesale_discount': round(wholesale_discount_float, 2),
            'wholesale_discount_percentage': round(wholesale_discount_percentage, 2) if wholesale_discount_percentage else None,
            'shipping_cost': round(shipping_cost_float, 2),
            'tax_amount': round(tax_amount_float, 2),
            'grand_total': round(grand_total, 2),
            'is_exempt': is_exempt,
        }
        
        if tax_rate_obj:
            response_data['tax_rate'] = f'{float(tax_rate_obj.rate) * 100:.2f}%'
            response_data['tax_rate_decimal'] = float(tax_rate_obj.rate)
            response_data['location'] = str(tax_rate_obj)
            response_data['tax_type'] = tax_rate_obj.tax_type
        else:
            response_data['tax_rate'] = '0.00%'
            response_data['tax_rate_decimal'] = 0.0
            response_data['location'] = f'{city}, {state}, {country}' if city else f'{state}, {country}'
            response_data['message'] = 'No tax rate found for this location'
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
