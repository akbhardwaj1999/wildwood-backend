"""
Comprehensive Test Runner - WildWud Backend
Tests all major components of the application
"""
import os
import sys
import django
from django.core.management import call_command
from django.test.utils import get_runner
from django.conf import settings

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wildwud.settings')
django.setup()

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_section(text):
    """Print formatted section"""
    print("\n" + "-"*70)
    print(f"  {text}")
    print("-"*70)

def safe_print(text):
    """Print text with safe encoding"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Replace emojis with ASCII equivalents
        text = text.replace('✅', '[OK]')
        text = text.replace('❌', '[FAIL]')
        text = text.replace('⚠️', '[WARN]')
        text = text.replace('⏭️', '[SKIP]')
        text = text.replace('🎉', '[SUCCESS]')
        print(text)

def check_migrations():
    """Check if migrations are up to date"""
    print_header("CHECKING MIGRATIONS")
    try:
        call_command('makemigrations', '--check', '--dry-run', verbosity=0)
        safe_print("[OK] All migrations are up to date")
        return True
    except SystemExit:
        safe_print("[WARN] Pending migrations detected")
        print("   Run: python manage.py makemigrations")
        print("   Then: python manage.py migrate")
        return False

def run_django_tests():
    """Run Django test suite"""
    print_header("RUNNING DJANGO TEST SUITE")
    
    test_modules = [
        'accounts.tests',
        'cart.tests',
        'galleryItem.tests',
        'NEW_tax_calculator.tests',
    ]
    
    results = {}
    
    for module in test_modules:
        print_section(f"Testing: {module}")
        try:
            result = call_command('test', module, verbosity=2, keepdb=True)
            results[module] = "[OK] PASSED"
        except SystemExit as e:
            if e.code == 0:
                results[module] = "[OK] PASSED"
            else:
                results[module] = f"[FAIL] FAILED (exit code: {e.code})"
        except Exception as e:
            results[module] = f"[FAIL] ERROR: {str(e)}"
    
    return results

def check_database_tables():
    """Check if all required database tables exist"""
    print_header("CHECKING DATABASE TABLES")
    
    from django.db import connection
    cursor = connection.cursor()
    
    required_tables = [
        'accounts_user',
        'cart_order',
        'cart_orderitem',
        'cart_address',
        'cart_coupon',
        'galleryItem_category',
        'galleryItem_galleryitem',
        'galleryItem_variant',
        'NEW_tax_calculator_country',
        'NEW_tax_calculator_state',
        'NEW_tax_calculator_city',
        'NEW_tax_calculator_new_taxrate',
    ]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    missing_tables = []
    for table in required_tables:
        if table in existing_tables:
            safe_print(f"[OK] {table}")
        else:
            safe_print(f"[FAIL] {table} - MISSING")
            missing_tables.append(table)
    
    if missing_tables:
        safe_print(f"\n[WARN] {len(missing_tables)} table(s) missing")
        print("   Run: python manage.py migrate")
        return False
    else:
        safe_print(f"\n[OK] All {len(required_tables)} required tables exist")
        return True

def check_media_files():
    """Check media files configuration"""
    print_header("CHECKING MEDIA FILES CONFIGURATION")
    
    from django.conf import settings
    
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"MEDIA_URL: {settings.MEDIA_URL}")
    print(f"DEBUG: {settings.DEBUG}")
    
    # Check if media directory exists
    if os.path.exists(settings.MEDIA_ROOT):
        safe_print(f"[OK] Media directory exists: {settings.MEDIA_ROOT}")
        
        # Count files in media directory
        media_files = []
        for root, dirs, files in os.walk(settings.MEDIA_ROOT):
            for file in files:
                media_files.append(os.path.join(root, file))
        
        safe_print(f"[OK] Found {len(media_files)} media file(s)")
        
        if len(media_files) == 0:
            safe_print("[WARN] No media files found")
            print("   You may need to import products or sync media files")
    else:
        safe_print(f"[WARN] Media directory does not exist: {settings.MEDIA_ROOT}")
        print("   Creating directory...")
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        safe_print("[OK] Media directory created")
    
    return True

def check_api_endpoints():
    """Check if API endpoints are accessible"""
    print_header("CHECKING API ENDPOINTS")
    
    from django.urls import reverse
    from django.test import Client
    
    client = Client()
    
    endpoints = [
        ('/api/gallery/items/', 'GET', 'Gallery Items'),
        ('/api/cart/cart/', 'GET', 'Cart'),
        ('/api/tax/countries/', 'GET', 'Tax Countries'),
    ]
    
    results = {}
    
    for url, method, name in endpoints:
        try:
            if method == 'GET':
                response = client.get(url)
                if response.status_code in [200, 401, 403]:
                    results[name] = f"[OK] {response.status_code}"
                else:
                    results[name] = f"[WARN] {response.status_code}"
            else:
                results[name] = "[SKIP] Skipped (POST requires data)"
        except Exception as e:
            results[name] = f"[FAIL] Error: {str(e)}"
    
    for name, result in results.items():
        print(f"{result} - {name}")
    
    return results

def check_tax_rates():
    """Check if tax rates are configured"""
    print_header("CHECKING TAX RATES")
    
    try:
        from NEW_tax_calculator.models import NEW_TaxRate, Country, State, City
        
        countries = Country.objects.count()
        states = State.objects.count()
        cities = City.objects.count()
        tax_rates = NEW_TaxRate.objects.filter(is_active=True).count()
        
        print(f"Countries: {countries}")
        print(f"States: {states}")
        print(f"Cities: {cities}")
        print(f"Active Tax Rates: {tax_rates}")
        
        if tax_rates > 0:
            safe_print(f"\n[OK] {tax_rates} active tax rate(s) configured")
            print("\nSample tax rates:")
            for rate in NEW_TaxRate.objects.filter(is_active=True)[:5]:
                print(f"  - {rate}")
        else:
            safe_print("\n[WARN] No active tax rates found")
            print("   Add tax rates in Django Admin:")
            print("   http://localhost:8000/admin/NEW_tax_calculator/new_taxrate/add/")
        
        return tax_rates > 0
    except Exception as e:
        safe_print(f"[FAIL] Error checking tax rates: {str(e)}")
        print("   Make sure migrations are run:")
        print("   python manage.py migrate NEW_tax_calculator")
        return False

def check_products():
    """Check if products exist"""
    print_header("CHECKING PRODUCTS")
    
    try:
        from galleryItem.models import GalleryItem, Variant, Category
        
        categories = Category.objects.count()
        products = GalleryItem.objects.filter(active=True).count()
        variants = Variant.objects.filter(active=True).count()
        
        print(f"Categories: {categories}")
        print(f"Active Products: {products}")
        print(f"Active Variants: {variants}")
        
        if products > 0:
            safe_print(f"\n[OK] {products} active product(s) found")
        else:
            safe_print("\n[WARN] No active products found")
            print("   Import products using:")
            print("   python manage.py import_products simple_matched_data.json")
        
        return products > 0
    except Exception as e:
        safe_print(f"[FAIL] Error checking products: {str(e)}")
        return False

def generate_summary(results):
    """Generate test summary"""
    print_header("TEST SUMMARY")
    
    total_checks = len(results)
    passed = sum(1 for r in results.values() if '[OK]' in str(r) or 'PASSED' in str(r))
    failed = total_checks - passed
    
    print(f"Total Checks: {total_checks}")
    safe_print(f"[OK] Passed: {passed}")
    safe_print(f"[FAIL] Failed: {failed}")
    
    if failed == 0:
        safe_print("\n[SUCCESS] All checks passed!")
    else:
        safe_print("\n[WARN] Some checks failed. Please review the output above.")
    
    return failed == 0

if __name__ == '__main__':
    print("\n" + "="*70)
    print("  WILDWUD BACKEND - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    all_results = {}
    
    # 1. Check migrations
    all_results['Migrations'] = check_migrations()
    
    # 2. Check database tables
    all_results['Database Tables'] = check_database_tables()
    
    # 3. Check media files
    all_results['Media Files'] = check_media_files()
    
    # 4. Check products
    all_results['Products'] = check_products()
    
    # 5. Check tax rates
    all_results['Tax Rates'] = check_tax_rates()
    
    # 6. Check API endpoints
    api_results = check_api_endpoints()
    all_results['API Endpoints'] = api_results
    
    # 7. Run Django tests
    print("\n" + "="*70)
    print("  Would you like to run Django test suite?")
    print("  (This may take a few minutes)")
    print("="*70)
    print("\nTo run tests manually:")
    print("  python manage.py test accounts.tests -v 2")
    print("  python manage.py test cart.tests -v 2")
    print("  python manage.py test galleryItem.tests -v 2")
    print("  python manage.py test NEW_tax_calculator.tests -v 2")
    print("\nOr run all tests:")
    print("  python manage.py test -v 2")
    
    # Generate summary
    generate_summary(all_results)
    
    print("\n" + "="*70)
    print("  TEST SUITE COMPLETE")
    print("="*70 + "\n")

