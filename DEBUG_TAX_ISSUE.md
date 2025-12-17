# Debug Tax Calculation Issue

## 🔍 Problem
Tax nahi aa raha jab location select karte hain.

## ✅ Steps to Debug

### 1. Check Browser Console
Open browser console (F12) and check for:
- ✅ API calls being made
- ✅ Error messages
- ✅ Response data

### 2. Check Network Tab
- Open Network tab in browser
- Select location (Country/State/City)
- Look for: `POST /api/tax/update-address/`
- Check:
  - ✅ Request is being sent
  - ✅ Response status (200, 400, 500?)
  - ✅ Response data

### 3. Common Issues

#### Issue 1: Cart is Empty
**Error:** "Cart is empty. Please add items to cart first."
**Solution:** Add items to cart first, then select location

#### Issue 2: No Tax Rate Configured
**Error:** Tax amount is 0.00
**Solution:** Add tax rate in Django Admin for the location

#### Issue 3: API Not Being Called
**Error:** No network request in Network tab
**Solution:** Check if location dropdowns are triggering `handleChange`

#### Issue 4: CORS Error
**Error:** CORS policy error in console
**Solution:** Check backend CORS settings

#### Issue 5: Session Cookie Issue
**Error:** 401 or 403 error
**Solution:** Check if `credentials: 'include'` is set

---

## 🧪 Quick Test

### Test 1: Check if API is being called
1. Open browser console (F12)
2. Select Country: "United States"
3. Check console for: "Calculating tax for location:"
4. Select State: "California"
5. Check console for: "Tax calculation response:"

### Test 2: Check Network Request
1. Open Network tab
2. Select location
3. Find: `POST /api/tax/update-address/`
4. Check:
   - Status: Should be 200
   - Response: Should have `tax_amount`

### Test 3: Check Cart
1. Make sure cart has items
2. Check cart total is not $0.00
3. Then select location

---

## 🔧 Quick Fixes

### Fix 1: Add Console Logs
Console logs are already added. Check browser console for:
- "Calculating tax for location:"
- "Tax calculation response:"
- Any error messages

### Fix 2: Check Cart Items
Make sure cart has items before selecting location.

### Fix 3: Add Tax Rate
Go to Django Admin and add tax rate for:
- Country: United States
- State: California
- Rate: 0.0875 (8.75%)

---

## 📋 Checklist

- [ ] Cart has items
- [ ] Browser console shows API calls
- [ ] Network tab shows POST request
- [ ] Response status is 200
- [ ] Tax rate is configured in Django Admin
- [ ] No CORS errors
- [ ] Session cookies are working

---

## 🎯 Next Steps

1. **Check Browser Console** - Look for error messages
2. **Check Network Tab** - Verify API is being called
3. **Check Cart** - Make sure cart has items
4. **Check Tax Rates** - Add tax rate in Django Admin if needed

**Share the console/network errors if tax still doesn't work!**

