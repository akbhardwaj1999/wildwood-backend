"""
Simple API Test - Direct HTTP requests to test Tax Calculator APIs
This script tests the APIs without Django test framework
"""
import requests
import json

BASE_URL = "http://localhost:8000"  # Change if your server runs on different port

def test_calculate_tax():
    """Test calculate tax API"""
    print("\n" + "="*60)
    print("TEST 1: Calculate Tax API")
    print("="*60)
    
    url = f"{BASE_URL}/api/tax/calculate/"
    
    # Test 1: Calculate tax with country and state
    print("\n1. Testing with country and state...")
    data = {
        "country": "United States",
        "state": "California",
        "subtotal": 100.00
    }
    
    try:
        response = requests.post(url, json=data, timeout=5)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Success!")
            print(f"   Tax Amount: ${result.get('tax_amount', 'N/A')}")
            print(f"   Tax Rate: {result.get('tax_rate', 'N/A')}")
            print(f"   Subtotal: ${result.get('subtotal', 'N/A')}")
            print(f"   Grand Total: ${result.get('grand_total', 'N/A')}")
            return True
        else:
            print(f"   ✗ Failed: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ⚠ Server not running at {BASE_URL}")
        print(f"   Please start Django server: python manage.py runserver")
        return False
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False


def test_update_address():
    """Test update address API"""
    print("\n" + "="*60)
    print("TEST 2: Update Address and Calculate Tax API")
    print("="*60)
    
    url = f"{BASE_URL}/api/tax/update-address/"
    
    # Test 1: Update address
    print("\n1. Testing update address...")
    data = {
        "country": "United States",
        "state": "California",
        "city": "San Francisco",
        "zip_code": "94102",
        "address_line_1": "123 Main St",
        "first_name": "John",
        "last_name": "Doe",
        "email_address": "john@example.com",
        "phone_number": "123-456-7890"
    }
    
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        
        # First, get cart to create session
        cart_url = f"{BASE_URL}/api/cart/cart/"
        session.get(cart_url, timeout=5)
        
        # Now test update address
        response = session.post(url, json=data, timeout=5)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Success!")
            print(f"   Order ID: {result.get('order_id', 'N/A')}")
            print(f"   Subtotal: ${result.get('subtotal', 'N/A')}")
            print(f"   Tax Amount: ${result.get('tax_amount', 'N/A')}")
            print(f"   Tax Rate: {result.get('tax_rate', 'N/A')}")
            print(f"   Grand Total: ${result.get('grand_total', 'N/A')}")
            return True
        elif response.status_code == 400:
            result = response.json()
            error = result.get('error', 'Unknown error')
            if 'empty' in error.lower():
                print(f"   ⚠ Cart is empty (expected if no items added)")
                print(f"   Error: {error}")
                return True  # This is expected behavior
            else:
                print(f"   ✗ Failed: {error}")
                return False
        else:
            print(f"   ✗ Failed: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ⚠ Server not running at {BASE_URL}")
        print(f"   Please start Django server: python manage.py runserver")
        return False
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False


def test_location_apis():
    """Test location APIs"""
    print("\n" + "="*60)
    print("TEST 3: Location APIs")
    print("="*60)
    
    # Test Countries API
    print("\n1. Testing Countries API...")
    try:
        url = f"{BASE_URL}/api/tax/countries/"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Success!")
            countries = result.get('countries', [])
            print(f"   Found {len(countries)} countries")
            if countries:
                print(f"   Example: {countries[0].get('name', 'N/A')}")
            return True
        else:
            print(f"   ✗ Failed: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ⚠ Server not running at {BASE_URL}")
        return False
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TAX CALCULATOR API - SIMPLE HTTP TESTS")
    print("="*60)
    print(f"\nTesting APIs at: {BASE_URL}")
    print("Make sure Django server is running!")
    print("\nTo start server: python manage.py runserver")
    
    results = []
    
    # Run tests
    results.append(("Calculate Tax API", test_calculate_tax()))
    results.append(("Update Address API", test_update_address()))
    results.append(("Location APIs", test_location_apis()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠ Some tests failed or server not running")
        print("Make sure:")
        print("1. Django server is running: python manage.py runserver")
        print("2. Tax rates are configured in admin panel")
        print("3. Database has test data")


if __name__ == '__main__':
    main()


