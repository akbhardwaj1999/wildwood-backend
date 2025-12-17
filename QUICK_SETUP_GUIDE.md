# Quick Setup Guide - PythonAnywhere Ke Liye

## 🚀 3 Commands - Sab Kuch Setup Ho Jayega

### 1️⃣ Countries, States, Cities Add Karne Ke Liye
```bash
python manage.py add_us_states_cities
```
**Kya Hoga:**
- 50 US States add honge
- 396+ Cities add honge
- Tax rates add karne ke liye ready

**File:** `NEW_tax_calculator/management/commands/add_us_states_cities.py`

---

### 2️⃣ Tax Rates Add Karne Ke Liye
```bash
python manage.py add_default_tax_rates
```
**Kya Hoga:**
- US ke major states/cities ke default tax rates add honge
- California, New York, Texas, Florida, etc.

**File:** `NEW_tax_calculator/management/commands/add_default_tax_rates.py`

---

### 3️⃣ Shipping Cost Rules Add Karne Ke Liye
```bash
python manage.py add_default_shipping_costs
```
**Kya Hoga:**
- 32 shipping cost rules add honge
- LOCAL, OTHER_CITY, OTHER_STATE, INTERNATIONAL ke liye

**File:** `cart/management/commands/add_default_shipping_costs.py`

---

## 📋 PythonAnywhere Par Complete Setup

### Step-by-Step:

```bash
# 1. Project folder mein jao
cd ~/wildwood-backend

# 2. Virtual environment activate karo
source env/bin/activate

# 3. Migrations run karo (agar nahi kiye)
python manage.py migrate

# 4. Countries/States/Cities add karo
python manage.py add_us_states_cities

# 5. Tax rates add karo
python manage.py add_default_tax_rates

# 6. Shipping costs add karo
python manage.py add_default_shipping_costs

# 7. Server restart karo (PythonAnywhere dashboard se)
```

---

## ✅ Verification

Sab kuch add ho gaya ya nahi check karo:

```bash
# Check states/cities
python manage.py shell -c "from NEW_tax_calculator.models import Country, State, City; us = Country.objects.get(name='United States'); print(f'States: {State.objects.filter(country=us).count()}'); print(f'Cities: {City.objects.filter(state__country=us).count()}')"

# Check tax rates
python manage.py shell -c "from NEW_tax_calculator.models import NEW_TaxRate; print(f'Tax Rates: {NEW_TaxRate.objects.count()}')"

# Check shipping costs
python manage.py shell -c "from cart.models import ShippingCost; print(f'Shipping Rules: {ShippingCost.objects.count()}')"
```

---

## 📝 Important Notes

1. **Order Important Hai:**
   - Pehle `add_us_states_cities` (tax rates ke liye states/cities chahiye)
   - Phir `add_default_tax_rates`
   - Phir `add_default_shipping_costs`

2. **Safe Commands:**
   - Multiple times run kar sakte ho
   - Duplicate nahi banenge
   - Existing data ko overwrite nahi karega

3. **Warehouse Settings:**
   - `wildwud/settings.py` mein check karo:
   ```python
   WAREHOUSE_COUNTRY = 'United States'
   WAREHOUSE_STATE = 'California'
   WAREHOUSE_CITY = 'Los Angeles'
   ```

---

## 🎯 Summary

| Kaam | Command |
|------|---------|
| **Countries/States/Cities** | `python manage.py add_us_states_cities` |
| **Tax Rates** | `python manage.py add_default_tax_rates` |
| **Shipping Costs** | `python manage.py add_default_shipping_costs` |

**Bas ye 3 commands run karo - sab ready!** ✅

