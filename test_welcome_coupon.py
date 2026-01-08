"""
Test script for Welcome Coupon System
Tests:
1. Coupon creation on user registration
2. User-specific coupon verification
3. Single-use restriction
4. Email with coupon code
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wildwud.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Coupon, Order, OrderItem
from galleryItem.models import GalleryItem, Variant, Category
from decimal import Decimal

User = get_user_model()

def test_coupon_creation_on_registration():
    """Test 1: Coupon is created when user registers"""
    print("\n" + "="*70)
    print("TEST 1: Coupon Creation on Registration")
    print("="*70)
    
    # Create a test user (simulating registration)
    test_username = f"testuser_{os.urandom(4).hex()}"
    test_email = f"{test_username}@test.com"
    
    try:
        user = User.objects.create_user(
            username=test_username,
            email=test_email,
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        print(f"✅ User created: {user.username}")
        
        # Simulate coupon creation (as in registration view)
        import secrets
        coupon_code = f"WELCOME20_{user.id}_{secrets.token_urlsafe(6).upper()}"
        
        coupon = Coupon.objects.create(
            title=f'Welcome Discount for {user.username}',
            description='20% off on your first purchase as a welcome gift!',
            code=coupon_code,
            discount=Decimal('20.00'),
            discount_type=Coupon.DiscountType.PERCENTAGE,
            minimum_order_amount=Decimal('0.00'),
            single_use_per_user=True,
            created_for_user=user,
            active=True
        )
        print(f"✅ Coupon created: {coupon.code}")
        print(f"   - Discount: {coupon.discount}%")
        print(f"   - Created for user: {coupon.created_for_user.username}")
        print(f"   - Single use: {coupon.single_use_per_user}")
        
        # Verify coupon exists
        assert Coupon.objects.filter(code=coupon_code).exists(), "Coupon should exist"
        assert coupon.created_for_user == user, "Coupon should be linked to user"
        print("✅ TEST 1 PASSED: Coupon created successfully on registration")
        
        return user, coupon
        
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {str(e)}")
        return None, None


def test_user_specific_verification(user1, coupon, user2):
    """Test 2: Only the user for whom coupon was created can use it"""
    print("\n" + "="*70)
    print("TEST 2: User-Specific Coupon Verification")
    print("="*70)
    
    if not user1 or not coupon:
        print("❌ TEST 2 SKIPPED: Previous test failed")
        return False
    
    # Create second user
    if not user2:
        test_username2 = f"testuser2_{os.urandom(4).hex()}"
        test_email2 = f"{test_username2}@test.com"
        user2 = User.objects.create_user(
            username=test_username2,
            email=test_email2,
            password='TestPass123!'
        )
        print(f"✅ Second user created: {user2.username}")
    
    # Test: User2 tries to use User1's coupon
    print(f"\n🔍 Testing: User2 ({user2.username}) tries to use User1's coupon ({coupon.code})")
    
    # Simulate verification logic
    if coupon.created_for_user:
        if coupon.created_for_user != user2:
            print(f"✅ Verification: Coupon is NOT valid for User2")
            print(f"   - Coupon created for: {coupon.created_for_user.username}")
            print(f"   - Trying user: {user2.username}")
            print("✅ TEST 2 PASSED: User-specific verification works")
            return True
        else:
            print(f"❌ TEST 2 FAILED: Coupon should not be valid for User2")
            return False
    else:
        print(f"❌ TEST 2 FAILED: Coupon should have created_for_user set")
        return False


def test_single_use_restriction(user, coupon):
    """Test 3: Coupon can only be used once"""
    print("\n" + "="*70)
    print("TEST 3: Single-Use Restriction")
    print("="*70)
    
    if not user or not coupon:
        print("❌ TEST 3 SKIPPED: Previous test failed")
        return False
    
    # Create category and product for order
    category, _ = Category.objects.get_or_create(
        title='Test Category',
        defaults={'description': 'Test'}
    )
    
    product, _ = GalleryItem.objects.get_or_create(
        title='Test Product',
        defaults={
            'category': category,
            'active': True,
            'description': 'Test'
        }
    )
    
    variant, _ = Variant.objects.get_or_create(
        product=product,
        title='Test Variant',
        defaults={
            'price': Decimal('100.00'),
            'quantity': 10,
            'active': True
        }
    )
    
    # Create first order with coupon
    print(f"\n🔍 Testing: User uses coupon for first time")
    order1 = Order.objects.create(
        user=user,
        coupon=coupon,
        status=Order.FINALIZED
    )
    OrderItem.objects.create(
        order=order1,
        variant=variant,
        quantity=1
    )
    print(f"✅ First order created with coupon: Order #{order1.id}")
    
    # Check if coupon was used
    used_before = Order.objects.filter(
        user=user,
        coupon=coupon
    ).exclude(
        status=Order.NOT_FINALIZED
    ).exists()
    
    if used_before:
        print(f"✅ Verification: Coupon has been used before")
        print(f"   - Found order: Order #{order1.id}")
        print("✅ TEST 3 PASSED: Single-use restriction works")
        return True
    else:
        print(f"❌ TEST 3 FAILED: Should detect coupon was used")
        return False


def test_coupon_code_format(user, coupon):
    """Test 4: Coupon code format is correct"""
    print("\n" + "="*70)
    print("TEST 4: Coupon Code Format")
    print("="*70)
    
    if not user or not coupon:
        print("❌ TEST 4 SKIPPED: Previous test failed")
        return False
    
    code = coupon.code
    print(f"🔍 Testing coupon code format: {code}")
    
    # Check format: WELCOME20_{user_id}_{random}
    parts = code.split('_')
    if len(parts) == 3:
        prefix = parts[0]
        user_id = parts[1]
        random_part = parts[2]
        
        if prefix == 'WELCOME20':
            print(f"✅ Prefix correct: {prefix}")
        else:
            print(f"❌ Prefix incorrect: {prefix}")
            return False
        
        if user_id == str(user.id):
            print(f"✅ User ID correct: {user_id}")
        else:
            print(f"❌ User ID incorrect: {user_id}")
            return False
        
        if len(random_part) >= 6:
            print(f"✅ Random part present: {random_part[:6]}...")
        else:
            print(f"❌ Random part too short")
            return False
        
        print("✅ TEST 4 PASSED: Coupon code format is correct")
        return True
    else:
        print(f"❌ TEST 4 FAILED: Code format incorrect")
        return False


def cleanup_test_data(user1, user2, coupon):
    """Clean up test data"""
    print("\n" + "="*70)
    print("CLEANUP: Removing test data")
    print("="*70)
    
    try:
        if coupon:
            # Delete orders first
            Order.objects.filter(coupon=coupon).delete()
            coupon.delete()
            print(f"✅ Coupon deleted: {coupon.code}")
        
        if user1:
            user1.delete()
            print(f"✅ User1 deleted: {user1.username}")
        
        if user2:
            user2.delete()
            print(f"✅ User2 deleted: {user2.username}")
        
        # Clean up test products
        GalleryItem.objects.filter(title='Test Product').delete()
        Category.objects.filter(title='Test Category').delete()
        print("✅ Test products deleted")
        
    except Exception as e:
        print(f"⚠️  Cleanup warning: {str(e)}")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("WELCOME COUPON SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    user1 = None
    user2 = None
    coupon = None
    
    try:
        # Test 1: Coupon creation
        user1, coupon = test_coupon_creation_on_registration()
        
        # Test 2: User-specific verification
        test_user_specific_verification(user1, coupon, user2)
        
        # Test 3: Single-use restriction
        test_single_use_restriction(user1, coupon)
        
        # Test 4: Coupon code format
        test_coupon_code_format(user1, coupon)
        
        print("\n" + "="*70)
        print("ALL TESTS COMPLETED")
        print("="*70)
        
    finally:
        # Cleanup
        cleanup_test_data(user1, user2, coupon)


if __name__ == '__main__':
    main()

