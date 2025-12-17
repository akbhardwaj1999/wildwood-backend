"""
Test Tax Calculator API with any address
Run this script to test tax calculation for different addresses
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_address(country, state, city=None, subtotal=100.00):
    """Test tax calculation for any address"""
    url = f"{BASE_URL}/api/tax/calculate/"
    
    data = {
        "country": country,
        "state": state,
        "subtotal": subtotal
    }
    
    if city:
        data["city"] = city
    
    location = f"{city}, " if city else ""
    location += f"{state}, {country}"
    
    try:
        response = requests.post(url, json=data, timeout=5)
        result = response.json()
        
        print(f"\n📍 Testing: {location}")
        print(f"   Status Code: {response.status_code}")
        
        if result.get('success'):
            print(f"   ✅ Success!")
            print(f"   Tax Rate: {result.get('tax_rate', 'N/A')}")
            print(f"   Tax Amount: ${result.get('tax_amount', 0):.2f}")
            print(f"   Subtotal: ${result.get('subtotal', subtotal):.2f}")
            print(f"   Grand Total: ${result.get('grand_total', subtotal):.2f}")
            
            if result.get('tax_amount', 0) == 0:
                print(f"   ℹ️  No tax rate configured for this location")
                print(f"   💡 Add tax rate in Django Admin to calculate tax")
            else:
                print(f"   Location: {result.get('location', 'N/A')}")
        else:
            print(f"   ❌ Failed!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except requests.exceptions.ConnectionError:
        print(f"\n📍 Testing: {location}")
        print(f"   ⚠️  Server not running at {BASE_URL}")
        print(f"   Please start Django server: python manage.py runserver")
        return None
    except Exception as e:
        print(f"\n📍 Testing: {location}")
        print(f"   ❌ Error: {str(e)}")
        return None


def test_update_address(country, state, city=None, zip_code=None):
    """Test update address API"""
    url = f"{BASE_URL}/api/tax/update-address/"
    
    data = {
        "country": country,
        "state": state,
        "address_line_1": "123 Test St",
        "first_name": "Test",
        "last_name": "User",
        "email_address": "test@example.com",
        "phone_number": "123-456-7890"
    }
    
    if city:
        data["city"] = city
    if zip_code:
        data["zip_code"] = zip_code
    
    try:
        # Create session to maintain cookies
        session = requests.Session()
        
        # First, get cart to create session
        cart_url = f"{BASE_URL}/api/cart/cart/"
        session.get(cart_url, timeout=5)
        
        # Add item to cart first
        add_item_url = f"{BASE_URL}/api/cart/cart/add-item/"
        # Note: You need to add item first, this is just for testing address update
        
        response = session.post(url, json=data, timeout=5)
        result = response.json()
        
        location = f"{city}, " if city else ""
        location += f"{state}, {country}"
        
        print(f"\n📍 Testing Update Address: {location}")
        print(f"   Status Code: {response.status_code}")
        
        if result.get('success'):
            print(f"   ✅ Success!")
            print(f"   Order ID: {result.get('order_id', 'N/A')}")
            print(f"   Tax Amount: ${result.get('tax_amount', 0):.2f}")
            print(f"   Tax Rate: {result.get('tax_rate', 'N/A')}")
            print(f"   Grand Total: ${result.get('grand_total', 0):.2f}")
        else:
            print(f"   ⚠️  {result.get('error', 'Unknown error')}")
            if 'empty' in result.get('error', '').lower():
                print(f"   💡 Add items to cart first")
        
        return result
        
    except requests.exceptions.ConnectionError:
        print(f"\n📍 Testing Update Address: {location}")
        print(f"   ⚠️  Server not running at {BASE_URL}")
        return None
    except Exception as e:
        print(f"\n📍 Testing Update Address: {location}")
        print(f"   ❌ Error: {str(e)}")
        return None


def main():
    """Run all tests"""
    print("="*60)
    print("TAX CALCULATOR API - ANY ADDRESS TESTING")
    print("="*60)
    print(f"\nTesting APIs at: {BASE_URL}")
    print("Make sure Django server is running!")
    print("\nTo start server: python manage.py runserver")
    print("\n" + "="*60)
    
    # Test different addresses
    print("\n📋 TEST 1: Calculate Tax API")
    print("-"*60)
    
    test_addresses = [
        ("United States", "California", "San Francisco"),
        ("United States", "California", "Los Angeles"),
        ("United States", "New York", "New York City"),
        ("United States", "Texas", "Houston"),
        ("United States", "Texas", "Dallas"),
        ("United States", "Florida", "Miami"),
        ("United States", "Illinois", "Chicago"),
        ("United States", "Alaska"),  # No tax rate (will return 0%)
        ("United States", "Hawaii"),  # No tax rate (will return 0%)
        ("Canada", "Ontario", "Toronto"),  # Different country
    ]
    
    results = []
    for country, state, *city in test_addresses:
        city = city[0] if city else None
        result = test_address(country, state, city)
        results.append((country, state, city, result))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    with_tax = sum(1 for _, _, _, r in results if r and r.get('tax_amount', 0) > 0)
    without_tax = sum(1 for _, _, _, r in results if r and (not r or r.get('tax_amount', 0) == 0))
    
    print(f"\n✅ Addresses with tax calculated: {with_tax}")
    print(f"ℹ️  Addresses without tax rate: {without_tax}")
    print(f"📊 Total tested: {len(results)}")
    
    print("\n" + "="*60)
    print("💡 TIPS")
    print("="*60)
    print("1. Add tax rates in Django Admin:")
    print("   http://localhost:8000/admin/NEW_tax_calculator/new_taxrate/add/")
    print("\n2. Priority: City > State > Country")
    print("   (City rate has highest priority)")
    print("\n3. No tax rate = 0% tax (gracefully handled)")
    print("\n4. You can test ANY address, just configure tax rate for it!")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60)


if __name__ == '__main__':
    main()

