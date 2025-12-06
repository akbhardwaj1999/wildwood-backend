# Coupon Discount Testing Guide

## Overview
This guide will help you test the coupon discount functionality in the Wildwood e-commerce system.

## Prerequisites
1. Backend server running on `http://127.0.0.1:8000`
2. Frontend server running on `http://localhost:3000`
3. At least one product added to the cart

---

## Step 1: Create Test Coupons

### Using Management Command (Recommended)
```bash
cd F:\wildwud-backend
python manage.py create_test_coupons
```

This will create 5 test coupons (all percentage discounts, NO minimum order required):
- **SAVE5** - 5% discount (No minimum order)
- **SAVE10** - 10% discount (No minimum order)
- **SAVE15** - 15% discount (No minimum order)
- **SAVE20** - 20% discount (No minimum order)
- **SAVE25** - 25% discount (No minimum order)

### Using Django Admin
1. Go to `http://127.0.0.1:8000/admin/`
2. Navigate to **Cart > Coupons**
3. Click **Add Coupon**
4. Fill in the details:
   - **Title**: Test Coupon
   - **Code**: TEST10
   - **Discount**: 10.00
   - **Discount Type**: Fixed Amount or Percentage
   - **Minimum Order Amount**: 50.00
   - **Single Use Per User**: Check if needed
   - **Active**: Check to enable

---

## Step 2: Test Coupon Application via API

### Test 1: Apply Fixed Amount Coupon ($10 off)

**Request:**
```bash
POST http://127.0.0.1:8000/api/cart/coupons/apply/
Content-Type: application/json

{
  "code": "TEST10"
}
```

**Expected Response (200 OK):**
```json
{
  "message": "Coupon applied successfully",
  "coupon_discount_amount": "10.00",
  "cart": {
    "id": 1,
    "subtotal": "100.00",
    "coupon_discount_amount": "10.00",
    "total": "90.00",
    ...
  }
}
```

**Verification:**
- Check that `coupon_discount_amount` is "10.00"
- Check that `total` = `subtotal` - `coupon_discount_amount`
- Check that `cart.coupon` is set

---

### Test 2: Apply Percentage Coupon (20% off)

**Request:**
```bash
POST http://127.0.0.1:8000/api/cart/coupons/apply/
Content-Type: application/json

{
  "code": "SAVE20"
}
```

**Expected Response (200 OK):**
```json
{
  "message": "Coupon applied successfully",
  "coupon_discount_amount": "20.00",  // 20% of $100 = $20
  "cart": {
    "subtotal": "100.00",
    "coupon_discount_amount": "20.00",
    "total": "80.00",
    ...
  }
}
```

**Calculation:**
- If subtotal = $100.00
- 20% discount = $100 × 0.20 = $20.00
- Total = $100.00 - $20.00 = $80.00

---

### Test 3: Invalid Coupon Code

**Request:**
```bash
POST http://127.0.0.1:8000/api/cart/coupons/apply/
Content-Type: application/json

{
  "code": "INVALID"
}
```

**Expected Response (400 Bad Request):**
```json
{
  "error": "Coupon code is invalid."
}
```

---

### Test 4: Apply Coupon to Small Cart (No Minimum Required)

**Request:**
```bash
POST http://127.0.0.1:8000/api/cart/coupons/apply/
Content-Type: application/json

{
  "code": "SAVE5"
}
```

**Scenario:** Cart subtotal is $10.00 (small cart)

**Expected Response (200 OK):**
```json
{
  "message": "Coupon applied successfully",
  "coupon_discount_amount": "0.50",
  "cart": {
    "subtotal": "10.00",
    "coupon_discount_amount": "0.50",
    "total": "9.50",
    ...
  }
}
```

**Note:** All test coupons have NO minimum order requirement, so they can be applied to any cart size!

---

### Test 5: Remove Coupon

**Request:**
```bash
DELETE http://127.0.0.1:8000/api/cart/coupons/remove/
```

**Expected Response (200 OK):**
```json
{
  "message": "Coupon removed successfully",
  "cart": {
    "subtotal": "100.00",
    "coupon_discount_amount": "0.00",
    "total": "100.00",
    "coupon": null,
    ...
  }
}
```

---

## Step 3: Test via Frontend (Cart Page)

### Test Steps:
1. **Add items to cart** - Go to shop page and add products
2. **Go to Cart page** - Navigate to `/cart`
3. **Enter coupon code** - In the "Discount Coupon Code" section
4. **Click "APPLY CODE"** button
5. **Verify discount** - Check that:
   - Discount amount is shown
   - Total is updated (Subtotal - Discount)
   - Success message appears

### Test Cases:

#### Case 1: Valid Fixed Amount Coupon
- **Coupon Code**: `TEST10`
- **Cart Subtotal**: $100.00
- **Expected Discount**: $10.00
- **Expected Total**: $90.00

#### Case 2: Valid Percentage Coupon
- **Coupon Code**: `SAVE20`
- **Cart Subtotal**: $100.00
- **Expected Discount**: $20.00 (20%)
- **Expected Total**: $80.00

#### Case 3: Below Minimum Order
- **Coupon Code**: `TEST10` (requires $50 minimum)
- **Cart Subtotal**: $30.00
- **Expected**: Error message "The minimum order amount should be $50.00..."

#### Case 4: Invalid Coupon
- **Coupon Code**: `INVALID123`
- **Expected**: Error message "Coupon code is invalid."

#### Case 5: Remove Coupon
- Apply a coupon first
- Click "Remove" button next to applied coupon
- **Expected**: Coupon removed, total updated, discount = $0.00

---

## Step 4: Test Discount Calculation

### Fixed Amount Discount Formula:
```
Discount = Coupon Discount Amount
Total = Subtotal - Discount
```

**Example:**
- Subtotal: $100.00
- Coupon: TEST10 ($10 off)
- Discount: $10.00
- Total: $100.00 - $10.00 = $90.00

### Percentage Discount Formula:
```
Discount = (Coupon Discount % / 100) × Subtotal
Total = Subtotal - Discount
```

**Example:**
- Subtotal: $100.00
- Coupon: SAVE20 (20% off)
- Discount: (20 / 100) × $100.00 = $20.00
- Total: $100.00 - $20.00 = $80.00

---

## Step 5: Test Edge Cases

### Edge Case 1: Coupon with Wholesale Discount
- **Scenario**: Order has wholesale discount applied
- **Expected**: Error "Coupons cannot be used with wholesale discounts."

### Edge Case 2: Single Use Per User (Not Logged In)
- **Coupon**: MIN100 (single use, requires login)
- **Scenario**: Guest user tries to apply
- **Expected**: Error "Please login to apply for this coupon."

### Edge Case 3: Single Use Per User (Already Used)
- **Coupon**: MIN100
- **Scenario**: User already used this coupon in a previous order
- **Expected**: Error "This coupon has been consumed before."

### Edge Case 4: Empty Cart
- **Scenario**: Cart is empty, try to apply coupon
- **Expected**: Error "Cart is empty. Add items to cart before applying coupon."

### Edge Case 5: Inactive Coupon
- **Scenario**: Coupon exists but `active = False`
- **Expected**: Error "Coupon code is invalid."

---

## Step 6: Test via Postman

### Import Postman Collection
1. Open Postman
2. Import the file: `postman_test_data.json`
3. Look for coupon-related requests:
   - `Apply Coupon - TEST10`
   - `Apply Coupon - SAVE20`
   - `Remove Coupon`
   - `Apply Invalid Coupon`

### Test Sequence:
1. **Get Cart** - First get your current cart
2. **Add Item** - Add a product to cart (if empty)
3. **Apply Coupon** - Apply a valid coupon
4. **Verify Cart** - Get cart again and verify discount
5. **Remove Coupon** - Remove the coupon
6. **Verify Cart** - Get cart again and verify discount removed

---

## Step 7: Manual Testing Checklist

### ✅ Pre-Testing Setup
- [ ] Backend server is running
- [ ] Frontend server is running
- [ ] Test coupons are created
- [ ] At least one product exists in database
- [ ] Cart has items (subtotal > $50 for TEST10)

### ✅ Fixed Amount Coupon Tests
- [ ] Apply TEST10 with cart > $50 → Discount $10 applied
- [ ] Apply TEST10 with cart < $50 → Error shown
- [ ] Verify total = subtotal - $10
- [ ] Remove coupon → Discount removed, total updated

### ✅ Percentage Coupon Tests
- [ ] Apply SAVE20 with cart > $100 → 20% discount applied
- [ ] Apply SAVE20 with cart < $100 → Error shown
- [ ] Verify discount calculation: subtotal × 20%
- [ ] Verify total = subtotal - discount

### ✅ Error Handling Tests
- [ ] Invalid coupon code → Error message
- [ ] Below minimum order → Error message
- [ ] Empty cart → Error message
- [ ] Inactive coupon → Error message

### ✅ UI Tests (Frontend)
- [ ] Coupon input field works
- [ ] Apply button works
- [ ] Success message shows
- [ ] Error message shows
- [ ] Discount amount displays correctly
- [ ] Total updates correctly
- [ ] Remove button works
- [ ] Cart totals update in header

---

## Step 8: Verify Discount in Database

### Check Order Model:
```python
# In Django shell
python manage.py shell

from cart.models import Order, Coupon

# Get your order
order = Order.objects.filter(ordered=False).first()

# Check coupon
print(f"Coupon: {order.coupon}")
print(f"Subtotal: {order.get_subtotal()}")
print(f"Discount: {order.get_coupon_discount_amount()}")
print(f"Total: {order.get_total()}")
```

### Expected Output:
```
Coupon: Test Coupon - $10 Off
Subtotal: 100.00
Discount: 10.00
Total: 90.00
```

---

## Step 9: Test Discount Calculation Logic

### Test Script:
```python
# test_coupon_calculation.py
from decimal import Decimal
from cart.models import Coupon, Order, OrderItem
from galleryItem.models import Variant, GalleryItem, Category

# Create test data
category = Category.objects.create(title='Test Category')
product = GalleryItem.objects.create(title='Test Product', category=category)
variant = Variant.objects.create(product=product, price=Decimal('100.00'), quantity=10)

# Create order
order = Order.objects.create()
OrderItem.objects.create(order=order, variant=variant, quantity=1)

# Test Fixed Amount
coupon_fixed = Coupon.objects.get(code='TEST10')
order.coupon = coupon_fixed
order.save()

print(f"Subtotal: ${order.get_subtotal()}")
print(f"Discount: ${order.get_coupon_discount_amount()}")
print(f"Total: ${order.get_total()}")
print(f"Expected Total: ${float(order.get_subtotal()) - float(order.get_coupon_discount_amount())}")

# Test Percentage
coupon_percent = Coupon.objects.get(code='SAVE20')
order.coupon = coupon_percent
order.save()

print(f"\nSubtotal: ${order.get_subtotal()}")
print(f"Discount: ${order.get_coupon_discount_amount()}")
print(f"Total: ${order.get_total()}")
print(f"Expected Total: ${float(order.get_subtotal()) - float(order.get_coupon_discount_amount())}")
```

---

## Common Issues and Solutions

### Issue 1: Coupon not applying
**Solution**: 
- Check if cart has items
- Check if cart subtotal meets minimum order amount
- Check if coupon is active
- Check browser console for errors

### Issue 2: Discount not showing in total
**Solution**:
- Verify coupon is saved to order: `order.coupon` should not be None
- Check `order.get_coupon_discount_amount()` returns correct value
- Verify `order.get_total()` includes discount calculation

### Issue 3: Coupon removed automatically
**Solution**:
- Check session: `request.session.get('coupon_applied_at')` should be set
- Verify `get_or_set_order_session` doesn't clear coupon
- Check if order is being recreated

### Issue 4: Percentage discount calculation wrong
**Solution**:
- Verify formula: `(discount / 100) × subtotal`
- Check if subtotal is calculated correctly
- Verify discount value in coupon model

---

## API Endpoints Reference

### Apply Coupon
- **URL**: `POST /api/cart/coupons/apply/`
- **Body**: `{"code": "TEST10"}`
- **Response**: Cart with discount applied

### Remove Coupon
- **URL**: `DELETE /api/cart/coupons/remove/`
- **Response**: Cart with coupon removed

### Get Cart
- **URL**: `GET /api/cart/cart/`
- **Response**: Current cart with coupon info

---

## Test Data Summary

| Coupon Code | Type | Discount | Min Order | Single Use | Login Required |
|------------|------|----------|-----------|------------|----------------|
| TEST10 | Fixed | $10 | $50 | No | No |
| SAVE20 | Percentage | 20% | $100 | No | No |
| FIXED50 | Fixed | $50 | $200 | No | No |
| PERCENT15 | Percentage | 15% | $0 | No | No |
| MIN100 | Fixed | $25 | $100 | Yes | Yes |

---

## Quick Test Commands

```bash
# Create test coupons
python manage.py create_test_coupons

# Run coupon tests
python manage.py test cart.tests.CouponTestCase

# Check coupons in admin
# Go to: http://127.0.0.1:8000/admin/cart/coupon/
```

---

## Success Criteria

✅ Coupon applies successfully when:
- Code is valid
- Cart has items
- Subtotal meets minimum order amount
- Coupon is active
- No wholesale discount exists

✅ Discount calculation is correct:
- Fixed amount: Discount = coupon.discount
- Percentage: Discount = (coupon.discount / 100) × subtotal
- Total = Subtotal - Discount

✅ UI updates correctly:
- Discount amount shows
- Total updates
- Success/error messages display
- Remove button works

---

## Need Help?

If you encounter issues:
1. Check browser console for errors
2. Check Django server logs
3. Verify coupon exists in database
4. Test API directly via Postman
5. Check cart session is working

Happy Testing! 🎉

