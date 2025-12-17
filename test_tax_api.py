"""
Simple test script for Tax Calculator API
Run this script to test the tax calculation APIs
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wildwud.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from decimal import Decimal
from datetime import date, timedelta

from NEW_tax_calculator.api_views import calculate_tax_api, update_address_and_calculate_tax
from NEW_tax_calculator.models import Country, State, City, NEW_TaxRate
from cart.models import Order, OrderItem, Address
from galleryItem.models import Category, GalleryItem, Variant


def create_test_data():
    """Create test data for testing"""
    print("Creating test data...")
    
    # Create country, state, city
    country, _ = Country.objects.get_or_create(name='United States')
    state, _ = State.objects.get_or_create(name='California', country=country)
    city, _ = City.objects.get_or_create(name='San Francisco', state=state)
    
    # Create tax rates
    state_tax_rate, _ = NEW_TaxRate.objects.get_or_create(
        country=country,
        state=state,
        city=None,
        defaults={
            'rate': Decimal('0.0875'),  # 8.75%
            'tax_type': 'sales',
            'effective_date': date.today() - timedelta(days=30),
            'is_active': True
        }
    )
    
    city_tax_rate, _ = NEW_TaxRate.objects.get_or_create(
        country=country,
        state=state,
        city=city,
        defaults={
            'rate': Decimal('0.0900'),  # 9.00%
            'tax_type': 'sales',
            'effective_date': date.today() - timedelta(days=30),
            'is_active': True
        }
    )
    
    # Create category and product
    category, _ = Category.objects.get_or_create(
        title='Test Category',
        defaults={'description': 'Test Description'}
    )
    
    product, _ = GalleryItem.objects.get_or_create(
        title='Test Product',
        defaults={
            'description': 'Test Product Description',
            'category': category,
            'active': True
        }
    )
    
    variant, _ = Variant.objects.get_or_create(
        product=product,
        title='Test Variant',
        defaults={
            'price': Decimal('100.00'),
            'quantity': 10,
            'volume': 100,
            'weight': 200,
            'active': True
        }
    )
    
    print("✓ Test data created successfully!")
    return country, state, city, variant


def test_calculate_tax_api():
    """Test calculate_tax_api endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Calculate Tax API")
    print("="*60)
    
    factory = RequestFactory()
    
    # Test 1: Calculate tax with country and state
    print("\n1. Testing with country and state only...")
    request = factory.post('/api/tax/calculate/', {
        'country': 'United States',
        'state': 'California',
        'subtotal': 100.00
    }, content_type='application/json')
    
    # Add session middleware
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    response = calculate_tax_api(request)
    
    if response.status_code == 200:
        data = response.data
        print(f"   ✓ Success!")
        print(f"   Tax Amount: ${data['tax_amount']}")
        print(f"   Tax Rate: {data['tax_rate']}")
        print(f"   Subtotal: ${data['subtotal']}")
        print(f"   Grand Total: ${data['grand_total']}")
        assert data['tax_amount'] == 8.75, f"Expected 8.75, got {data['tax_amount']}"
        assert data['tax_rate'] == '8.75%', f"Expected 8.75%, got {data['tax_rate']}"
    else:
        print(f"   ✗ Failed with status {response.status_code}")
        print(f"   Error: {response.data}")
        return False
    
    # Test 2: Calculate tax with city (should use city rate)
    print("\n2. Testing with city (should use city rate 9.00%)...")
    request = factory.post('/api/tax/calculate/', {
        'country': 'United States',
        'state': 'California',
        'city': 'San Francisco',
        'subtotal': 100.00
    }, content_type='application/json')
    
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    response = calculate_tax_api(request)
    
    if response.status_code == 200:
        data = response.data
        print(f"   ✓ Success!")
        print(f"   Tax Amount: ${data['tax_amount']}")
        print(f"   Tax Rate: {data['tax_rate']}")
        assert data['tax_amount'] == 9.0, f"Expected 9.0, got {data['tax_amount']}"
        assert data['tax_rate'] == '9.00%', f"Expected 9.00%, got {data['tax_rate']}"
    else:
        print(f"   ✗ Failed with status {response.status_code}")
        return False
    
    # Test 3: Missing required fields
    print("\n3. Testing with missing country...")
    request = factory.post('/api/tax/calculate/', {
        'state': 'California',
        'subtotal': 100.00
    }, content_type='application/json')
    
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    response = calculate_tax_api(request)
    
    if response.status_code == 400:
        print(f"   ✓ Correctly rejected with status {response.status_code}")
        print(f"   Error: {response.data.get('error', 'N/A')}")
    else:
        print(f"   ✗ Should have failed with 400, got {response.status_code}")
        return False
    
    print("\n✓ All Calculate Tax API tests passed!")
    return True


def test_update_address_api(variant):
    """Test update_address_and_calculate_tax endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Update Address and Calculate Tax API")
    print("="*60)
    
    factory = RequestFactory()
    
    # Create order with items
    order = Order.objects.create(user=None)
    OrderItem.objects.create(
        order=order,
        variant=variant,
        quantity=2
    )
    
    # Test 1: Update address and calculate tax
    print("\n1. Testing update address with order...")
    request = factory.post('/api/tax/update-address/', {
        'country': 'United States',
        'state': 'California',
        'city': 'San Francisco',
        'zip_code': '94102',
        'address_line_1': '123 Main St',
        'first_name': 'John',
        'last_name': 'Doe',
        'email_address': 'john@example.com',
        'phone_number': '123-456-7890'
    }, content_type='application/json')
    
    # Add session middleware
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session['order_id'] = order.id
    request.session.save()
    
    response = update_address_and_calculate_tax(request)
    
    if response.status_code == 200:
        data = response.data
        print(f"   ✓ Success!")
        print(f"   Order ID: {data['order_id']}")
        print(f"   Subtotal: ${data['subtotal']}")
        print(f"   Tax Amount: ${data['tax_amount']}")
        print(f"   Tax Rate: {data['tax_rate']}")
        print(f"   Grand Total: ${data['grand_total']}")
        
        # Verify address was created
        order.refresh_from_db()
        if order.shipping_address:
            print(f"   ✓ Address created: {order.shipping_address.city}, {order.shipping_address.state}")
            assert order.shipping_address.country == 'United States'
            assert order.shipping_address.state == 'California'
            assert order.shipping_address.city == 'San Francisco'
        else:
            print(f"   ✗ Address was not created")
            return False
        
        # Verify tax was calculated
        assert float(order.tax_amount) > 0, "Tax amount should be greater than 0"
    else:
        print(f"   ✗ Failed with status {response.status_code}")
        print(f"   Error: {response.data}")
        return False
    
    # Test 2: Empty cart
    print("\n2. Testing with empty cart...")
    empty_order = Order.objects.create(user=None)
    
    request = factory.post('/api/tax/update-address/', {
        'country': 'United States',
        'state': 'California'
    }, content_type='application/json')
    
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session['order_id'] = empty_order.id
    request.session.save()
    
    response = update_address_and_calculate_tax(request)
    
    if response.status_code == 400:
        print(f"   ✓ Correctly rejected empty cart with status {response.status_code}")
        print(f"   Error: {response.data.get('error', 'N/A')}")
    else:
        print(f"   ✗ Should have failed with 400, got {response.status_code}")
        return False
    
    print("\n✓ All Update Address API tests passed!")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TAX CALCULATOR API TESTS")
    print("="*60)
    
    try:
        # Create test data
        country, state, city, variant = create_test_data()
        
        # Run tests
        test1_passed = test_calculate_tax_api()
        test2_passed = test_update_address_api(variant)
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Calculate Tax API: {'✓ PASSED' if test1_passed else '✗ FAILED'}")
        print(f"Update Address API: {'✓ PASSED' if test2_passed else '✗ FAILED'}")
        
        if test1_passed and test2_passed:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())


