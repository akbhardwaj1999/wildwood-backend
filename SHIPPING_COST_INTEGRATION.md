# Shipping Cost Auto-Calculation Integration

## Overview
Shipping cost is now automatically calculated when address is entered/updated on the checkout page, similar to tax calculation.

## Implementation Details

### Backend Changes

#### 1. API Endpoint: `/api/tax/update-address/`
**File:** `NEW_tax_calculator/api_views.py`

**What it does:**
- Updates order shipping address with country, state, city
- Calculates shipping cost based on updated address
- Calculates tax based on updated address
- Returns all values in single API call

**Key Change:**
```python
# Before: Used order.shipping_address (old address)
shipping_cost = calculate_total_shipping_cost(order)

# After: Uses updated address explicitly
shipping_cost = calculate_total_shipping_cost(
    order, 
    country=country, 
    state=state, 
    city=city if city else None
)
```

**API Response:**
```json
{
    "success": true,
    "order_id": 123,
    "subtotal": 100.00,
    "shipping_cost": 15.50,  // Automatically calculated
    "tax_amount": 8.75,
    "grand_total": 124.25,
    "tax_rate": "8.75%",
    "is_exempt": false
}
```

### Shipping Cost Calculation Logic

**File:** `cart/utils.py` - `calculate_total_shipping_cost()`

**How it works:**
1. Compares destination address with warehouse location
2. Determines shipment type:
   - **LOCAL**: Same city as warehouse
   - **OTHER_CITY**: Same state, different city
   - **OTHER_STATE**: Same country, different state
   - **INTERNATIONAL**: Different country
3. Calculates cost based on:
   - Product volume/weight from cart items
   - Shipment type (local/other city/other state/international)
   - Shipping cost rules in database (`ShippingCost` model)

**Required Settings:**
- `WAREHOUSE_COUNTRY`: Warehouse country name
- `WAREHOUSE_STATE`: Warehouse state name
- `WAREHOUSE_CITY`: Warehouse city name

### Frontend Integration

**Expected Frontend Behavior:**
1. When user selects country/state/city on checkout page
2. Frontend calls: `taxApi.updateAddressAndCalculateTax(addressData)`
3. API returns: `shipping_cost`, `tax_amount`, `grand_total`
4. Frontend updates cart state with these values
5. UI displays updated shipping cost immediately

**Frontend Code Example:**
```typescript
const response = await taxApi.updateAddressAndCalculateTax({
    country: "United States",
    state: "California",
    city: "Los Angeles"
});

// Update cart state
setCart({
    ...cart,
    shipping_cost: response.shipping_cost,
    tax_amount: response.tax_amount,
    total: response.grand_total
});
```

## Testing

### Manual Testing Steps:
1. Add items to cart
2. Go to checkout page
3. Select country (e.g., "United States")
4. Select state (e.g., "California")
5. Select city (e.g., "Los Angeles")
6. **Verify:**
   - Shipping cost appears/updates automatically
   - Tax amount appears/updates automatically
   - Grand total includes shipping + tax
   - No page refresh needed

### API Testing:
```bash
POST /api/tax/update-address/
Content-Type: application/json

{
    "country": "United States",
    "state": "California",
    "city": "Los Angeles",
    "zip_code": "90001"
}
```

## Error Handling

- If warehouse settings are missing: Shipping cost = 0.00
- If shipping calculation fails: Shipping cost = 0.00 (error logged)
- If address is incomplete: API returns error message

## Notes

- Shipping cost is calculated **after** address is updated
- Shipping cost is included in `grand_total` calculation
- Shipping cost is saved to `order.total_shipping_cost` in database
- Same API call handles both tax and shipping calculation for efficiency

