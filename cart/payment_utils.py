"""
Payment processing utilities for PayPal and Stripe integration
"""
import requests
import json
from decimal import Decimal
from django.conf import settings
from django.utils import timezone


def verify_paypal_order(paypal_order_id, order_total):
    """
    Verify and capture PayPal order payment
    
    Args:
        paypal_order_id: PayPal order ID from frontend
        order_total: Order total amount to verify
    
    Returns:
        dict: {
            'success': bool,
            'transaction_id': str,
            'raw_response': dict,
            'error': str (if failed)
        }
    """
    try:
        # Get PayPal credentials from settings
        paypal_client_id = getattr(settings, 'PAYPAL_CLIENT_ID', None)
        paypal_client_secret = getattr(settings, 'PAYPAL_CLIENT_SECRET', None)
        paypal_mode = getattr(settings, 'PAYPAL_MODE', 'sandbox')  # 'sandbox' or 'live'
        
        if not paypal_client_id or not paypal_client_secret:
            return {
                'success': False,
                'error': 'PayPal credentials not configured in settings'
            }
        
        # Determine PayPal API base URL
        if paypal_mode == 'live':
            paypal_base_url = 'https://api-m.paypal.com'
        else:
            paypal_base_url = 'https://api-m.sandbox.paypal.com'
        
        # Step 1: Get access token
        token_url = f'{paypal_base_url}/v1/oauth2/token'
        token_headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en_US',
        }
        token_data = {
            'grant_type': 'client_credentials'
        }
        
        token_response = requests.post(
            token_url,
            headers=token_headers,
            auth=(paypal_client_id, paypal_client_secret),
            data=token_data
        )
        
        if token_response.status_code != 200:
            return {
                'success': False,
                'error': f'Failed to get PayPal access token: {token_response.text}'
            }
        
        access_token = token_response.json()['access_token']
        
        # Step 2: Verify the order
        order_url = f'{paypal_base_url}/v2/checkout/orders/{paypal_order_id}'
        order_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        order_response = requests.get(order_url, headers=order_headers)
        
        if order_response.status_code != 200:
            return {
                'success': False,
                'error': f'Failed to verify PayPal order: {order_response.text}'
            }
        
        order_data = order_response.json()
        
        # Check order status
        if order_data['status'] != 'APPROVED':
            return {
                'success': False,
                'error': f'PayPal order not approved. Status: {order_data["status"]}'
            }
        
        # Verify amount
        paypal_amount = float(order_data['purchase_units'][0]['amount']['value'])
        if abs(paypal_amount - float(order_total)) > 0.01:  # Allow small rounding differences
            return {
                'success': False,
                'error': f'Amount mismatch. Expected: {order_total}, Got: {paypal_amount}'
            }
        
        # Step 3: Capture the payment
        capture_url = f'{paypal_base_url}/v2/checkout/orders/{paypal_order_id}/capture'
        capture_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        capture_response = requests.post(capture_url, headers=capture_headers, json={})
        
        if capture_response.status_code not in [200, 201]:
            return {
                'success': False,
                'error': f'Failed to capture PayPal payment: {capture_response.text}'
            }
        
        capture_data = capture_response.json()
        
        # Check capture status
        if capture_data['status'] != 'COMPLETED':
            return {
                'success': False,
                'error': f'PayPal payment not completed. Status: {capture_data["status"]}'
            }
        
        # Get transaction ID
        transaction_id = capture_data['purchase_units'][0]['payments']['captures'][0]['id']
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'raw_response': capture_data,
            'amount': float(capture_data['purchase_units'][0]['payments']['captures'][0]['amount']['value'])
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'PayPal payment processing error: {str(e)}'
        }


def process_stripe_payment(stripe_token, order_total, currency='usd'):
    """
    Process Stripe payment
    
    Args:
        stripe_token: Stripe payment token from frontend
        order_total: Order total amount
        currency: Currency code (default: 'usd')
    
    Returns:
        dict: {
            'success': bool,
            'transaction_id': str,
            'raw_response': dict,
            'error': str (if failed)
        }
    """
    try:
        import stripe
        
        # Get Stripe secret key from settings
        stripe_secret_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        
        if not stripe_secret_key:
            return {
                'success': False,
                'error': 'Stripe secret key not configured in settings'
            }
        
        # Set Stripe API key
        stripe.api_key = stripe_secret_key
        
        # Create charge
        charge = stripe.Charge.create(
            amount=int(float(order_total) * 100),  # Convert to cents
            currency=currency,
            source=stripe_token,
            description=f'Order payment'
        )
        
        if charge.status == 'succeeded':
            return {
                'success': True,
                'transaction_id': charge.id,
                'raw_response': charge.to_dict(),
                'amount': float(charge.amount) / 100  # Convert back from cents
            }
        else:
            return {
                'success': False,
                'error': f'Stripe charge not succeeded. Status: {charge.status}'
            }
            
    except stripe.error.CardError as e:
        return {
            'success': False,
            'error': f'Stripe card error: {str(e)}'
        }
    except stripe.error.StripeError as e:
        return {
            'success': False,
            'error': f'Stripe error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Stripe payment processing error: {str(e)}'
        }

