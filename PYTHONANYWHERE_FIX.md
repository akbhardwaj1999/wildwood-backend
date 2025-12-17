# PythonAnywhere Fix - Country Code Error

## Problem
Error: `Invalid field name(s) for model Country: 'code'`

## Solution
Country model mein `code` field nahi hai, isliye script se remove kiya gaya hai.

## Fix Applied

**File:** `NEW_tax_calculator/management/commands/add_us_states_cities.py`

**Changed:**
```python
# BEFORE (Error):
country, created = Country.objects.get_or_create(
    name='United States',
    defaults={'code': 'US'}  # ❌ Code field doesn't exist
)

# AFTER (Fixed):
country, created = Country.objects.get_or_create(
    name='United States'  # ✅ Only name field
)
```

## PythonAnywhere Par Kaise Fix Karein

### Option 1: File Edit Karo (Recommended)
1. PythonAnywhere console mein jao
2. File open karo:
   ```bash
   nano ~/wildwood-backend/NEW_tax_calculator/management/commands/add_us_states_cities.py
   ```
3. Line 18-21 ko update karo:
   ```python
   # Get or create United States country
   country, created = Country.objects.get_or_create(
       name='United States'
   )
   ```
4. Save karo (Ctrl+X, then Y, then Enter)

### Option 2: Git Se Pull Karo
Agar code Git mein push kiya hai:
```bash
cd ~/wildwood-backend
git pull origin main
```

### Option 3: File Upload Karo
Fixed file ko manually upload karo PythonAnywhere par.

## Ab Command Run Karo

Fix ke baad:
```bash
python manage.py add_us_states_cities
```

Ab error nahi aayega! ✅

