# Shipping Cost Setup Complete

## What Was Fixed

1. **Added Warehouse Settings** in `wildwud/settings.py`:
   - `WAREHOUSE_COUNTRY = 'United States'`
   - `WAREHOUSE_STATE = 'California'`
   - `WAREHOUSE_CITY = 'Los Angeles'`

2. **Added Default Shipping Cost Rules** using management command:
   - 32 shipping cost rules added for all shipment types
   - LOCAL, OTHER_CITY, OTHER_STATE, and INTERNATIONAL shipping
   - Volume-based and weight-based pricing

3. **Fixed API Shipping Cost Calculation**:
   - API now passes updated address (country, state, city) to shipping calculation
   - Better error handling and logging

## How Shipping Cost is Calculated

1. **Compare destination with warehouse**:
   - Same city = LOCAL shipping
   - Same state, different city = OTHER_CITY shipping
   - Same country, different state = OTHER_STATE shipping
   - Different country = INTERNATIONAL shipping

2. **Calculate based on product dimensions**:
   - Uses product variant's `volume` or `weight`
   - Finds matching shipping cost rule
   - Uses higher of volume-based or weight-based cost

3. **Example**:
   - Warehouse: Los Angeles, California, United States
   - Destination: New York, New York, United States
   - Result: OTHER_STATE shipping (different state)
   - Cost: Based on product volume/weight

## Testing

1. **Add items to cart** (make sure variants have volume/weight set)
2. **Go to checkout page**
3. **Enter address**:
   - Country: United States
   - State: New York (different from California)
   - City: New York
4. **Check shipping cost**:
   - Should show OTHER_STATE shipping cost (e.g., $12-35 based on product size)
   - Not $0.00 anymore!

## Important Notes

- **Product Variants Must Have Volume/Weight**: 
  - Check that your product variants have `volume` and `weight` fields set
  - Without these, shipping cost will be $0.00

- **Update Warehouse Location**:
  - If your warehouse is not in Los Angeles, California, update settings:
  ```python
  WAREHOUSE_COUNTRY = 'Your Country'
  WAREHOUSE_STATE = 'Your State'
  WAREHOUSE_CITY = 'Your City'
  ```

- **Customize Shipping Costs**:
  - Go to Django Admin → Cart → Shipping Costs
  - Edit or add new shipping cost rules as needed

## API Response

The `/api/tax/update-address/` endpoint now returns:
```json
{
    "success": true,
    "shipping_cost": 12.00,  // Calculated based on address and product
    "tax_amount": 2.07,
    "grand_total": 37.07,
    ...
}
```

## Troubleshooting

If shipping cost is still $0.00:
1. Check that product variants have `volume` or `weight` set
2. Verify warehouse settings in `settings.py`
3. Check that shipping cost rules exist in database
4. Check Django logs for any errors

