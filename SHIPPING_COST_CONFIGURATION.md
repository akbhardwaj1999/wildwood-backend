# Shipping Cost Configuration Guide

## Shipping Cost Kiske Basis Par Configured Hota Hai?

Shipping cost **3 cheezo** ke basis par calculate hota hai:

### 1. **Product Dimensions** (Volume aur Weight)
- **Volume**: Product ka volume (cubic inches ya cubic cm)
- **Weight**: Product ka weight (pounds ya kg)
- Ye data **Product Variant** model mein stored hota hai
- Location: `galleryItem/models.py` - `Variant` model

### 2. **Destination Address** (Country, State, City)
- **Warehouse Location** (settings.py mein):
  - `WAREHOUSE_COUNTRY = 'United States'`
  - `WAREHOUSE_STATE = 'California'`
  - `WAREHOUSE_CITY = 'Los Angeles'`
  
- **Customer Address** (checkout page se):
  - Country
  - State
  - City

### 3. **Shipping Cost Rules** (Database mein)
- **ShippingCost** model mein rules stored hain
- Location: Django Admin → Cart → Shipping Costs

## Kaise Calculate Hota Hai?

### Step 1: Shipment Type Determine Karna
Destination address ko warehouse se compare karke:

```
IF country != WAREHOUSE_COUNTRY:
    → INTERNATIONAL shipping
ELIF state != WAREHOUSE_STATE:
    → OTHER_STATE shipping
ELIF city != WAREHOUSE_CITY:
    → OTHER_CITY shipping
ELSE:
    → LOCAL shipping
```

### Step 2: Product Dimensions Check Karna
Har cart item ke liye:
- Product variant ka **volume** check karo
- Product variant ka **weight** check karo

### Step 3: Shipping Cost Rule Find Karna
Database se matching rule find karo:
- **Parameter**: Volume ya Weight
- **Range**: Product ka volume/weight kis range mein hai
- **Shipment Type**: LOCAL/OTHER_CITY/OTHER_STATE/INTERNATIONAL

### Step 4: Cost Calculate Karna
- Volume-based cost aur Weight-based cost dono check karo
- **Higher cost** use karo (safety ke liye)
- Quantity se multiply karo
- Sab items ka total sum karo

## Example

**Scenario:**
- Warehouse: Los Angeles, California, United States
- Customer Address: New York, New York, United States
- Product: Volume = 200, Weight = 15 lbs

**Calculation:**
1. Shipment Type: OTHER_STATE (different state)
2. Volume 200 → Range: 101-500 → Cost: $18.00
3. Weight 15 → Range: 11-50 → Cost: $18.00
4. Higher cost: $18.00
5. Quantity = 2 → Total: $18.00 × 2 = **$36.00**

## Configuration Kahan Karein?

### 1. Warehouse Location
**File:** `wildwud/settings.py`
```python
WAREHOUSE_COUNTRY = 'United States'
WAREHOUSE_STATE = 'California'
WAREHOUSE_CITY = 'Los Angeles'
```

### 2. Product Volume/Weight
**Location:** Django Admin → Gallery Item → Variants
- Har variant ke liye `volume` aur `weight` set karo
- Agar nahi set kiya, shipping cost $0.00 hoga

### 3. Shipping Cost Rules
**Location:** Django Admin → Cart → Shipping Costs

**Add Rule:**
- **Parameter**: Volume ya Weight
- **Value Start**: Range ka start (e.g., 0)
- **Value End**: Range ka end (e.g., 100)
- **Shipment Type**: LOCAL/OTHER_CITY/OTHER_STATE/INTERNATIONAL
- **Charges**: Cost amount (e.g., 5.00)

**Example Rules:**
```
Volume 0-100, LOCAL → $5.00
Volume 101-500, LOCAL → $8.00
Weight 0-10, OTHER_STATE → $12.00
Weight 11-50, INTERNATIONAL → $35.00
```

## Default Rules Add Karne Ke Liye

```bash
python manage.py add_default_shipping_costs
```

Ye command 32 default shipping cost rules add karega:
- LOCAL: $5-$15
- OTHER_CITY: $8-$25
- OTHER_STATE: $12-$35
- INTERNATIONAL: $25-$75

## Important Notes

1. **Product Variants Must Have Volume/Weight**:
   - Agar variant mein volume/weight nahi hai, shipping cost $0.00 hoga
   - Admin se har variant ke liye set karo

2. **Warehouse Settings Required**:
   - `settings.py` mein warehouse location set hona chahiye
   - Agar nahi hai, shipping cost $0.00 hoga

3. **Shipping Cost Rules Required**:
   - Database mein shipping cost rules honi chahiye
   - Agar nahi hain, shipping cost $0.00 hoga

4. **Priority**:
   - Volume aur Weight dono check hote hain
   - **Higher cost** use hota hai (safety ke liye)

## Troubleshooting

**Shipping Cost $0.00 aa raha hai?**

1. Check karo: Product variants mein volume/weight set hai?
2. Check karo: Warehouse settings `settings.py` mein hain?
3. Check karo: Shipping cost rules database mein hain?
4. Check karo: Django logs mein koi error hai?

## Summary

Shipping cost = **Product Dimensions** (volume/weight) + **Distance** (warehouse se destination) + **Shipping Rules** (database mein stored)

