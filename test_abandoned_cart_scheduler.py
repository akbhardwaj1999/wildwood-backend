"""
Test script for Abandoned Cart Scheduler
This script tests if the scheduler is working correctly
"""
import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wildwud.settings')
django.setup()

from cart.models import Order, OrderItem
from galleryItem.models import Variant, GalleryItem
from django.contrib.auth import get_user_model

User = get_user_model()

def test_scheduler_setup():
    """Test if scheduler can be imported and configured"""
    print("=" * 60)
    print("TEST 1: Checking APScheduler Installation")
    print("=" * 60)
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.jobstores.memory import MemoryJobStore
        from apscheduler.executors.pool import ThreadPoolExecutor
        print("[PASS] APScheduler is installed")
        return True
    except ImportError as e:
        print(f"[FAIL] APScheduler is NOT installed: {e}")
        print("   Install it with: pip install apscheduler")
        return False

def test_scheduler_function():
    """Test if the scheduler function can be called"""
    print("\n" + "=" * 60)
    print("TEST 2: Testing Scheduler Function Import")
    print("=" * 60)
    
    try:
        from cart.scheduler import send_abandoned_cart_emails, start_scheduler
        print("[PASS] Scheduler functions can be imported")
        return True
    except ImportError as e:
        print(f"❌ Cannot import scheduler functions: {e}")
        return False

def test_abandoned_cart_logic():
    """Test if abandoned cart detection logic works"""
    print("\n" + "=" * 60)
    print("TEST 3: Testing Abandoned Cart Detection Logic")
    print("=" * 60)
    
    try:
        from cart.models import Order
        
        # Check if Order model has abandoned cart fields
        required_fields = [
            'abandoned_email_sent',
            'abandoned_email_sent_at',
            'abandoned_email_count',
            'recovery_link_clicked_at',
            'last_updated'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not hasattr(Order, field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"[FAIL] Missing fields in Order model: {', '.join(missing_fields)}")
            return False
        else:
            print("[PASS] All required fields exist in Order model")
        
        # Check for abandoned carts
        time_ago = timezone.now() - timedelta(minutes=2)
        abandoned_orders = Order.objects.filter(
            user__isnull=False,
            ordered=False,
            start_date__lt=time_ago,
            items__isnull=False
        ).exclude(
            user__email=''
        ).exclude(
            user__email__isnull=True
        ).distinct().count()
        
        print(f"[PASS] Found {abandoned_orders} potential abandoned carts")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing abandoned cart logic: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_create_test_abandoned_cart():
    """Create a test abandoned cart for testing"""
    print("\n" + "=" * 60)
    print("TEST 4: Creating Test Abandoned Cart")
    print("=" * 60)
    
    try:
        # Get or create a test user
        test_user, created = User.objects.get_or_create(
            username='test_abandoned_cart_user',
            defaults={
                'email': 'test_abandoned@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            print(f"[PASS] Created test user: {test_user.username}")
        else:
            print(f"[PASS] Using existing test user: {test_user.username}")
        
        # Get a product variant
        variant = Variant.objects.filter(quantity__gt=0).first()
        if not variant:
            print("[FAIL] No variants available to create test cart")
            return False
        
        # Create an abandoned cart (ordered=False, old start_date)
        old_date = timezone.now() - timedelta(minutes=5)  # 5 minutes ago
        
        # Delete any existing test orders for this user
        Order.objects.filter(user=test_user, ordered=False).delete()
        
        # Create new abandoned cart
        order = Order.objects.create(
            user=test_user,
            ordered=False,
            start_date=old_date,
            last_updated=old_date,
            abandoned_email_count=0,
            abandoned_email_sent=False
        )
        
        # Add item to cart
        OrderItem.objects.create(
            order=order,
            variant=variant,
            quantity=1
        )
        
        print(f"[PASS] Created test abandoned cart:")
        print(f"   - Order ID: {order.id}")
        print(f"   - Reference: {order.reference_number}")
        print(f"   - User: {test_user.email}")
        print(f"   - Created: {order.start_date}")
        print(f"   - Items: {order.items.count()}")
        print(f"   - Email count: {order.abandoned_email_count}")
        
        return order
        
    except Exception as e:
        print(f"[FAIL] Error creating test cart: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_scheduler_manual_run():
    """Manually run the scheduler function to test it"""
    print("\n" + "=" * 60)
    print("TEST 5: Manually Running Scheduler Function")
    print("=" * 60)
    
    try:
        from cart.scheduler import send_abandoned_cart_emails
        
        print("Running send_abandoned_cart_emails()...")
        emails_sent = send_abandoned_cart_emails()
        
        print(f"[PASS] Scheduler function ran successfully")
        print(f"   - Emails sent: {emails_sent}")
        
        # Check if test cart was updated
        test_user = User.objects.filter(username='test_abandoned_cart_user').first()
        if test_user:
            order = Order.objects.filter(user=test_user, ordered=False).first()
            if order:
                print(f"\n   Test cart status:")
                print(f"   - Email sent: {order.abandoned_email_sent}")
                print(f"   - Email count: {order.abandoned_email_count}")
                print(f"   - Email sent at: {order.abandoned_email_sent_at}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error running scheduler function: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scheduler_start():
    """Test if scheduler can be started"""
    print("\n" + "=" * 60)
    print("TEST 6: Testing Scheduler Start (Will run in background)")
    print("=" * 60)
    
    try:
        from cart.scheduler import start_scheduler
        
        print("Starting scheduler...")
        start_scheduler()
        
        print("[PASS] Scheduler started successfully!")
        print("   - Scheduler is running in background")
        print("   - It will check for abandoned carts every 2 minutes")
        print("   - Check logs for scheduler activity")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error starting scheduler: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n" + "=" * 60)
    print("CLEANUP: Removing Test Data")
    print("=" * 60)
    
    try:
        test_user = User.objects.filter(username='test_abandoned_cart_user').first()
        if test_user:
            Order.objects.filter(user=test_user, ordered=False).delete()
            print("[PASS] Cleaned up test orders")
        
        return True
    except Exception as e:
        print(f"[WARN] Error cleaning up: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ABANDONED CART SCHEDULER TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Check APScheduler installation
    results.append(("APScheduler Installation", test_scheduler_setup()))
    
    # Test 2: Check scheduler function import
    if results[-1][1]:
        results.append(("Scheduler Function Import", test_scheduler_function()))
    
    # Test 3: Test abandoned cart logic
    if results[-1][1]:
        results.append(("Abandoned Cart Logic", test_abandoned_cart_logic()))
    
    # Test 4: Create test abandoned cart
    if results[-1][1]:
        test_order = test_create_test_abandoned_cart()
        results.append(("Create Test Cart", test_order is not None))
    
    # Test 5: Manually run scheduler
    if results[-1][1]:
        results.append(("Manual Scheduler Run", test_scheduler_manual_run()))
    
    # Test 6: Start scheduler (optional - comment out if you don't want background process)
    # results.append(("Start Scheduler", test_scheduler_start()))
    
    # Cleanup
    cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! Scheduler should work correctly.")
    else:
        print("\n[WARNING] Some tests failed. Please fix the issues above.")
    
    return passed == total

if __name__ == '__main__':
    main()

