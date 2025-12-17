# PythonAnywhere Setup Commands - Complete Guide

## Sab Commands Ek Jagah

PythonAnywhere par deploy karne ke baad ye commands run karo:

---

## 1. Countries, States, aur Cities Add Karne Ke Liye

**Command:**
```bash
python manage.py add_us_states_cities
```

**Kya Hoga:**
- United States country add hoga (agar nahi hai)
- 50 US States add honge
- 396+ Major Cities add honge
- Tax rates add karne ke liye ready ho jayega

**File Location:**
`NEW_tax_calculator/management/commands/add_us_states_cities.py`

**Output:**
```
Total States: 50 (Created: 44, Existing: 6)
Total Cities: 396 (Created: 366, Existing: 29)
```

---

## 2. Default Tax Rates Add Karne Ke Liye

**Command:**
```bash
python manage.py add_default_tax_rates
```

**Kya Hoga:**
- US ke major states aur cities ke liye default tax rates add honge
- California, New York, Texas, Florida, Illinois ke tax rates
- Testing ke liye ready ho jayega

**File Location:**
`NEW_tax_calculator/management/commands/add_default_tax_rates.py`

**Output:**
```
Created tax rate for California state: 8.75%
Created tax rate for Los Angeles city: 9.00%
...
```

---

## 3. Default Shipping Cost Rules Add Karne Ke Liye

**Command:**
```bash
python manage.py add_default_shipping_costs
```

**Kya Hoga:**
- 32 shipping cost rules add honge
- LOCAL, OTHER_CITY, OTHER_STATE, INTERNATIONAL ke liye
- Volume-based aur Weight-based rules
- Shipping cost calculation ke liye ready ho jayega

**File Location:**
`cart/management/commands/add_default_shipping_costs.py`

**Output:**
```
Created: V 0-100, L, $5.00
Created: V 101-500, L, $8.00
...
Completed! Created 32 shipping cost rules
```

---

## Complete Setup Sequence (PythonAnywhere Par)

### Step 1: Code Deploy Karo
```bash
# Git se pull karo ya files upload karo
cd ~/wildwood-backend  # ya apna project path
```

### Step 2: Virtual Environment Activate Karo
```bash
source env/bin/activate  # ya apna venv path
```

### Step 3: Dependencies Install Karo
```bash
pip install -r requirements.txt
```

### Step 4: Migrations Run Karo
```bash
python manage.py migrate
```

### Step 5: Countries, States, Cities Add Karo
```bash
python manage.py add_us_states_cities
```

### Step 6: Default Tax Rates Add Karo
```bash
python manage.py add_default_tax_rates
```

### Step 7: Default Shipping Costs Add Karo
```bash
python manage.py add_default_shipping_costs
```

### Step 8: Server Restart Karo
PythonAnywhere dashboard se web app restart karo.

---

## Quick Reference - Commands List

| Kaam | Command | File Location |
|------|---------|---------------|
| **Countries/States/Cities** | `python manage.py add_us_states_cities` | `NEW_tax_calculator/management/commands/add_us_states_cities.py` |
| **Tax Rates** | `python manage.py add_default_tax_rates` | `NEW_tax_calculator/management/commands/add_default_tax_rates.py` |
| **Shipping Costs** | `python manage.py add_default_shipping_costs` | `cart/management/commands/add_default_shipping_costs.py` |

---

## Important Notes

### 1. Warehouse Settings Check Karo
`wildwud/settings.py` mein ye settings honi chahiye:
```python
WAREHOUSE_COUNTRY = 'United States'
WAREHOUSE_STATE = 'California'
WAREHOUSE_CITY = 'Los Angeles'
```

### 2. Commands Safe Hain
- Sab commands **idempotent** hain (multiple times run kar sakte ho)
- Duplicate entries nahi banenge
- Existing data ko overwrite nahi karega

### 3. Order Important Hai
1. Pehle `add_us_states_cities` run karo (tax rates ke liye states/cities chahiye)
2. Phir `add_default_tax_rates` run karo
3. Phir `add_default_shipping_costs` run karo

---

## Verification Commands

### Check Countries/States/Cities
```bash
python manage.py shell -c "from NEW_tax_calculator.models import Country, State, City; us = Country.objects.get(name='United States'); print(f'States: {State.objects.filter(country=us).count()}'); print(f'Cities: {City.objects.filter(state__country=us).count()}')"
```

### Check Tax Rates
```bash
python manage.py shell -c "from NEW_tax_calculator.models import NEW_TaxRate; print(f'Tax Rates: {NEW_TaxRate.objects.count()}')"
```

### Check Shipping Costs
```bash
python manage.py shell -c "from cart.models import ShippingCost; print(f'Shipping Cost Rules: {ShippingCost.objects.count()}')"
```

---

## Troubleshooting

### Error: "No module named 'NEW_tax_calculator'"
- Check karo ki app `INSTALLED_APPS` mein hai
- Virtual environment activate kiya hai?

### Error: "Command not found"
- Check karo ki management commands folder structure sahi hai
- File permissions check karo

### Data Already Exists
- Koi problem nahi - commands skip kar denge existing data ko
- Agar fresh start chahiye, pehle manually delete karo

---

## Summary

**PythonAnywhere Par Setup:**
1. `python manage.py add_us_states_cities` → Countries/States/Cities
2. `python manage.py add_default_tax_rates` → Tax Rates
3. `python manage.py add_default_shipping_costs` → Shipping Costs

**Sab ready ho jayega!** ✅

