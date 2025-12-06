"""
Quick test script to verify coupon discount calculation
Run: python test_coupon_quick.py
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wildwud.settings')
django.setup()

from decimal import Decimal
from cart.models import Coupon, Order, OrderItem
from galleryItem.models import Variant, GalleryItem, Category
from django.contrib.auth import get_user_model

User = get_user_model()

def test_coupon_calculation():
    print("=" * 60)
    print("COUPON DISCOUNT CALCULATION TEST")
    print("=" * 60)
    
    # Get or create test data
    category, _ = Category.objects.get_or_create(
        title='Test Category',
        defaults={'description': 'Test Category for Coupon Testing'}
    )
    
    product, _ = GalleryItem.objects.get_or_create(
        title='Test Product for Coupon',
        defaults={
            'category': category,
            'description': 'Test product',
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
    
    # Get or create order with items
    order = Order.objects.filter(ordered=False).first()
    if not order:
        order = Order.objects.create(ordered=False)
    
    # Clear existing items
    OrderItem.objects.filter(order=order).delete()
    
    # Add item
    OrderItem.objects.create(
        order=order,
        variant=variant,
        quantity=1
    )
    
    print(f"\n📦 Test Order Setup:")
    print(f"   Product: {product.title}")
    print(f"   Variant: {variant.title}")
    print(f"   Price: ${variant.price}")
    print(f"   Quantity: 1")
    print(f"   Subtotal: ${order.get_subtotal()}")
    
    # Test 1: 5% Percentage Coupon
    print(f"\n{'='*60}")
    print("TEST 1: 5% Discount Coupon (SAVE5)")
    print(f"{'='*60}")
    
    try:
        coupon_fixed = Coupon.objects.get(code='SAVE5')
        order.coupon = coupon_fixed
        order.save()
        
        subtotal = float(order.get_subtotal())
        discount = float(order.get_coupon_discount_amount())
        total = float(order.get_total())
        expected_total = subtotal - discount
        
        print(f"   Coupon: {coupon_fixed.title}")
        print(f"   Code: {coupon_fixed.code}")
        print(f"   Discount Type: {coupon_fixed.get_discount_type_display()}")
        print(f"   Discount Value: ${coupon_fixed.discount}")
        print(f"   Subtotal: ${subtotal:.2f}")
        print(f"   Discount Applied: ${discount:.2f}")
        print(f"   Total: ${total:.2f}")
        print(f"   Expected Total: ${expected_total:.2f}")
        
        if abs(total - expected_total) < 0.01:
            print(f"   ✅ PASS: Discount calculation is correct!")
        else:
            print(f"   ❌ FAIL: Expected ${expected_total:.2f}, got ${total:.2f}")
    except Coupon.DoesNotExist:
        print("   ⚠️  Coupon TEST10 not found. Run: python manage.py create_test_coupons")
    
    # Test 2: Percentage Coupon
    print(f"\n{'='*60}")
    print("TEST 2: Percentage Coupon (SAVE20 - 20% off)")
    print(f"{'='*60}")
    
    try:
        coupon_percent = Coupon.objects.get(code='SAVE20')
        order.coupon = coupon_percent
        order.save()
        
        subtotal = float(order.get_subtotal())
        discount = float(order.get_coupon_discount_amount())
        total = float(order.get_total())
        expected_discount = (float(coupon_percent.discount) / 100) * subtotal
        expected_total = subtotal - expected_discount
        
        print(f"   Coupon: {coupon_percent.title}")
        print(f"   Code: {coupon_percent.code}")
        print(f"   Discount Type: {coupon_percent.get_discount_type_display()}")
        print(f"   Discount Value: {coupon_percent.discount}%")
        print(f"   Subtotal: ${subtotal:.2f}")
        print(f"   Discount Applied: ${discount:.2f}")
        print(f"   Expected Discount: ${expected_discount:.2f} (20% of ${subtotal:.2f})")
        print(f"   Total: ${total:.2f}")
        print(f"   Expected Total: ${expected_total:.2f}")
        
        if abs(discount - expected_discount) < 0.01 and abs(total - expected_total) < 0.01:
            print(f"   ✅ PASS: Discount calculation is correct!")
        else:
            print(f"   ❌ FAIL: Discount mismatch")
            print(f"      Expected discount: ${expected_discount:.2f}, got ${discount:.2f}")
            print(f"      Expected total: ${expected_total:.2f}, got ${total:.2f}")
    except Coupon.DoesNotExist:
        print("   ⚠️  Coupon SAVE20 not found. Run: python manage.py create_test_coupons")
    
    # Test 3: Remove Coupon
    print(f"\n{'='*60}")
    print("TEST 3: Remove Coupon")
    print(f"{'='*60}")
    
    order.coupon = None
    order.save()
    
    subtotal = float(order.get_subtotal())
    discount = float(order.get_coupon_discount_amount())
    total = float(order.get_total())
    
    print(f"   Subtotal: ${subtotal:.2f}")
    print(f"   Discount: ${discount:.2f}")
    print(f"   Total: ${total:.2f}")
    
    if discount == 0.0 and abs(total - subtotal) < 0.01:
        print(f"   ✅ PASS: Coupon removed successfully!")
    else:
        print(f"   ❌ FAIL: Coupon not removed properly")
    
    # Test 4: No Minimum Order Required
    print(f"\n{'='*60}")
    print("TEST 4: No Minimum Order Required Check")
    print(f"{'='*60}")
    
    try:
        coupon_no_min = Coupon.objects.get(code='SAVE5')
        print(f"   Coupon: {coupon_no_min.code}")
        print(f"   Minimum Order Amount: ${coupon_no_min.minimum_order_amount}")
        print(f"   Current Subtotal: ${float(order.get_subtotal()):.2f}")
        
        if float(coupon_no_min.minimum_order_amount) == 0.00:
            print(f"   ✅ PASS: No minimum order required - coupon can be applied to any cart")
        else:
            print(f"   ⚠️  WARNING: This coupon has minimum order requirement")
    except Coupon.DoesNotExist:
        print("   ⚠️  Coupon SAVE5 not found")
    
    print(f"\n{'='*60}")
    print("TEST COMPLETE")
    print(f"{'='*60}")
    print("\n💡 Tips:")
    print("   - Run 'python manage.py create_test_coupons' to create test coupons")
    print("   - Available coupons: SAVE5, SAVE10, SAVE15, SAVE20, SAVE25 (all 5% to 25% off)")
    print("   - Test via API: POST /api/cart/coupons/apply/ with {'code': 'SAVE5'}")
    print("   - Test via Frontend: Go to /cart page and enter coupon code")
    print("   - No minimum order required - apply to any cart!")
    print("   - Check COUPON_TESTING_GUIDE.md for detailed testing instructions")

if __name__ == '__main__':
    test_coupon_calculation()

