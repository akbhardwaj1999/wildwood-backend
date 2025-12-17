"""
Quick test script to verify tax API is working
Run this to test if backend API is calculating tax correctly
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_tax_calculation():
    """Test tax calculation API"""
    print("\n" + "="*60)
    print("TESTING TAX CALCULATION API")
    print("="*60)
    
    url = f"{BASE_URL}/api/tax/update-address/"
    
    # Test data
    data = {
        "country": "United States",
        "state": "California",
        "city": "Los Angeles"
    }
    
    print(f"\n[REQUEST]")
    print(f"   URL: {url}")
    print(f"   Data: {json.dumps(data, indent=2)}")
    
    try:
        # Create session to maintain cookies
        session = requests.Session()
        
        # First, get cart to establish session
        cart_url = f"{BASE_URL}/api/cart/cart/"
        cart_response = session.get(cart_url)
        print(f"\n[Cart Session] Status: {cart_response.status_code}")
        
        # Now call tax API
        response = session.post(url, json=data)
        
        print(f"\n[Response] Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n[SUCCESS]")
            print(f"\n[Tax Calculation Results]")
            print(f"   Subtotal: ${result.get('subtotal', 0):.2f}")
            print(f"   Shipping Cost: ${result.get('shipping_cost', 0):.2f}")
            print(f"   Tax Amount: ${result.get('tax_amount', 0):.2f}")
            print(f"   Tax Rate: {result.get('tax_rate', '0.00%')}")
            print(f"   Grand Total: ${result.get('grand_total', 0):.2f}")
            print(f"   Location: {result.get('location', 'N/A')}")
            
            if result.get('tax_amount', 0) > 0:
                print(f"\n[OK] Tax is being calculated correctly!")
            else:
                print(f"\n[WARN] Tax is 0 - This could mean:")
                print(f"   1. No tax rate configured for this location")
                print(f"   2. Cart is empty")
                print(f"   3. Tax rate is 0% for this location")
        else:
            print(f"\n[ERROR] Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] Cannot connect to {BASE_URL}")
        print(f"   Make sure Django server is running:")
        print(f"   python manage.py runserver")
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")

if __name__ == '__main__':
    test_tax_calculation()
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")

